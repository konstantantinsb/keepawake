"""Smoke-test: проверяем, что ctypes, pystray, Pillow и весь модуль импортируются,
и что SetThreadExecutionState реально вызывается."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from keepawake import (
    _SetThreadExecutionState,
    ES_CONTINUOUS,
    ES_SYSTEM_REQUIRED,
    ES_DISPLAY_REQUIRED,
    make_icon,
    KeepAwakeState,
    build_menu,
    _setup_logging,
    _fmt_remaining,
)
from datetime import timedelta

print("=" * 60)
print("ES_CONTINUOUS       = 0x%08X" % ES_CONTINUOUS)
print("ES_SYSTEM_REQUIRED  = 0x%08X" % ES_SYSTEM_REQUIRED)
print("ES_DISPLAY_REQUIRED = 0x%08X" % ES_DISPLAY_REQUIRED)

print()
print("--- Smoke test: SetThreadExecutionState ---")
r1 = _SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
print("Включил (CONT|SYS|DISP)   -> 0x%08X  (ожидаем ненулевой = ОК)" % r1)
r2 = _SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
print("Оставил систему (CONT|SYS) -> 0x%08X" % r2)
r3 = _SetThreadExecutionState(ES_CONTINUOUS)
print("Сбросил (CONT)             -> 0x%08X" % r3)

print()
print("--- Тест иконки ---")
img = make_icon(True)
print("Активная:", img.size, img.mode, "-> _test_icon_active.png")
img.save("_test_icon_active.png")
img2 = make_icon(False)
print("Серая:   ", img2.size, img2.mode, "-> _test_icon_inactive.png")
img2.save("_test_icon_inactive.png")

print()
print("--- Тест _fmt_remaining ---")
print("None              ->", repr(_fmt_remaining(None)))
print("timedelta(h=2, m=15) ->", repr(_fmt_remaining(timedelta(hours=2, minutes=15))))
print("timedelta(m=45)     ->", repr(_fmt_remaining(timedelta(minutes=45))))
print("timedelta(0)        ->", repr(_fmt_remaining(timedelta(0))))

print()
print("--- Тест KeepAwakeState (без GUI) ---")
log = _setup_logging()
state = KeepAwakeState(log)
print("Начальное: enabled=%s, hours=%s" % (state.enabled, state.timer_hours))
state.toggle()
print("После toggle: enabled=%s (должен быть True)" % state.enabled)
state.set_keep_display(False)
print("keep_display=%s (должен быть False)" % state.keep_display)
state.inc_timer(); state.inc_timer(); state.inc_timer()
print("После 3x inc_timer: hours=%s (должен быть 1.5)" % state.timer_hours)
state.dec_timer()
print("После dec_timer: hours=%s (должен быть 1.0)" % state.timer_hours)
state.shutdown()
print("После shutdown: enabled=%s (должен быть False)" % state.enabled)

print()
print("--- Тест build_menu (создаёт Menu, не показывает) ---")
state2 = KeepAwakeState(log)
menu = build_menu(state2)
print("Menu создан:", type(menu).__name__, "с", len(menu.items), "элементами")
for i, item in enumerate(menu.items):
    text = item.text if isinstance(item.text, str) else "(callable)"
    print("  [%d] %s" % (i, text))

print()
print("=" * 60)
print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
print("=" * 60)
