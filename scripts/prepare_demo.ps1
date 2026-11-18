# Chuẩn bị dữ liệu cho buổi demo / bảo vệ: XÓA dữ liệu demo cũ, tạo lại tài khoản + sản phẩm + luật,
# rồi sinh 14 ngày lịch sử tính đến hôm nay để Tổng quan / Báo cáo có số liệu.
# Chạy sáng ngày bảo vệ (hoặc tối hôm trước). Mất khoảng 3–6 phút.
. (Join-Path $PSScriptRoot "common.ps1")

Write-Host "Script này sẽ XÓA TOÀN BỘ dữ liệu trong CSDL demo (riskshop) rồi tạo lại." -ForegroundColor Yellow
Write-Host "Không ảnh hưởng mã nguồn, tài liệu hay kết quả thực nghiệm."
if ($args -notcontains "-Yes") {
    $answer = Read-Host "Gõ CO rồi Enter để tiếp tục"
    if ($answer -ne "CO") { Write-Host "Đã hủy, không thay đổi gì."; exit 0 }
}

Write-Step "1/4 Kiểm tra MariaDB"
if (-not (Test-Port 3306)) { Write-Bad "MariaDB chưa chạy -> chạy scripts\start.bat trước"; exit 1 }
Write-Ok "MariaDB đang chạy"

Push-Location $Backend
try {
    $env:PYTHONWARNINGS = "ignore"
    Write-Step "2/4 Demo reset (xóa và tạo lại dữ liệu chuẩn)"
    & $Python -m app.modules.lab.reset --yes
    if ($LASTEXITCODE -ne 0) { Write-Bad "demo reset lỗi (DEMO_MODE=true trong backend\.env chưa?)"; exit 1 }
    Write-Ok "xong"

    Write-Step "3/4 Sinh lịch sử 14 ngày (vài phút, đừng đóng cửa sổ)"
    & $Python -m simulator.history --days 14 --yes
    if ($LASTEXITCODE -ne 0) { Write-Bad "sinh lịch sử lỗi, xem thông báo ở trên"; exit 1 }
    Write-Ok "xong"
} finally { Pop-Location }

Write-Step "4/4 Kiểm tra lại"
$s = Get-DemoStatus
if ($s -and $s.decisions_7d -ge 50 -and $s.missing_accounts.Count -eq 0) {
    Write-Ok "$($s.decisions_7d) lượt chấm điểm trong 7 ngày, đủ tài khoản demo"
} else { Write-Bad "dữ liệu chưa như mong đợi: $($s | ConvertTo-Json -Compress)"; exit 1 }

Write-Host ""
Write-Host "Sẵn sàng demo. Tài khoản: admin1/admin2/admin3@test.com (Admin / Risk Manager / Analyst)," -ForegroundColor Green
Write-Host "user1/user2/user3@test.com (khách), mật khẩu chung 11111111." -ForegroundColor Green
Write-Host "Nếu backend đang chạy thì không cần khởi động lại. Kịch bản: docs\KICH_BAN_DEMO.md"
