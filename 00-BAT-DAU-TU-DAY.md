# Bắt đầu từ đây — thông tin demo RiskShop

> File ghim ở đầu repo: link, tài khoản demo, cách chạy, các cảnh demo. Cập nhật lần cuối: 2026-11-05.
> Tài khoản demo dùng chung mật khẩu `11111111` (chỉ là dữ liệu demo chạy trên máy local, tạo bởi *demo reset*; không dùng cho hệ thống thật).

## 1. Đường dẫn

| | Địa chỉ |
|---|---|
| GitHub (công khai) | https://github.com/luca13224/riskshop-do-an |
| Shop (khách hàng) | http://localhost:5173 |
| Risk Console (nhân viên) | http://localhost:5173/console |
| Tài liệu API (tự sinh) | http://localhost:8000/docs |
| Kịch bản demo | [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) |
| Quyết định kỹ thuật (ADR) | [docs/DECISIONS.md](docs/DECISIONS.md) |
| Bộ luật | [docs/RULES_V0.md](docs/RULES_V0.md) |
| Kết quả thực nghiệm | [docs/TEST_PLAN.md](docs/TEST_PLAN.md) |
| Dàn ý báo cáo | [docs/BAO_CAO_DAN_Y.md](docs/BAO_CAO_DAN_Y.md) |

## 2. Tài khoản demo

Mật khẩu chung: **`11111111`** (đổi được bằng `DEMO_PASSWORD` trong `backend/.env`). Danh sách cũng được ghi vào `backend/.env.accounts` sau mỗi lần *demo reset* (mục 4), để các script demo đọc.

| Email | Vai trò | Dùng để |
|---|---|---|
| `admin1@test.com` | Admin | Mọi màn hình Console, **Attack Lab**, khóa / gỡ khóa tài khoản |
| `admin2@test.com` | Risk Manager | Kết luận khiếu nại, sửa luật, khóa / gỡ khóa, xem liên hệ đầy đủ |
| `admin3@test.com` | Analyst | Xử lý case (không sửa luật, không gỡ khóa) |
| `user1@test.com` | Khách mới (Minh) | Cảnh 1: mua hàng bình thường, có sẵn mã NGUOIMOI trong túi voucher |
| `user2@test.com` | Khách có lịch sử bùng COD (Khang) | Cảnh 5, 5c, 5e: bị ẩn COD; cố đặt lặp thì bị khóa |
| `user3@test.com` | Khách uy tín, 30 đơn (Lan) | Cảnh 5: đơn COD giá trị cao vẫn được duyệt |

Mã giảm giá: **NGUOIMOI** (−50.000đ, khách mới, đơn từ 200.000đ, cấp sẵn khi đăng ký) · **GIAM10** (−10%, tối đa 100.000đ, đơn từ 500.000đ).

## 3. Chạy hệ thống (4 cửa sổ)

1. **MariaDB:** mở `D:\xampp\xampp-control.exe` → Start ở dòng MySQL.
2. **Backend:** `cd backend` → `.venv/Scripts/python -m uvicorn app.main:app --port 8000` (sửa code backend xong thì dừng và chạy lại).
3. **Worker** (mở case, chạy Attack Lab): `cd backend` → `.venv/Scripts/python -m worker.main`
4. **Frontend:** `cd frontend` → `npm run dev`

## 4. Trước buổi demo

- **Demo reset** (XÓA toàn bộ dữ liệu, tạo lại sản phẩm, voucher, luật, nhân viên admin1–3, khách user1–3; chỉ chạy khi `.env` có `DEMO_MODE=true`):
  `cd backend` → `.venv/Scripts/python -m app.modules.lab.reset --yes`
- **Lịch sử 14 ngày** cho Dashboard có số liệu: `.venv/Scripts/python -m simulator.history --days 14 --yes`
- Kiểm tra nhanh: `.venv/Scripts/python -m pytest -q` (hiện 215 test qua).

## 5. Các cảnh có thao tác đặc biệt

| Cảnh | Làm gì |
|---|---|
| 2. Farm voucher | Console → **Attack Lab** (đăng nhập admin) → chạy "farm_voucher" |
| 5c. Cố đặt lặp → khóa 24 giờ | `cd backend` → `.venv/Scripts/python scripts/demo_attack.py spam-cod user2@test.com --times 4` → mở Case của Khang trên Console |
| 5d. Khiếu nại | Đăng nhập Khang (user2) → Khiếu nại → gửi; đăng nhập Risk Manager (admin2) → Khiếu nại → Chấp nhận (tự gỡ khóa) |
| 5e. Né lệnh khóa bằng tài khoản mới | Risk Manager (admin2) mở Case của Khang → **Khóa vô thời hạn** (ghi lý do) → `.venv/Scripts/python scripts/demo_attack.py evade` → tài khoản mới bị khóa thanh toán 30 ngày; đồ thị liên kết có vòng đỏ đặc ở Khang |
| Sau buổi demo | Gỡ khóa trên Console (ghi lý do) hoặc chạy lại demo reset |

## 6. Quy tắc khóa (tóm tắt để trả lời hội đồng)

- Lần đặt hàng bị từ chối thứ 4 trong 24 giờ → khóa mua 24 giờ; tái phạm trong 30 ngày → khóa vô thời hạn (ADR-010).
- Tài khoản mới chung **≥ 2** điểm (thiết bị, SĐT nhận hàng, địa chỉ) với tài khoản đang bị khóa vô thời hạn, hoặc chung 1 điểm **và** spam mã người mới → khóa thanh toán 30 ngày, tái phạm 60 ngày. Chung 1 điểm mà không spam (người nhà dùng chung máy) → chỉ trừ điểm tin cậy và mở case. Chung IP → không tính (ADR-011, ADR-013).
- Mọi lệnh khóa: tự mở case, ghi audit, khách vẫn đăng nhập và khiếu nại được, Risk Manager gỡ được (bắt buộc lý do).
