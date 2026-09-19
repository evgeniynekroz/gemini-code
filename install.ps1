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
& $pythonCmd.Source -m pip install --upgrade pip
& $pythonCmd.Source -m pip install -r requirements.txt
& $pythonCmd.Source -m pip install -e .

Write-Host "`n[OK] Gemini Code успешно установлен!" -ForegroundColor Green
Write-Host "Запустите команду: gemini-code" -ForegroundColor Cyan