# Gemini Code (geminicode) Windows Installer
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Установка Gemini Code (geminicode)  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Поиск установленного Python
$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $pythonCmd) {
    $pythonCmd = (Get-Command py -ErrorAction SilentlyContinue)
}

if (-not $pythonCmd) {
    Write-Host "[ERROR] Python не найден!" -ForegroundColor Red
    Write-Host "Пожалуйста, установите Python 3.9+ с https://www.python.org/downloads/ (обязательно включите галочку 'Add python.exe to PATH')." -ForegroundColor Yellow
    exit 1
}

Write-Host "[INFO] Найден Python: $($pythonCmd.Source)" -ForegroundColor Green

# 2. Установка пакета geminicode
if ($PSScriptRoot -and (Test-Path "$PSScriptRoot\pyproject.toml")) {
    Write-Host "[INFO] Локальная установка из папки проекта..." -ForegroundColor Green
    & $pythonCmd.Source -m pip install -r "$PSScriptRoot\requirements.txt"
    & $pythonCmd.Source -m pip install -e "$PSScriptRoot"
} else {
    Write-Host "[INFO] Установка последней версии geminicode с GitHub..." -ForegroundColor Green
    & $pythonCmd.Source -m pip install --upgrade git+https://github.com/evgeniynekroz/gemini-code.git
}

# 3. Регистрация глобальной команды geminicode в WindowsApps (эта папка есть в PATH у всех пользователей Windows)
$appsDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
$batchCode = @"
@echo off
setlocal
chcp 65001 >nul
python -m gemini_code.cli %*
if %ERRORLEVEL% NEQ 0 (
    py -m gemini_code.cli %*
)
endlocal
"@

if (Test-Path $appsDir) {
    Set-Content -Path "$appsDir\geminicode.cmd" -Value $batchCode -Encoding ASCII
    Set-Content -Path "$appsDir\gemini-code.cmd" -Value $batchCode -Encoding ASCII
    Write-Host "[OK] Глобальная команда geminicode зарегистрирована в системе!" -ForegroundColor Green
}

$npmDir = "$env:APPDATA\npm"
if (Test-Path $npmDir) {
    Set-Content -Path "$npmDir\geminicode.cmd" -Value $batchCode -Encoding ASCII
    Set-Content -Path "$npmDir\gemini-code.cmd" -Value $batchCode -Encoding ASCII
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "   УСТАНОВКА УСПЕШНО ЗАВЕРШЕНА!         " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Теперь откройте командную строку (CMD) в ЛЮБОЙ папке и напишите:" -ForegroundColor White
Write-Host "  geminicode" -ForegroundColor Cyan
Write-Host "Интерфейс запустится именно в этой папке!`n" -ForegroundColor White