@echo off
setlocal
chcp 65001 >nul
python -m gemini_code.cli %*
if %ERRORLEVEL% NEQ 0 (
    py -m gemini_code.cli %*
)
endlocal