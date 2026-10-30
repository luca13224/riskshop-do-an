# Đồ án tốt nghiệp — Hệ thống kiểm soát rủi ro và ngăn ngừa lạm dụng chính sách trên sàn TMĐT

Sinh viên: Luca — Hệ thống thông tin quản lý, Trường Đại học Thủy Lợi.

## Cách chạy (môi trường dev trên Windows)

**Cần có:** XAMPP tại `D:\xampp` (dùng MariaDB), Python 3.11, Node.js 24.

1. **Bật MariaDB:** mở `D:\xampp\xampp-control.exe` → bấm **Start** ở dòng MySQL.
2. **Backend** (lần đầu):
   ```bash
   cd backend
   python -m venv .venv
   .venv/Scripts/python -m pip install -r requirements-dev.txt
   cp .env.example .env   # rồi điền mật khẩu CSDL
   .venv/Scripts/alembic upgrade head
   .venv/Scripts/python -m app.modules.catalog.seed     # 16 sản phẩm mẫu (chạy lại an toàn)
   .venv/Scripts/python -m app.modules.promotion.seed   # voucher TANTHU, GIAM10
   .venv/Scripts/python -m app.modules.risk.seed        # bộ luật rủi ro R01–R10 + ngưỡng quyết định
   ```
   Chạy: `.venv/Scripts/python -m uvicorn app.main:app --port 8000` (sửa code backend xong thì dừng và chạy lại; `--reload` hay bị kẹt trên Windows) → tài liệu API: http://localhost:8000/docs
   **Worker** (mở case, chạy kịch bản Attack Lab), chạy ở cửa sổ dòng lệnh thứ hai: `.venv/Scripts/python -m worker.main`
   **Attack Lab** chỉ hiện khi `.env` có `DEMO_MODE=true` và chỉ tài khoản `admin` dùng được.

   **Demo reset** (trước buổi demo hoặc trước mỗi đợt đo): XÓA TOÀN BỘ dữ liệu rồi tạo lại sản phẩm, voucher, luật v1, nhân viên và các nhân vật Minh, Khang, Lan. Mật khẩu mới ghi vào `backend/.env.accounts`. Chỉ chạy được khi `DEMO_MODE=true`.
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

## Cấu trúc thư mục
| Thư mục | Nội dung |
|---|---|
| `backend/` | FastAPI: `app/core` (cấu hình, CSDL, lỗi), `app/modules` (các module nghiệp vụ), `migrations` (Alembic), `tests` |
| `frontend/` | React + Vite + TypeScript + Tailwind + shadcn/ui |
| `spike/risk-mock/` | Risk API giả từ spike, giữ làm mẫu hợp đồng tích hợp |
| `docs/` | Tài liệu dự án |

## Tài liệu dự án
| File | Nội dung |
|---|---|
| [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md) | Mục tiêu, phạm vi, hiện trạng |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Yêu cầu nghiệp vụ và chức năng |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Kiến trúc và các thành phần |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Các quyết định kỹ thuật (ADR) |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Kế hoạch, milestone |
| [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) | Kịch bản demo bảo vệ; phạm vi MVP suy ra từ đây |
| [docs/RULES_V0.md](docs/RULES_V0.md) | Bộ luật rủi ro v0: đặc trưng, luật, ma trận quyết định |
| [docs/ERD.md](docs/ERD.md) | Thiết kế CSDL: sơ đồ, index theo đặc trưng, ràng buộc, dữ liệu cá nhân |
| [docs/TEST_PLAN.md](docs/TEST_PLAN.md) | Chiến lược và kịch bản kiểm thử |
| [docs/PROGRESS_LOG.md](docs/PROGRESS_LOG.md) | Nhật ký tiến độ |
| [docs/reviews/](docs/reviews/) | Các bản tư vấn, phản biện (chưa phải quyết định) |
