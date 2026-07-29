@echo off
set elapsed=0
set prefix=PixivSyncFlag
set timestamp=%date:~0,4%%date:~5,2%%date:~8,2%%time:~0,2%%time:~3,2%%time:~6,2%
set "timestamp=%timestamp: =0%"
echo Waiting for network...

:wait_network
ping -n 1 8.8.8.8 >nul
if not errorlevel 1 (
    echo Network is ready!
    uv run sync.py
    attrib -H %prefix%*
    del /f /q %prefix%*
    type nul > %prefix%%timestamp%
    attrib +H %prefix%%timestamp%
    exit /b
)

timeout /t 5 >nul
set /a elapsed+=5

if %elapsed% geq 30 (
    echo Network timeout. Exiting...
    exit /b 1
)

goto wait_network