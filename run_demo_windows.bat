@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 app.py --project examplesdemo --open
  goto finish
)
if exist "%USERPROFILE%.cachecodex-runtimescodex-primary-runtimedependenciespythonpython.exe" (
  "%USERPROFILE%.cachecodex-runtimescodex-primary-runtimedependenciespythonpython.exe" app.py --project examplesdemo --open
  goto finish
)
where python >nul 2>&1
if %errorlevel%==0 (
  python app.py --project examplesdemo --open
  goto finish
)
echo Python 3.10 or newer was not found.
:finish
if errorlevel 1 pause
