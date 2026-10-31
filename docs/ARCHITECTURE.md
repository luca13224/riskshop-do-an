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
backend/simulator/                 persona, chạy mô phỏng qua API, đo kết quả (CSDL riêng riskshop_sim)
```

## 5. Còn phải thiết kế
- Kịch bản demo (định hướng phạm vi MVP).
- Danh sách luật v0 và đặc trưng cần tính.
- ERD và từ điển dữ liệu.
- Danh sách endpoint và màn hình.

## 6. Khả năng tích hợp: Risk Engine như một khối "cắm được" (2026-10-31)
> Mức trình bày (MVP): chưa tách thành dịch vụ riêng. Lộ trình tách ở mục 6.5. Bối cảnh: ADR-002 (phương án lai WooCommerce) đã dừng, ADR-003 giữ modular monolith.

### 6.1 Hai cổng vào, một cổng ra
- **Cổng vào A, yêu cầu chấm điểm:** bên bán gọi ở 3 thời điểm (`voucher_apply`, `payment_options`, `place_order`).
- **Cổng vào B, dữ liệu hành vi:** nơi engine lấy lịch sử để tính đặc trưng F01–F16. Hiện là adapter đọc thẳng CSDL RiskShop (`risk/features.py`, `risk/graph.py`); tương lai là adapter nhận sự kiện do hệ thống khác đẩy sang.
- **Cổng ra:** quyết định + danh sách hành động + lý do (luật khớp, điểm tin cậy). Case, khiếu nại, audit xử lý bên trong.

### 6.2 Hợp đồng tích hợp
| Thời điểm gọi | Bên bán gửi | Engine trả | Bên bán phải làm | Ở WooCommerce [cần xác minh khi cài] |
|---|---|---|---|---|
| Áp mã | tài khoản, thiết bị, IP, mã, giá trị giỏ | cho phép / gỡ mã | gỡ mã khỏi giỏ | hook kiểm tra coupon |
| Chọn thanh toán | như trên + phương thức | có / không cho COD | ẩn COD | bộ lọc phương thức thanh toán |
| Đặt hàng | như trên + địa chỉ, SĐT | cho phép / hạn chế / giữ chờ duyệt / chặn | đổi trạng thái đơn | trạng thái đơn "on-hold" |

### 6.3 Sự kiện tối thiểu một hệ thống khác phải cung cấp
| Sự kiện | Dùng cho |
|---|---|
| Đăng ký tài khoản | F01 tuổi tài khoản |
| Thiết bị, IP mỗi lần đăng nhập/thao tác | F02, F04, F13 |
| Lần thử mã giảm giá | F05 |
| Lượt xem sản phẩm | F06 |
| Đơn hàng kèm địa chỉ, SĐT, tiền giảm | F03, F11, F12, F14–F16 |
| Kết quả giao hàng | F07–F10 |

### 6.4 Bằng chứng trong code
- Module `risk` **không import** `cart`, `order`, `catalog`, `promotion`: bán hàng gọi vào engine, engine không gọi ngược.
- Chỗ còn dính: (1) đọc 6 bảng `users`, `user_devices`, `user_ips`, `addresses`, `orders`, `events` bằng SQL, gom trong `features.py` và `graph.py`; (2) dùng module `auth` để băm IP và ghi nhận thiết bị. Đây là lớp chuyển đổi duy nhất phải thay khi cắm vào hệ thống khác; luật, ma trận, Trust Score, case, khiếu nại giữ nguyên.

### 6.5 Giới hạn và lộ trình
- Nhiều bên bán dùng chung: tách dữ liệu theo từng bên, khóa API.
- Gọi qua mạng: độ trễ và lúc engine sập; đã có dự phòng fail-open/fail-closed (RULES_V0 mục 4).
- Quyền riêng tư: SĐT, IP phải băm trước khi gửi (IP đã băm sẵn).
- Lộ trình: API có phiên bản + khóa (`/api/risk/v1/evaluate`) → API nhận sự kiện (`/api/risk/v1/events`) → plugin WooCommerce.

