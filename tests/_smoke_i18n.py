"""Smoke-test for i18n refactor."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Pre-clean cached bytecode
import shutil
for d in (Path(__file__).parent / "__pycache__", Path(__file__).parent / "locales" / "__pycache__"):
    if d.exists():
        shutil.rmtree(d)

import i18n
from i18n import t, set_lang, get_lang, supported, LANG_NAMES, load
from keepawake import KeepAwakeState, TrayApp, _fmt_remaining, _setup_logging, make_icon
from datetime import timedelta
from pystray import MenuItem

print("=" * 70)
print("1. i18n: загрузка и базовые переводы")
print("=" * 70)
load("en")
assert get_lang() == "en", "default lang should be en"
assert t("menu.exit") == "Exit"
assert t("menu.toggle") == "On / Off"
assert t("timer.infinite") == "∞ (infinite)"
print("  [en] menu.exit           =", repr(t("menu.exit")))
print("  [en] menu.toggle         =", repr(t("menu.toggle")))
print("  [en] timer.hours_minutes =", repr(t("timer.hours_minutes", h=2, m=5)))
print()

set_lang("ru")
assert get_lang() == "ru"
assert t("menu.exit") == "Выход"
assert t("menu.toggle") == "Вкл / Выкл"
assert t("timer.hours_minutes", h=2, m=5) == "2 ч 05 мин"
print("  [ru] menu.exit           =", repr(t("menu.exit")))
print("  [ru] menu.toggle         =", repr(t("menu.toggle")))
print("  [ru] timer.hours_minutes =", repr(t("timer.hours_minutes", h=2, m=5)))
print()

set_lang("lv")
assert get_lang() == "lv"
assert t("menu.exit") == "Iziet"
assert t("menu.toggle") == "Ieslēgt / Izslēgt"
print("  [lv] menu.exit           =", repr(t("menu.exit")))
print("  [lv] menu.toggle         =", repr(t("menu.toggle")))
print("  [lv] menu.status_active  =", repr(t("menu.status_active")))
print("  [lv] timer.hours_minutes =", repr(t("timer.hours_minutes", h=1, m=30)))
print()

print("=" * 70)
print("2. LANG_NAMES: самоименование")
print("=" * 70)
print("  ru ->", repr(LANG_NAMES["ru"]))
print("  en ->", repr(LANG_NAMES["en"]))
print("  lv ->", repr(LANG_NAMES["lv"]))
print()

print("=" * 70)
print("3. Fallback: несуществующий ключ возвращает сам ключ")
print("=" * 70)
print("  t('nonexistent.key') ->", repr(t("nonexistent.key")))
print()

print("=" * 70)
print("4. _fmt_remaining во всех языках")
print("=" * 70)
for lang in ("en", "ru", "lv"):
    set_lang(lang)
    print(f"  [{lang}]")
    print(f"    None         -> {repr(_fmt_remaining(None))}")
    print(f"    2h15m        -> {repr(_fmt_remaining(timedelta(hours=2, minutes=15)))}")
    print(f"    45m          -> {repr(_fmt_remaining(timedelta(minutes=45)))}")
    print(f"    0            -> {repr(_fmt_remaining(timedelta(0)))}")
print()

print("=" * 70)
print("5. TrayApp: построение меню в 3 языках")
print("=" * 70)
log = _setup_logging()
state = KeepAwakeState(log)
app = TrayApp(state)

for lang in ("en", "ru", "lv"):
    set_lang(lang)
    menu = app._build_menu()
    state._timer_hours = 1.5
    state._enabled = True
    print(f"\n  [{lang}] ({len(menu.items)} items)")
    for i, item in enumerate(menu.items):
        text = item.text if isinstance(item.text, str) else "(callable)"
        chk = "✓" if (item.checked is not None) else " "
        if isinstance(text, str) and len(text) > 50:
            text = text[:47] + "..."
        print(f"    [{i:2d}] {chk} {text!r}")

# Reset state
state.shutdown()
set_lang("en")
print()
print("=" * 70)
print("ВСЕ ТЕСТЫ ПРОЙДЕНЫ")
print("=" * 70)
