"""Check that all 3 locales are bundled inside the .exe (uncompressed, --add-data)."""
from pathlib import Path

exe = Path("dist/KeepAwake.exe")
data = exe.read_bytes()
print(f"Reading {exe} ({len(data):,} bytes)")
print()

checks = [
    # locale filenames
    (b"locales/en.json", "en.json path"),
    (b"locales/ru.json", "ru.json path"),
    (b"locales/lv.json", "lv.json path"),
    # JSON keys
    (b'"menu.exit"', "JSON key menu.exit"),
    (b'"menu.toggle"', "JSON key menu.toggle"),
    (b'"notification.timer_expired_message"', "JSON key notification"),
    # en strings
    (b'"Exit"', "en: Exit"),
    (b'"On / Off"', "en: On / Off"),
    (b'"Language"', "en: Language"),
    # ru strings (UTF-8 encoded: Выход = D0 92 D1 8B D1 85 D0 BE D0 B4)
    (b'"\xd0\x92\xd1\x8b\xd1\x85\xd0\xbe\xd0\xb4"', "ru: Выход"),
    (b'"\xd0\x92\xd0\xba\xd0\xbb / \xd0\x92\xd1\x8b\xd0\xba\xd0\xbb"', "ru: Вкл / Выкл"),
    (b'"\xd0\xaf\xd0\xb7\xd1\x8b\xd0\xba"', "ru: Язык"),
    # lv strings
    (b'"Iziet"', "lv: Iziet"),
    (b'"Iesl', "lv: Iesl"),
    (b'"Valoda"', "lv: Valoda"),
    (b'"Latvie', "lv: Latvie"),
]
all_ok = True
for needle, desc in checks:
    found = needle in data
    mark = "FOUND  " if found else "MISSING"
    print(f"  [{mark}] {desc}")
    if not found:
        all_ok = False

print()
print("RESULT:", "ALL LOCALES BUNDLED" if all_ok else "SOME LOCALES MISSING")
