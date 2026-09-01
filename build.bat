@echo off
REM ============================================================
REM  KeepAwake - build standalone .exe (PyInstaller)
REM  All messages in English to keep cmd.exe happy with CP866.
REM ============================================================
setlocal

cd /d "%~dp0"

echo.
echo [1/3] Checking PyInstaller...
python -c "import PyInstaller; print('  PyInstaller', PyInstaller.__version__)" || (
    echo PyInstaller not found. Installing...
    python -m pip install --upgrade pyinstaller
)

echo.
echo [2/3] Cleaning previous build artifacts...
if exist build  rmdir /s /q build
if exist dist   rmdir /s /q dist
if exist KeepAwake.spec del /q KeepAwake.spec

echo.
echo [3/3] Building KeepAwake.exe (onefile, no console)...
python -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --noconsole ^
    --name KeepAwake ^
    --icon=NONE ^
    --add-data "locales;locales" ^
    keepawake.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed.
    exit /b 1
)

echo.
echo ============================================================
echo  Done! Output: %CD%\dist\KeepAwake.exe
echo  Size:
for %%I in (dist\KeepAwake.exe) do @echo    %%~zI bytes
echo ============================================================
endlocal
