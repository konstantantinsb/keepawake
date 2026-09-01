import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import i18n
from keepawake import TrayApp, KeepAwakeState, _setup_logging

i18n.load("en")
state = KeepAwakeState(_setup_logging())
app = TrayApp(state)
sub = app._build_language_submenu()
print(f"Language submenu: {len(sub.items)} items")
for it in sub.items:
    # pystray's _checked is wrapped; check if it returns truthy
    is_checked = bool(it._checked(it)) if it._checked else False
    print(f"  - {it.text!r:14s}  checked={is_checked}  radio={bool(it._radio)}")
