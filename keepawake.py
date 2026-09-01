"""
KeepAwake Tray App
==================
Lightweight Windows 11 system tray app that prevents the system from
sleeping (and optionally the display from turning off) via the native
Win32 API SetThreadExecutionState.

Key principles:
- NO key emulation (no F15 / Shift etc.) — only the OS-level API.
- All UI text is internationalized via i18n.py (en/ru/lv).
- On exit / crash / Ctrl+C the execution state flags are reset.

Usage:
    python keepawake.py            # run from source
    KeepAwake.exe                  # standalone build
"""

from __future__ import annotations

import atexit
import ctypes
import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import pystray
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

import i18n

# Версия — пишется в лог при старте, чтобы можно было проверить,
# какая именно сборка запущена (помогает при путанице со старыми .exe).
__version__ = "0.2.0"

# ─── Windows API ────────────────────────────────────────────────────────────
# Docs: https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

_kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
_SetThreadExecutionState = _kernel32.SetThreadExecutionState
_SetThreadExecutionState.restype = ctypes.c_uint32
_SetThreadExecutionState.argtypes = [ctypes.c_uint32]


# ─── Логирование ────────────────────────────────────────────────────────────
def _setup_logging() -> logging.Logger:
    log_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "KeepAwake"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "keepawake.log"

    logger = logging.getLogger("keepawake")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        # Flush after every record so log reflects the latest state
        # even if the process is killed abruptly.
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        # Add a flush-on-every-emit wrapper
        orig_emit = handler.emit
        def emit_with_flush(record):
            orig_emit(record)
            handler.flush()
        handler.emit = emit_with_flush
    return logger


# ─── Иконка ─────────────────────────────────────────────────────────────────
ICON_SIZE = 64


def make_icon(active: bool) -> Image.Image:
    """64×64 coffee cup. Amber = active, gray = inactive."""
    img = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if active:
        cup_fill = (255, 196, 0, 255)
        cup_outline = (120, 70, 0, 255)
        steam = (230, 230, 230, 220)
    else:
        cup_fill = (170, 170, 170, 255)
        cup_outline = (90, 90, 90, 255)
        steam = (200, 200, 200, 140)

    draw.ellipse([10, 18, 50, 56], fill=cup_fill, outline=cup_outline, width=2)
    draw.arc([44, 28, 62, 48], 270, 90, fill=cup_outline, width=3)
    draw.ellipse([14, 22, 46, 32], fill=cup_outline)
    for x in (22, 32, 42):
        draw.line([(x, 16), (x - 3, 6)], fill=steam, width=2)

    return img


