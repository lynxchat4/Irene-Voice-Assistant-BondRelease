@echo off
REM LAVA / Irene Voice Assistant - Windows installer (CMD)
REM Run from repo root: double-click or: install.bat
REM Re-running is safe (idempotent).
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

REM ---------- Defaults ----------
set "VENV_DIR=venv"
set "DO_FRONTEND=1"
set "DO_PYTHON=1"
set "LITE=0"
set "DEV=0"
set "REINSTALL=0"
set "YES=0"
set "SKIP_SYSTEM=0"

REM ---------- Parse args ----------
:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="--venv"        (set "VENV_DIR=%~2" & shift & shift & goto :parse_args)
if /I "%~1"=="--no-frontend" (set "DO_FRONTEND=0" & shift & goto :parse_args)
if /I "%~1"=="--no-python"   (set "DO_PYTHON=0" & shift & goto :parse_args)
if /I "%~1"=="--lite"        (set "LITE=1" & shift & goto :parse_args)
if /I "%~1"=="--dev"         (set "DEV=1" & shift & goto :parse_args)
if /I "%~1"=="--reinstall"   (set "REINSTALL=1" & shift & goto :parse_args)
if /I "%~1"=="--yes"         (set "YES=1" & shift & goto :parse_args)
if /I "%~1"=="-y"            (set "YES=1" & shift & goto :parse_args)
if /I "%~1"=="--skip-system" (set "SKIP_SYSTEM=1" & shift & goto :parse_args)
if /I "%~1"=="--help"        goto :usage
if /I "%~1"=="-h"            goto :usage
echo [ERROR] Unknown option: %~1
echo Use install.bat --help
exit /b 1

:usage
echo Usage: install.bat [options]
echo.
echo Options:
echo   --venv DIR        Venv folder (default venv)
echo   --no-frontend     Skip frontend build
echo   --no-python       Skip Python deps
echo   --lite            Light install: skip torch (~800MB), no Silero TTS
echo   --dev             Install requirements-ci.txt (mypy/pep8)
echo   --reinstall       Recreate venv and reinstall all
echo   --yes, -y         No confirmations
echo   --help, -h        Show help
echo.
echo Examples:
echo   install.bat                      (full install)
echo   install.bat --lite               (fast, small)
echo   install.bat --reinstall --dev    (clean + dev)
echo.
echo After install:
echo   venv\Scripts\activate.bat
echo   python -m irene
exit /b 0
:args_done

REM ---------- Banner ----------
echo === LAVA Installer (Windows) ===
echo Project: %CD%
echo Venv: %VENV_DIR%  Frontend: %DO_FRONTEND%  Lite: %LITE%  Dev: %DEV%  Reinstall: %REINSTALL%
echo.

REM ---------- Check repo root ----------
if not exist "requirements.txt" (
  echo [ERROR] requirements.txt not found. Run from repo root.
  exit /b 1
)
if not exist "frontend\package.json" (
  echo [WARN] frontend\package.json not found - frontend build will be skipped.
)

REM ---------- Find Python ----------
set "PYTHON_BIN="
py --version >nul 2>&1
if %errorlevel%==0 (
  py -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
  if !errorlevel!==0 set "PYTHON_BIN=py"
)
if not defined PYTHON_BIN (
  python --version >nul 2>&1
  if !errorlevel!==0 (
    python -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
    if !errorlevel!==0 set "PYTHON_BIN=python"
  )
)
if not defined PYTHON_BIN (
  python3 --version >nul 2>&1
  if !errorlevel!==0 (
    python3 -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
    if !errorlevel!==0 set "PYTHON_BIN=python3"
  )
)
if not defined PYTHON_BIN (
  echo [ERROR] Python ^>=3.9 not found.
  echo Install from https://python.org (check "Add to PATH"!) or Microsoft Store.
  exit /b 1
)
echo [OK] Python:
%PYTHON_BIN% --version
%PYTHON_BIN% -c "import sys; print('     ', sys.executable, sys.version.split()[0])"

%PYTHON_BIN% -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
  echo [WARN] pip not found - trying ensurepip...
  %PYTHON_BIN% -m ensurepip --upgrade
  if %errorlevel% neq 0 (
    echo [ERROR] Failed to install pip.
    exit /b 1
  )
)
%PYTHON_BIN% -m venv --help >nul 2>&1
if %errorlevel% neq 0 (
  echo [ERROR] venv module not available. Reinstall Python with pip/venv.
  exit /b 1
)

