# Bật toàn bộ hệ thống RiskShop: MariaDB, backend (cổng 8000), worker, frontend (cổng 5173).
# Thành phần nào đang chạy rồi thì bỏ qua. Mỗi thành phần mở trong một cửa sổ riêng (đóng cửa sổ là tắt).
. (Join-Path $PSScriptRoot "common.ps1")

Write-Step "1/4 MariaDB (cổng 3306)"
if (Test-Port 3306) { Write-Ok "đang chạy" } else {
    if (-not (Test-Path "$XamppMysql\mysqld.exe")) { Write-Bad "không thấy $XamppMysql\mysqld.exe (XAMPP cài ở chỗ khác?)"; exit 1 }
    Start-Process -FilePath "$XamppMysql\mysqld.exe" -ArgumentList "--defaults-file=$XamppMysql\my.ini", "--standalone" `
        -WorkingDirectory $XamppMysql -WindowStyle Minimized
    if (Wait-Port 3306 60) { Write-Ok "đã bật" } else { Write-Bad "MariaDB không lên sau 60 giây: mở D:\xampp\xampp-control.exe, bấm Start ở dòng MySQL, xem log"; exit 1 }
}

Write-Step "2/4 Backend (http://localhost:8000)"
if (Test-Port 8000) { Write-Ok "đang chạy" } else {
    Start-Process powershell -ArgumentList "-NoExit", "-Command",
        "`$host.UI.RawUI.WindowTitle='RiskShop backend'; Set-Location '$Backend'; & '$Python' -m uvicorn app.main:app --port 8000"
    if ((Wait-Port 8000 60) -and ((Get-HttpStatus "http://127.0.0.1:8000/api/health") -eq 200)) { Write-Ok "đã bật, CSDL kết nối được" }
    else { Write-Bad "backend chưa trả lời: xem cửa sổ 'RiskShop backend' để biết lỗi"; exit 1 }
}

Write-Step "3/4 Worker (việc nền: mở case, Attack Lab)"
if (Get-WorkerProcess) { Write-Ok "đang chạy" } else {
    Start-Process powershell -ArgumentList "-NoExit", "-Command",
        "`$host.UI.RawUI.WindowTitle='RiskShop worker'; Set-Location '$Backend'; & '$Python' -m worker.main"
    Start-Sleep -Seconds 3
    if (Get-WorkerProcess) { Write-Ok "đã bật" } else { Write-Bad "worker không chạy: xem cửa sổ 'RiskShop worker'" }
}

Write-Step "4/4 Frontend (http://localhost:5173)"
if (Test-Port 5173) { Write-Ok "đang chạy" } else {
    Start-Process powershell -ArgumentList "-NoExit", "-Command",
        "`$host.UI.RawUI.WindowTitle='RiskShop frontend'; Set-Location '$Frontend'; npm run dev"
    if (Wait-Port 5173 90) { Write-Ok "đã bật" } else { Write-Bad "frontend chưa lên: xem cửa sổ 'RiskShop frontend'"; exit 1 }
}

Write-Host ""
Write-Host "Xong. Shop: http://localhost:5173   ·   Risk Console: http://localhost:5173/console" -ForegroundColor Green
Write-Host "Kiểm tra dữ liệu demo còn mới không: chạy scripts\check.bat"
if ($args -notcontains "-NoBrowser") { Start-Process "http://localhost:5173/console" }
