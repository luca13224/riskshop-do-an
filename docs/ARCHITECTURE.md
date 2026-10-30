# ARCHITECTURE

> Trạng thái: **Hướng kiến trúc đã chốt (ADR-003)**. Chi tiết module, ERD và API sẽ bổ sung trong giai đoạn thiết kế.

## 1. Tổng quan: modular monolith

```
┌──────────────────────── Frontend: một ứng dụng React ────────────────────────┐
│  /            Shop (khách hàng)          /console   Risk Console (nhân viên)  │
└───────────────────────────────┬───────────────────────────────────────────────┘
                                │ REST API (JSON) + SSE (cảnh báo realtime)
┌───────────────────────────────▼───────── Backend: FastAPI ────────────────────┐
│ auth  catalog  cart  promotion  order  fulfillment  events                    │
│ risk  cases  rules  reports  audit                                            │
└──────────────┬──────────────────────────────────────────────┬─────────────────┘
        ┌──────▼──────┐                               ┌───────▼───────┐
        │  MariaDB    │◄──── Worker (bảng jobs) ───────│ Attack        │
        └─────────────┘                               │ Simulator     │
                                                      └───────────────┘
```

## 2. Nguyên tắc
- Backend là **một ứng dụng**, chia **module theo nghiệp vụ**. Module gọi nhau qua hàm công khai trong `service.py`, không truy cập trực tiếp bảng của module khác.
- Module `risk` **không phụ thuộc** `order`: nhận một ngữ cảnh đánh giá, trả về `decision`, `actions`, `reason_codes`. Hợp đồng ban đầu lấy từ Risk mock của spike (`spike/risk-mock/main.py`).
- **Quyết định đồng bộ** tại hai điểm kiểm soát: áp voucher và checkout. **Phân tích bất đồng bộ** (cập nhật hồ sơ rủi ro, mở case) do worker xử lý và không đảo ngược quyết định đã trả.
- Quyết định rủi ro được lưu **bất biến**, kèm snapshot đặc trưng và phiên bản luật; override tạo quyết định mới.
- Attack Simulator gọi **đúng API** mà shop dùng.

## 3. Thành phần và công nghệ
| Thành phần | Công nghệ |
|---|---|
| Frontend | React + Vite + TypeScript, Tailwind CSS + shadcn/ui, TanStack Query, TanStack Table, React Hook Form + Zod, Recharts |
| Backend | FastAPI, SQLAlchemy 2, Alembic, Pydantic, pytest |
| CSDL | MariaDB (XAMPP, `D:\xampp`), chỉ nhận kết nối từ localhost |
| Tác vụ nền | Bảng `jobs` + worker Python |
| Realtime | Server-Sent Events |
| Mô phỏng | Python CLI; Playwright (Recommended) |

## 4. Cấu trúc thư mục (dự kiến)
```
backend/app/core/                  cấu hình, DB, bảo mật, lỗi chung
backend/app/modules/<module>/      models.py, schemas.py, service.py, router.py
backend/worker/                    tiến trình xử lý job
backend/migrations/                Alembic
backend/tests/
frontend/src/shop/                 trang khách hàng
frontend/src/console/              trang nhân viên rủi ro
frontend/src/components/ui/        component shadcn
frontend/src/lib/                  gọi API, tiện ích
simulator/                         persona, kịch bản tấn công, đo kết quả
```

## 5. Còn phải thiết kế
- Kịch bản demo (định hướng phạm vi MVP).
- Danh sách luật v0 và đặc trưng cần tính.
- ERD và từ điển dữ liệu.
- Danh sách endpoint và màn hình.
