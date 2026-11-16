@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 goto no_python

if not exist ".venv-separation\Scripts\python.exe" (
  py -3.10 -m venv ".venv-separation"
  if errorlevel 1 goto failed
)

".venv-separation\Scripts\python.exe" -m pip install -r requirements-separation.txt
if errorlevel 1 goto failed

echo.
echo Bird-MixIT environment is ready. Restart or return to the app.
pause
goto end

:no_python
echo Python 3.10 and the Python Launcher (py) are required.
:failed
echo.
echo Separation setup failed. Read the error above and check README.md.
pause
exit /b 1

:end
endlocal
