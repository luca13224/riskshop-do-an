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
   ```
   Chạy: `.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000` → tài liệu API: http://localhost:8000/docs
   Test: `.venv/Scripts/python -m pytest -q`
3. **Frontend** (lần đầu `npm install`): `cd frontend && npm run dev` → http://localhost:5173

Trang chủ hiện "Backend và cơ sở dữ liệu đã sẵn sàng" là cả ba phần đã nối với nhau.

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
