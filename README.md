# KeepAwake Tray App

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011-0078d4.svg)]()
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776ab.svg)]()

A lightweight Windows 11 system-tray application that **programmatically** prevents
your computer from sleeping (and optionally from turning off the display) via the
native Win32 API `SetThreadExecutionState`. No key emulation, no background noise.

🌐 **Interface languages**: 🇬🇧 English · 🇷🇺 Русский · 🇱🇻 Latviešu (switch in tray menu).

---

## Why not "F15 auto-presser"?

Many "keep awake" tools simulate key presses to fool the idle timer. That interferes
with typing, games, screenshot tools, and anything else listening to keyboard input.

**KeepAwake** calls the OS-level API directly:

```c
SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED);
```

This is what Windows itself uses internally for media playback and presentation modes.

---

## Features

- 🟢 **On / Off** toggle in the tray menu. Amber cup = active, gray cup = off.
- 🖥 **Keep display on** — independent from system sleep (useful for background
  downloads: keep system awake, let the screen turn off normally).
- ⏱ **Auto-off timer** with `+ 0.5 h` / `− 0.5 h` buttons. `0` = infinite.
  Shows live remaining time: `2 h 30 min` / `45 min` / `∞`.
- 🔔 **Notification** when the timer auto-disables the mode.
- 🛡 **Graceful cleanup** on exit, crash, or `Ctrl+C` — flags always reset.
- 🌍 **Multilingual** (en/ru/lv) with live switching, no restart needed.
- 📝 **Logs** in `%LOCALAPPDATA%\KeepAwake\keepawake.log`.

---

## Quick start

### Run from source

```powershell
git clone https://github.com/konstantantsb/keepawake.git
cd keepawake
python -m pip install -r requirements.txt
python keepawake.py
```

A coffee-cup icon will appear in the system tray (near the clock). Right-click for
the menu.

### Run the standalone .exe

Download the latest `KeepAwake.exe` from the [Releases](../../releases) page
and double-click. No Python installation required.

### Build your own .exe

```powershell
.\build.bat
```

Output: `dist\KeepAwake.exe` (single-file, no console).

---

## Tray menu

```
┌──────────────────────────────────────┐
│ KeepAwake                            │
│   ● ACTIVE — system won't sleep      │   ← live status
│ ──────────────────────────────────── │
│ ☐ On / Off                           │   ← enable/disable
│ ☑ Keep display on                    │   ← ES_DISPLAY_REQUIRED
│ ──────────────────────────────────── │
│   Auto-off timer: 2 h 30 min         │   ← live remaining
│   + 0.5 h                            │
│   (step 0.5 h · currently 2.0 h)     │
│   − 0.5 h                            │
│ ──────────────────────────────────── │
│   Language  ▸  ☑ English             │   ← live switch, no restart
│              ☐ Русский               │
│              ☐ Latviešu              │
│ ──────────────────────────────────── │
│ Exit                                 │
└──────────────────────────────────────┘
```

---

## Project structure

```
keepawake/
├── keepawake.py          ← entry point (tray + state)
├── i18n.py               ← i18n loader: t(key, **kwargs)
├── locales/
│   ├── en.json
│   ├── ru.json
│   └── lv.json
├── requirements.txt      ← pystray, Pillow, pyinstaller
├── build.bat             ← onefile .exe build (PyInstaller)
├── LICENSE               ← MIT
├── .gitignore
├── README.md
└── tests/                ← smoke-tests (no GUI)
```

---

## Adding a new language

1. Copy `locales/en.json` → `locales/<code>.json` and translate the values.
2. Add the code to `i18n.SUPPORTED` in `i18n.py`.
3. Add the self-name to `i18n.LANG_NAMES` (each language names itself in its own script).

The menu rebuilds on the next click — no restart needed.

---

## Used APIs

| API | Purpose |
|---|---|
| `kernel32!SetThreadExecutionState` | Prevent sleep / display-off (native Win32) |
| `pystray.Icon` | Tray icon + context menu |
| `PIL.Image` | Runtime 64×64 icon generation |
| `threading.Thread` | Background timer (non-blocking UI) |
| `atexit` | Guaranteed flag reset on process exit |

---

## Logs

```
%LOCALAPPDATA%\KeepAwake\keepawake.log
```

Typical output:

```
2026-09-01 15:30:12 [INFO] Toggled: ON
2026-09-01 15:30:12 [INFO] SetThreadExecutionState(0x80000003) -> 0x80000000
2026-09-01 16:30:12 [INFO] Timer expired — auto-disabled
```

---

## License

[MIT](LICENSE) © 2026 Konstantin Bazarevich
