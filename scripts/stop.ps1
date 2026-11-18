# Tắt backend, worker, frontend. MariaDB để chạy (an toàn cho dữ liệu); muốn tắt cả MariaDB thì
# đóng bằng D:\xampp\xampp-control.exe (nút Stop ở dòng MySQL).
. (Join-Path $PSScriptRoot "common.ps1")

Write-Step "Tắt backend (8000) và frontend (5173)"
foreach ($port in 8000, 5173) {
    # Socket đang lắng nghe có cổng đích = 0 (không lọc theo State: có máy hiển thị State rỗng)
    $owners = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        Where-Object { $_.RemotePort -eq 0 -and $_.OwningProcess -gt 0 } | Select-Object -ExpandProperty OwningProcess -Unique
    if (-not $owners) { Write-Ok "cổng $port không có gì chạy"; continue }
    foreach ($procId in $owners) {
        # Tắt cả tiến trình cha nếu đó là cửa sổ do start.ps1 mở (uvicorn --reload / npm có tiến trình cha)
        $parent = (Get-CimInstance Win32_Process -Filter "ProcessId=$procId" -ErrorAction SilentlyContinue).ParentProcessId
        Stop-Tree $procId
        $p = Get-CimInstance Win32_Process -Filter "ProcessId=$parent" -ErrorAction SilentlyContinue
        if ($p -and ($p.CommandLine -like "*uvicorn*" -or $p.CommandLine -like "*npm*" -or $p.CommandLine -like "*vite*")) { Stop-Tree $parent }
    }
    Start-Sleep -Seconds 1
    if (Test-Port $port) { Write-Bad "cổng $port vẫn bận" } else { Write-Ok "đã tắt cổng $port" }
}

Write-Step "Tắt worker"
$workers = Get-WorkerProcess
if (-not $workers) { Write-Ok "worker không chạy" } else {
    $workers | ForEach-Object { Stop-Tree $_.ProcessId }
    Write-Ok "đã tắt $(@($workers).Count) worker"
}
Write-Host ""
Write-Host "MariaDB vẫn chạy (cần cho lần bật sau). Tắt hẳn: D:\xampp\xampp-control.exe -> Stop ở dòng MySQL."
