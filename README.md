# Đồ án tốt nghiệp — Hệ thống kiểm soát rủi ro và ngăn ngừa lạm dụng chính sách trên sàn TMĐT

Sinh viên: Luca — Hệ thống thông tin quản lý, Trường Đại học Thủy Lợi.

## Cách chạy (môi trường dev trên Windows)

> **Thông tin demo (link, tài khoản, các cảnh): xem [00-BAT-DAU-TU-DAY.md](00-BAT-DAU-TU-DAY.md).**

**Cần có:** XAMPP tại `D:\xampp` (dùng MariaDB), Python 3.11, Node.js 24.

1. **Bật MariaDB:** mở `D:\xampp\xampp-control.exe` → bấm **Start** ở dòng MySQL.
2. **Backend** (lần đầu):
   ```bash
   cd backend
   python -m venv .venv
   .venv/Scripts/python -m pip install -r requirements-dev.txt
   cp .env.example .env   # rồi điền mật khẩu CSDL
   .venv/Scripts/alembic upgrade head
   .venv/Scripts/python -m app.modules.catalog.seed     # 24 sản phẩm công nghệ mẫu (chạy lại an toàn)
   .venv/Scripts/python -m app.modules.promotion.seed   # voucher NGUOIMOI, GIAM10
   .venv/Scripts/python -m app.modules.risk.seed        # bộ luật rủi ro R01–R10 + ngưỡng quyết định
   ```
   Chạy: `.venv/Scripts/python -m uvicorn app.main:app --port 8000` (sửa code backend xong thì dừng và chạy lại; `--reload` hay bị kẹt trên Windows) → tài liệu API: http://localhost:8000/docs
   **Worker** (mở case, chạy kịch bản Attack Lab), chạy ở cửa sổ dòng lệnh thứ hai: `.venv/Scripts/python -m worker.main`
   **Attack Lab** chỉ hiện khi `.env` có `DEMO_MODE=true` và chỉ tài khoản `admin` dùng được.

   **Demo reset** (trước buổi demo hoặc trước mỗi đợt đo): XÓA TOÀN BỘ dữ liệu rồi tạo lại sản phẩm, voucher, luật v1, nhân viên `admin1–3@test.com` và khách `user1–3@test.com` (Minh, Khang, Lan), mật khẩu chung `11111111` (cấu hình `DEMO_PASSWORD`). Danh sách ghi vào `backend/.env.accounts`. Chỉ chạy được khi `DEMO_MODE=true`.
   ```bash
   .venv/Scripts/python -m app.modules.lab.reset --yes
   ```
   Test: `.venv/Scripts/python -m pytest -q`
3. **Frontend** (lần đầu `npm install`): `cd frontend && npm run dev` → http://localhost:5173

**Tài khoản nhân viên** (API đăng ký chỉ tạo được khách hàng), chạy trong thư mục `backend/`:
```bash
.venv/Scripts/python -m app.modules.auth.cli --email analyst@riskshop.test --name "Analyst Demo" --role analyst
```
Vai trò: `analyst`, `risk_manager`, `admin`. Mật khẩu được hỏi khi chạy. Tài khoản test local nên ghi vào `backend/.env.accounts` (đã nằm trong `.gitignore`).

Đăng nhập bằng tài khoản nhân viên sẽ vào được http://localhost:5173/console; khách hàng vào đó sẽ bị chặn.

## Chạy thực nghiệm mô phỏng
Cần `SIM_DATABASE_URL` trong `backend/.env` (CSDL riêng, sẽ bị xóa mỗi lần chạy):
```
cd backend
.venv/Scripts/python -m alembic -x target=sim upgrade head
.venv/Scripts/python -m simulator --dataset dev --seed 1
```
Báo cáo ghi vào `docs/thuc_nghiem/mo_phong/v<phiên bản bộ dữ liệu>/` (mục lục: [docs/thuc_nghiem/README.md](docs/thuc_nghiem/README.md)). Tập `test` chỉ chạy sau khi đã khóa luật (`--confirm-test`).

## Cấu trúc thư mục
| Thư mục | Nội dung |
|---|---|
| `backend/` | FastAPI: `app/core` (cấu hình, CSDL, lỗi), `app/modules` (các module nghiệp vụ, Risk Engine), `migrations` (Alembic), `tests`, `worker`, `simulator` (bộ mô phỏng), `scripts` (đo tải, kiểm tra audit, demo, kiểm tra link) |
| `frontend/` | React + Vite + TypeScript + Tailwind + shadcn/ui: `shop/` (cửa hàng), `console/` (Risk Console) |
| `docs/` | Tài liệu dự án, kết quả thực nghiệm (`thuc_nghiem/`), bản tư vấn (`tu_van/`), sơ đồ (`so_do/`) |

Vai trò của từng file code: [docs/BAN_DO_MA_NGUON.md](docs/BAN_DO_MA_NGUON.md).

## Tài liệu dự án
| File | Nội dung |
|---|---|
| [docs/TONG_QUAN.md](docs/TONG_QUAN.md) | Mục tiêu, phạm vi, hiện trạng |
| [docs/YEU_CAU.md](docs/YEU_CAU.md) | Yêu cầu nghiệp vụ và chức năng |
| [docs/KIEN_TRUC.md](docs/KIEN_TRUC.md) | Kiến trúc và các thành phần |
| [docs/QUYET_DINH.md](docs/QUYET_DINH.md) | Các quyết định kỹ thuật (ADR) |
| [docs/LO_TRINH.md](docs/LO_TRINH.md) | Kế hoạch, milestone |
| [docs/KICH_BAN_DEMO.md](docs/KICH_BAN_DEMO.md) | Kịch bản demo bảo vệ; phạm vi MVP suy ra từ đây |
| [docs/BO_LUAT_RUI_RO.md](docs/BO_LUAT_RUI_RO.md) | Bộ luật rủi ro R01–R18: đặc trưng, luật, ma trận quyết định |
| [docs/ERD.md](docs/ERD.md) | Thiết kế CSDL: sơ đồ, index theo đặc trưng, ràng buộc, dữ liệu cá nhân |
| [docs/KIEM_THU.md](docs/KIEM_THU.md) | Chiến lược và kịch bản kiểm thử |
| [docs/NHAT_KY_TIEN_DO.md](docs/NHAT_KY_TIEN_DO.md) | Nhật ký tiến độ |
| [docs/BAN_DO_MA_NGUON.md](docs/BAN_DO_MA_NGUON.md) | Bản đồ mã nguồn: file nào ở đâu, làm gì |
| [docs/SO_TAY_VAN_HANH.md](docs/SO_TAY_VAN_HANH.md) | Sổ tay vận hành: bật / tắt bằng `scripts\*.bat`, chuẩn bị demo, xử lý sự cố |
| [docs/thuc_nghiem/](docs/thuc_nghiem/README.md) | Kết quả mô phỏng, đo tải, audit |
| `docs/tu_van/` | Bản tư vấn, rà soát, thiết kế (chưa phải quyết định) |
| [docs/tu_van/](docs/tu_van/) | Các bản tư vấn, phản biện (chưa phải quyết định) |
