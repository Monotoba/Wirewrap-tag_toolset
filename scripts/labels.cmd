@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0labels.ps1" %*
exit /b %ERRORLEVEL%