# ─── Состояние приложения ───────────────────────────────────────────────────
class KeepAwakeState:
    """Thread-safe state + timer."""

    def __init__(self, log: logging.Logger) -> None:
        self.log = log
        self._lock = threading.RLock()
        self._enabled = False
        self._keep_display = True
        self._timer_hours: float = 0.0
        self._timer_end: datetime | None = None
        self._stop_event = threading.Event()
        self._timer_thread: threading.Thread | None = None
        self._tray_icon: Icon | None = None

    @property
    def enabled(self) -> bool:
        with self._lock:
            return self._enabled

    @property
    def keep_display(self) -> bool:
        with self._lock:
            return self._keep_display

    @property
    def timer_hours(self) -> float:
        with self._lock:
            return self._timer_hours

    def toggle(self) -> None:
        with self._lock:
            self._enabled = not self._enabled
            self._apply_locked()
            self.log.info("Toggled: %s", "ON" if self._enabled else "OFF")

    def inc_timer(self) -> None:
        with self._lock:
            self._timer_hours = round(min(24.0, self._timer_hours + 0.5), 2)
            self._recompute_end_locked()
            self.log.info("Timer inc: %.1f h", self._timer_hours)

    def dec_timer(self) -> None:
        with self._lock:
            self._timer_hours = round(max(0.0, self._timer_hours - 0.5), 2)
            self._recompute_end_locked()
            self.log.info("Timer dec: %.1f h", self._timer_hours)

    def set_keep_display(self, value: bool) -> None:
        with self._lock:
            self._keep_display = value
            self._apply_locked()
            self.log.info("Keep display: %s", "yes" if value else "no")

    def timer_remaining(self) -> timedelta | None:
        with self._lock:
            if not self._enabled or self._timer_hours == 0 or self._timer_end is None:
                return None
            return self._timer_end - datetime.now()

    def _apply_locked(self) -> None:
        if self._enabled:
            flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            if self._keep_display:
                flags |= ES_DISPLAY_REQUIRED
            result = _SetThreadExecutionState(flags)
            self.log.info("SetThreadExecutionState(0x%X) -> 0x%X", flags, result)
        else:
            _SetThreadExecutionState(ES_CONTINUOUS)
            self.log.info("SetThreadExecutionState reset (ES_CONTINUOUS)")

    def _recompute_end_locked(self) -> None:
        if self._enabled and self._timer_hours > 0:
            self._timer_end = datetime.now() + timedelta(hours=self._timer_hours)
            if self._timer_thread is None or not self._timer_thread.is_alive():
                self._timer_thread = threading.Thread(
                    target=self._timer_loop, name="keepawake-timer", daemon=True
                )
                self._timer_thread.start()
        else:
            self._timer_end = None

    def _timer_loop(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(1.0)
            with self._lock:
                if not self._enabled or self._timer_end is None:
                    return
                if datetime.now() >= self._timer_end:
                    self._enabled = False
                    self._timer_hours = 0.0
                    self._timer_end = None
                    self._apply_locked()
                    self.log.info("Timer expired — auto-disabled")
                    if self._tray_icon is not None:
                        try:
                            self._tray_icon.icon = make_icon(False)
                            self._tray_icon.update_menu()
                            self._tray_icon.notify(
                                i18n.t("notification.timer_expired_message"),
                                i18n.t("notification.timer_expired_title"),
                            )
                        except Exception:
                            pass
                    return

    def shutdown(self) -> None:
        self._stop_event.set()
        with self._lock:
            if self._enabled:
                _SetThreadExecutionState(ES_CONTINUOUS)
                self._enabled = False
                self.log.info("Shutdown: flags reset")


# ─── Форматирование таймера ─────────────────────────────────────────────────
def _fmt_remaining(td: timedelta | None) -> str:
    if td is None:
        return i18n.t("timer.infinite")
    secs = int(td.total_seconds())
    if secs <= 0:
        return i18n.t("timer.expired")
    h, rem = divmod(secs, 3600)
    m, _ = divmod(rem, 60)
    if h == 0:
        return i18n.t("timer.minutes", m=m)
    return i18n.t("timer.hours_minutes", h=h, m=m)


# ─── Меню ───────────────────────────────────────────────────────────────────
class TrayApp:
    """Связывает state ↔ иконка ↔ i18n. Владеет жизненным циклом трея."""

    def __init__(self, state: KeepAwakeState) -> None:
        self.state = state
        self.icon: Icon | None = None

    def _set_lang_action(self, code: str):
        def action(_icon: Icon, _item: MenuItem) -> None:
            i18n.set_lang(code)
            self.state.log.info("Language -> %s", code)
            self._refresh()
        return action

    def _toggle_action(self, _icon: Icon, _item: MenuItem) -> None:
        self.state.toggle()
        self._refresh_icon_and_menu()

    def _display_action(self, _icon: Icon, _item: MenuItem) -> None:
        self.state.set_keep_display(not self.state.keep_display)
        self._refresh_icon_and_menu()

    def _inc_action(self, _icon: Icon, _item: MenuItem) -> None:
        self.state.inc_timer()
        self._refresh_icon_and_menu()

    def _dec_action(self, _icon: Icon, _item: MenuItem) -> None:
        self.state.dec_timer()
        self._refresh_icon_and_menu()

    def _quit_action(self, _icon: Icon, _item: MenuItem) -> None:
        self.state.shutdown()
        _icon.stop()

    def _status_text(self, _item: MenuItem) -> str:
        return i18n.t("menu.status_active") if self.state.enabled else i18n.t("menu.status_inactive")

    def _timer_text(self, _item: MenuItem) -> str:
        return i18n.t("menu.timer_header", remaining=_fmt_remaining(self.state.timer_remaining()))

    def _timer_hint(self, _item: MenuItem) -> str:
        if self.state.timer_hours == 0:
            return i18n.t("menu.timer_hint_infinite")
        return i18n.t("menu.timer_hint_set", hours=self.state.timer_hours)

    def _language_text(self, _item: MenuItem) -> str:
        return i18n.t("menu.language")

    def _build_language_submenu(self) -> Menu:
        items = []
        for code in i18n.supported():
            items.append(
                MenuItem(
                    i18n.LANG_NAMES[code],
                    self._set_lang_action(code),
                    checked=lambda _i, c=code: i18n.get_lang() == c,
                    radio=True,
                )
            )
        return Menu(*items)

    def _build_menu(self) -> Menu:
        return Menu(
            MenuItem(i18n.t("menu.header"), None, enabled=False),
            MenuItem(self._status_text, None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(i18n.t("menu.toggle"), self._toggle_action,
                     checked=lambda _i: self.state.enabled),
            MenuItem(i18n.t("menu.keep_display"), self._display_action,
                     checked=lambda _i: self.state.keep_display),
            Menu.SEPARATOR,
            MenuItem(self._timer_text, None, enabled=False),
            MenuItem(i18n.t("menu.timer_increment"), self._inc_action),
            MenuItem(self._timer_hint, None, enabled=False),
            MenuItem(i18n.t("menu.timer_decrement"), self._dec_action),
            Menu.SEPARATOR,
            MenuItem(self._language_text, self._build_language_submenu()),
            Menu.SEPARATOR,
            MenuItem(i18n.t("menu.exit"), self._quit_action),
        )

    def _refresh_icon_and_menu(self) -> None:
        if self.icon is None:
            return
        self.icon.icon = make_icon(self.state.enabled)
        self.icon.update_menu()

    def _refresh(self) -> None:
        """Полное обновление: иконка, заголовок, меню (после смены языка)."""
        if self.icon is None:
            return
        self.icon.icon = make_icon(self.state.enabled)
        self.icon.title = i18n.t("app.tooltip")
        self.icon.menu = self._build_menu()
        self.icon.update_menu()

    def run(self) -> None:
        self.icon = Icon(
            "KeepAwake",
            make_icon(self.state.enabled),
            i18n.t("app.tooltip"),
            self._build_menu(),
        )
        self.state._tray_icon = self.icon
        self.icon.run()


# ─── Точка входа ────────────────────────────────────────────────────────────
def main() -> int:
    if sys.platform != "win32":
        print("KeepAwake works only on Windows.", file=sys.stderr)
        return 2

    log = _setup_logging()
    log.info("─" * 50)
    log.info("KeepAwake v%s starting (Python %s, pid=%d, exe=%s)",
             __version__, sys.version.split()[0], os.getpid(), sys.executable)

    # Загружаем i18n. Язык по умолчанию — English; пользователь меняет в меню.
    i18n.load(i18n.DEFAULT_LANG)
    log.info("i18n loaded, default lang: %s (locales dir: %s)", i18n.get_lang(), i18n.LOCALES_DIR)

    state = KeepAwakeState(log)
    app = TrayApp(state)
    atexit.register(state.shutdown)

    try:
        app.run()
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt")
    finally:
        state.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
