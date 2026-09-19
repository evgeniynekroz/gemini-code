@echo off
setlocal
chcp 65001 >nul
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python -m gemini_code.cli %*
    exit /b %ERRORLEVEL%
)
py -m gemini_code.cli %*
exit /b %ERRORLEVEL%