REM ---------- Check Node ----------
set "NODE_OK=0"
set "NPM_OK=0"
node --version >nul 2>&1
if %errorlevel%==0 (
  echo [OK] Node:
  node --version
  node -e "process.exit(parseInt(process.versions.node.split('.')[0],10) >= 16 ? 0 : 1)" >nul 2>&1
  if !errorlevel!==0 (
    set "NODE_OK=1"
  ) else (
    echo [WARN] Node too old (need ^>=16.17). Frontend may fail.
    set "NODE_OK=1"
  )
  npm --version >nul 2>&1
  if !errorlevel!==0 (
    echo [OK] npm:
    npm --version
    set "NPM_OK=1"
  ) else (
    echo [WARN] npm not found - frontend skipped.
    set "DO_FRONTEND=0"
  )
) else (
  if "%DO_FRONTEND%"=="1" (
    echo [WARN] Node.js not found - frontend build skipped.
    echo Install Node 16.17+ from https://nodejs.org
    set "DO_FRONTEND=0"
  )
)

REM ---------- Confirm reinstall ----------
if "%REINSTALL%"=="1" if "%YES%"=="0" (
  set /p "ANS=Recreate %VENV_DIR% and reinstall all? [y/N]: "
  if /I not "!ANS!"=="y" (
    echo Cancelled.
    exit /b 1
  )
)

REM ---------- Venv ----------
if "%REINSTALL%"=="1" if exist "%VENV_DIR%" (
  echo [..] Removing %VENV_DIR%...
  rmdir /s /q "%VENV_DIR%"
  if exist "%VENV_DIR%" (
    echo [ERROR] Failed to remove %VENV_DIR% - close programs using it.
    exit /b 1
  )
)
if not exist "%VENV_DIR%" (
  echo [..] Creating venv: %VENV_DIR% (%PYTHON_BIN% -m venv)...
  %PYTHON_BIN% -m venv "%VENV_DIR%"
  if %errorlevel% neq 0 (
    echo [ERROR] Failed to create venv.
    exit /b 1
  )
  echo [OK] venv created.
) else (
  echo [OK] venv exists: %VENV_DIR%
)

REM ---------- Activate venv ----------
if not exist "%VENV_DIR%\Scripts\activate.bat" (
  echo [ERROR] Not found %VENV_DIR%\Scripts\activate.bat
  exit /b 1
)
echo [..] Activating venv...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
  echo [WARN] activate returned error, continuing...
)

echo [OK] Venv python:
python --version
where python

echo [..] Upgrading pip/setuptools/wheel...
python -m pip install --upgrade pip setuptools wheel
if %errorlevel% neq 0 echo [WARN] Failed to upgrade pip - continuing.

REM ---------- Python deps ----------
if "%DO_PYTHON%"=="1" (
  echo [..] Installing Python deps...
  if "%LITE%"=="1" (
    echo [WARN] Light mode (--lite): skipping torch.
    set "TMP_REQ=%TEMP%\lava_req_lite.txt"
    findstr /V /I /C:"torch" requirements.txt > "!TMP_REQ!"
    if !errorlevel! neq 0 copy requirements.txt "!TMP_REQ!" >nul
    pip install -r "!TMP_REQ!"
    if !errorlevel! neq 0 (
      echo [ERROR] pip install failed.
      del "!TMP_REQ!" 2>nul
      exit /b 1
    )
    del "!TMP_REQ!" 2>nul
    echo [OK] Python deps (lite) installed.
  ) else (
    echo       This may take 3-10 minutes (torch ~200MB)...
    pip install -r requirements.txt
    if !errorlevel!==0 (
      echo [ERROR] pip install failed. Try: pip install --verbose -r requirements.txt
      exit /b 1
    )
    echo [OK] Python deps installed.
  )
  if "%DEV%"=="1" (
    if exist "requirements-ci.txt" (
      echo [..] Installing dev deps...
      pip install -r requirements-ci.txt
      if !errorlevel!==0 echo [WARN] Failed to install dev deps.
    )
  )
  echo [..] Checking imports...
  python -c "import fastapi, uvicorn, yaml, vosk; print('  fastapi/uvicorn/yaml/vosk - OK')"
  if !errorlevel!==0 echo [WARN] Some packages not importable.
  if "%LITE%"=="0" (
    python -c "import torch; print('  torch', torch.__version__)"
    if !errorlevel!==0 echo [WARN] torch not importable (Silero will not work).
  )
) else (
  echo [WARN] Skipping Python deps (--no-python).
)

