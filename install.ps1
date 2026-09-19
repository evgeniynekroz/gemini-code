# Gemini Code PowerShell installer
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Установка Gemini Code (Windows)     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Python
$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $pythonCmd) {
    $pythonCmd = (Get-Command py -ErrorAction SilentlyContinue)
}

if (-not $pythonCmd) {
    Write-Host "[ERROR] Python не найден! Установите Python с https://python.org и включите галочку 'Add to PATH'." -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Установка зависимостей через pip..." -ForegroundColor Green
& $pythonCmd.Source -m pip install -r "$PSScriptRoot\requirements.txt"
& $pythonCmd.Source -m pip install -e "$PSScriptRoot"

# Register global command 'geminicode' into WindowsApps or npm directory (always on PATH)
$installedGlobally = $false
$appsDir = "$env:LOCALAPPDATA\Microsoft\WindowsApps"
if (Test-Path $appsDir) {
    Copy-Item -Force "$PSScriptRoot\geminicode.cmd" "$appsDir\geminicode.cmd"
    Copy-Item -Force "$PSScriptRoot\geminicode.cmd" "$appsDir\gemini-code.cmd"
    $installedGlobally = $true
}

$npmDir = "$env:APPDATA\npm"
if (Test-Path $npmDir) {
    Copy-Item -Force "$PSScriptRoot\geminicode.cmd" "$npmDir\geminicode.cmd"
    Copy-Item -Force "$PSScriptRoot\geminicode.cmd" "$npmDir\gemini-code.cmd"
    $installedGlobally = $true
}

Write-Host "`n[OK] Gemini Code успешно установлен!" -ForegroundColor Green
Write-Host "Теперь откройте терминал в ЛЮБОЙ папке и запустите: geminicode" -ForegroundColor Cyan