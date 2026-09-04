@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Drag a project folder onto this file, or pass it as the first argument.
  pause
  exit /b 1
)
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 app.py --project "%~1" --open
  goto finish
)
if exist "%USERPROFILE%.cachecodex-runtimescodex-primary-runtimedependenciespythonpython.exe" (
  "%USERPROFILE%.cachecodex-runtimescodex-primary-runtimedependenciespythonpython.exe" app.py --project "%~1" --open
  goto finish
)
where python >nul 2>&1
if %errorlevel%==0 (
  python app.py --project "%~1" --open
  goto finish
)
echo Python 3.10 or newer was not found.
:finish
if errorlevel 1 pause