REM ---------- Frontend ----------
if "%DO_FRONTEND%"=="1" (
  if "%NPM_OK%"=="0" (
    echo [WARN] npm not found - skipping frontend.
  ) else if not exist "frontend\package.json" (
    echo [WARN] frontend\package.json not found - skipping.
  ) else (
    echo [..] Installing frontend deps (npm ci)...
    if not exist "frontend\package-lock.json" (
      echo [WARN] package-lock.json not found - using npm install.
      pushd frontend
      call npm install
      if !errorlevel!==0 (
        echo [ERROR] npm install failed.
        popd & exit /b 1
      )
      popd
    ) else (
      pushd frontend
      call npm ci
      if !errorlevel!==0 (
        echo [ERROR] npm ci failed. Try: cd frontend ^&^& npm install
        popd & exit /b 1
      )
      popd
    )
    echo [OK] npm deps installed.
    echo [..] Building frontend (npm run build)...
    pushd frontend
    call npm run build
    if !errorlevel!==0 (
      echo [ERROR] npm run build failed. Check node --version (need ^>=16.17).
      popd & exit /b 1
    )
    popd
    echo [OK] Frontend built.
    if exist "frontend\dist\index.html" (
      echo [OK] artifacts: frontend\dist\index.html
    ) else (
      echo [WARN] frontend\dist\index.html not found after build!
    )
    if exist "frontend\dist" if not exist "irene_plugin_web_face_frontend\frontend-dist" (
      echo [..] Copying dist -^> irene_plugin_web_face_frontend\frontend-dist...
      mkdir "irene_plugin_web_face_frontend\frontend-dist" 2>nul
      xcopy /E /I /Y "frontend\dist\*" "irene_plugin_web_face_frontend\frontend-dist\" >nul
    )
  )
) else (
  echo [WARN] Frontend build skipped.
  if exist "frontend\dist\index.html" (
    echo [OK] Found existing frontend\dist - OK.
  ) else (
    echo [WARN] No built frontend. Web UI will not work until built.
    echo Build manually: cd frontend ^&^& npm ci ^&^& npm run build
  )
)

REM ---------- Resources ----------
echo [..] Checking resources...
if exist "resources\silero-models\c9e311e020562111e5414ff93d47e0a1-v3_1_ru.pt" (
  echo [OK] Silero model found.
) else (
  echo [WARN] Silero model not found (will auto-download on first run if internet).
)
if exist "resources\vosk-models\*.zip" (
  echo [OK] Vosk model found.
  dir /B "resources\vosk-models\*.zip"
) else (
  echo [WARN] Vosk model not found in resources\vosk-models\
  echo Download: https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
)

REM ---------- Final check ----------
echo [..] Final check...
python -c "import irene; print('  import irene - OK')"
if !errorlevel!==0 echo [WARN] import irene failed.
if exist "frontend\dist\index.html" (
  echo [OK] Frontend dist found.
) else if exist "irene_plugin_web_face_frontend\frontend-dist\index.html" (
  echo [OK] Frontend dist found (frontend-dist).
) else (
  echo [WARN] Frontend dist not found.
)

echo.
echo === Install complete ===
echo.
echo Run (from repo root):
echo   %VENV_DIR%\Scripts\activate.bat
echo   python -m irene                 (web on https://localhost:8086)
echo   python -m irene --help
echo   python -m irene -T console      (console mode)
echo.
echo Frontend dev (hot reload):
echo   cd frontend ^&^& npm run dev      (http://localhost:5173)
echo.
echo Useful:
echo   set IRENE_HOME=%CD%\irene-home ^&^& python -m irene
echo   install.bat --lite              (without torch)
echo   install.bat --reinstall         (clean reinstall)
echo.
echo If sound not working: check mic/speakers in Windows settings and
echo   pip show sounddevice (should be installed)
echo.
pause
endlocal
