# Kiểm tra nhanh toàn hệ thống (chỉ đọc, không sửa gì). Chạy trước mỗi lần tập demo và sáng ngày bảo vệ.
. (Join-Path $PSScriptRoot "common.ps1")
$problems = 0

Write-Step "Thành phần đang chạy"
if (Test-Port 3306) { Write-Ok "MariaDB (3306)" } else { Write-Bad "MariaDB chưa chạy -> chạy scripts\start.bat"; $problems++ }
$health = Get-HttpStatus "http://127.0.0.1:8000/api/health"
if ($health -eq 200) { Write-Ok "Backend (8000), kết nối CSDL tốt" }
elseif ($health -eq 503) { Write-Bad "Backend chạy nhưng không kết nối được CSDL -> bật MariaDB"; $problems++ }
else { Write-Bad "Backend chưa chạy -> chạy scripts\start.bat"; $problems++ }
if (Get-WorkerProcess) { Write-Ok "Worker" } else { Write-Bad "Worker chưa chạy (case sẽ không tự mở) -> scripts\start.bat"; $problems++ }
if ((Get-HttpStatus "http://localhost:5173") -eq 200) { Write-Ok "Frontend (5173)" } else { Write-Bad "Frontend chưa chạy -> scripts\start.bat"; $problems++ }

Write-Step "Dữ liệu demo"
if (-not (Test-Port 3306)) { Write-Warn "bỏ qua vì MariaDB chưa chạy" } else {
    $s = Get-DemoStatus
    if (-not $s -or $s.db -ne "ok") { Write-Bad "không đọc được CSDL ($($s.db))"; $problems++ } else {
        if ($s.demo_mode) { Write-Ok "DEMO_MODE=true (cho phép demo reset, Attack Lab)" } else { Write-Warn "DEMO_MODE chưa bật trong backend\.env" }
        if ($s.missing_accounts.Count -eq 0) { Write-Ok "đủ 6 tài khoản demo (admin1-3, user1-3, mật khẩu 11111111)" }
        else { Write-Bad "thiếu tài khoản: $($s.missing_accounts -join ', ') -> chạy scripts\prepare_demo.bat"; $problems++ }
        if ($s.decisions_7d -ge 50) { Write-Ok "$($s.decisions_7d) lượt chấm điểm trong 7 ngày: biểu đồ Tổng quan / Báo cáo có số liệu" }
        else { Write-Bad "chỉ $($s.decisions_7d) lượt chấm điểm trong 7 ngày (lần cuối cách đây $($s.hours_since_last) giờ): biểu đồ sẽ trống -> chạy scripts\prepare_demo.bat"; $problems++ }
        if ($s.active_restrictions -gt 0) { Write-Warn "$($s.active_restrictions) tài khoản đang bị khóa (còn từ lần demo trước?): gỡ trên Console hoặc chạy prepare_demo" }
        if ($s.jobs_queued -gt 20) { Write-Warn "$($s.jobs_queued) việc nền đang chờ: worker có chạy không?" }
    }
}

Write-Host ""
if ($problems -eq 0) { Write-Host "Mọi thứ sẵn sàng." -ForegroundColor Green } else { Write-Host "Có $problems vấn đề, xem các dòng [LỖI] ở trên." -ForegroundColor Red }
exit $problems
