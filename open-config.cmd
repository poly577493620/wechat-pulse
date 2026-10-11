@echo off
cd /d "%~dp0"
if not exist ".env" (
  echo 请先双击 start-wepulse.cmd 完成首次安装。
  pause
  exit /b 1
)
start "" notepad.exe "%~dp0.env"
