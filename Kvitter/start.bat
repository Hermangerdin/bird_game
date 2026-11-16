@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 goto no_python

if not exist ".venv\Scripts\python.exe" (
  py -3.10 -m venv ".venv"
  if errorlevel 1 goto failed
)

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed

".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
goto end

:no_python
echo Python 3.10 and the Python Launcher (py) are required.
goto failed

:failed
echo.
echo Setup or startup failed. Read the error above and check README.md.
pause
exit /b 1

:end
endlocal
