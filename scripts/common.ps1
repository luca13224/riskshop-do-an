# Hàm dùng chung cho các script vận hành (start / stop / check / prepare_demo). Không chạy trực tiếp file này.
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Python = Join-Path $Backend ".venv\Scripts\python.exe"
$XamppMysql = "D:\xampp\mysql\bin"

function Write-Ok($msg) { Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Write-Bad($msg) { Write-Host "  [LỖI] $msg" -ForegroundColor Red }
function Write-Warn($msg) { Write-Host "  [CHÚ Ý] $msg" -ForegroundColor Yellow }
function Write-Step($msg) { Write-Host ""; Write-Host "== $msg" -ForegroundColor Cyan }

# Cổng có chương trình đang lắng nghe không (thử kết nối TCP, nhanh hơn Test-NetConnection).
# Thử cả IPv4 và IPv6: MariaDB, backend nghe ở 127.0.0.1, còn Vite (frontend) có thể chỉ nghe ở ::1.
function Test-Port([int]$Port) {
    foreach ($addr in "127.0.0.1", "::1") {
        $family = [System.Net.Sockets.AddressFamily]::InterNetwork
        if ($addr -eq "::1") { $family = [System.Net.Sockets.AddressFamily]::InterNetworkV6 }
        $client = New-Object System.Net.Sockets.TcpClient($family)
        try {
            $task = $client.ConnectAsync($addr, $Port)
            if ($task.Wait(500) -and $client.Connected) { return $true }
        } catch {} finally { $client.Close() }
    }
    return $false
}

function Wait-Port([int]$Port, [int]$Seconds = 60) {
    for ($i = 0; $i -lt $Seconds; $i++) {
        if (Test-Port $Port) { return $true }
        Start-Sleep -Seconds 1
    }
    return $false
}

# Gọi một địa chỉ web, trả về mã HTTP (0 nếu không gọi được)
function Get-HttpStatus([string]$Url) {
    try { return (Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 $Url).StatusCode } catch {
        if ($_.Exception.Response) { return [int]$_.Exception.Response.StatusCode }
        return 0
    }
}

# Tiến trình python đang chạy worker (worker.main)
function Get-WorkerProcess {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*worker.main*" }
}

# Tắt một tiến trình và mọi tiến trình con của nó
function Stop-Tree([int]$ProcId) {
    Get-CimInstance Win32_Process -Filter "ParentProcessId=$ProcId" -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Tree $_.ProcessId }
    Stop-Process -Id $ProcId -Force -ErrorAction SilentlyContinue
}

# Tình trạng dữ liệu demo (JSON) từ backend/scripts/demo_status.py
function Get-DemoStatus {
    Push-Location $Backend
    try {
        $env:PYTHONWARNINGS = "ignore"
        $line = & $Python scripts/demo_status.py 2>$null | Select-Object -Last 1
        if ($line) { return $line | ConvertFrom-Json }
        return $null
    } finally { Pop-Location }
}
