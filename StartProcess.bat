@echo off
setlocal

rem ===== CONFIG =====
set "APP=%~dp0\FocusedUpScript\FocusedUpScript.exe"
set "DELAY=5"
set "MAX_RESTARTS=10"
rem ==================

set "LOCK=%TEMP%\app_watchdog.lock"
set /a RESTARTS=0
set /a PINGS=%DELAY%+1

rem Single-instance guard: if another watchdog holds the lock, this call is skipped
( call :main ) 9>"%LOCK%"
exit /b

:main
if not exist "%APP%" exit /b 1

:run
if exist "%~dp0stop.flag" exit /b 0

start "" /wait "%APP%"
set "RC=%errorlevel%"

rem Clean exit: stop watching
if "%RC%"=="0" exit /b 0

rem Non-zero exit: give up after too many restarts, otherwise wait and relaunch
set /a RESTARTS+=1
if %RESTARTS% gtr %MAX_RESTARTS% exit /b 1

rem ping -n 6 is about 5 seconds (works hidden/scheduled, unlike timeout)
ping -n %PINGS% 127.0.0.1 >nul
goto run