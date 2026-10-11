@echo off
for %%I in ("%~dp0..\..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"
if not exist ".env" (
  echo 请先双击 start-wepulse.cmd 完成首次安装。
  pause
  exit /b 1
)
start "" notepad.exe "%PROJECT_ROOT%\.env"
