# Bản đồ mã nguồn

> Mỗi thư mục / file code nằm ở đâu, làm gì. Tên file code giữ tiếng Anh theo quy ước chung của FastAPI và React (dễ đọc với người ngoài, không phải sửa import); vai trò ghi bằng tiếng Việt ở đây. Cập nhật file này khi thêm, xóa hoặc chuyển file.

## 1. Tổng thể
| Thư mục | Vai trò |
|---|---|
| `backend/` | Máy chủ API (FastAPI, Python 3.11) + Risk Engine + worker + bộ mô phỏng |
| `frontend/` | Giao diện React + TypeScript: cửa hàng (Shop) và Risk Console |
| `docs/` | Tài liệu dự án và kết quả thực nghiệm (xem mục 5) |
| `.claude/skills/` | Hướng dẫn quy trình cho Claude trong dự án (ADR, tổng kết phiên, chuẩn module...) |

## 2. Backend: `backend/app/`
Mỗi module nghiệp vụ trong `app/modules/<tên>/` theo cùng một khuôn:

| File | Vai trò |
|---|---|
| `models.py` | Bảng CSDL (SQLAlchemy) |
| `schemas.py` | Dữ liệu vào / ra của API (Pydantic), kiểm tra đầu vào |
| `service.py` | Nghiệp vụ chính; router chỉ gọi vào đây |
| `router.py` | Đường dẫn API (endpoint), phân quyền bằng `require_roles` |

### 2.1. Phần dùng chung `app/core/`
| File | Vai trò |
|---|---|
| `config.py` | Đọc cấu hình từ `.env` (CSDL, khóa bí mật, mật khẩu demo) |
| `db.py` | Kết nối CSDL, phiên làm việc cho mỗi request |
| `errors.py` | Định dạng lỗi chung `{error: {code, message, request_id}}` |
| `jobs.py` | Hàng đợi việc nền trong CSDL (ví dụ mở case), worker lấy việc ra chạy |
| `privacy.py` | Che email, SĐT trước khi trả về Console |
| `search.py` | Tìm kiếm an toàn với `LIKE` (thoát ký tự đặc biệt) |
| `time.py` | Giờ UTC thống nhất cho toàn hệ thống |
| `health.py` | API kiểm tra hệ thống sống / CSDL kết nối được |
| `../main.py` | Tạo ứng dụng FastAPI, gắn các router |
| `../models.py` | Gom mọi bảng để Alembic tạo migration |

### 2.2. Các module nghiệp vụ `app/modules/`
| Module | Vai trò |
|---|---|
| `auth/` | Đăng ký, đăng nhập, phiên, vai trò; ghi thiết bị / IP của khách (`security.py`: băm mật khẩu Argon2; `deps.py`: kiểm tra đăng nhập và quyền; `cli.py`: tạo tài khoản nhân viên) |
| `catalog/` | Sản phẩm, danh mục, tồn kho (`seed.py`: dữ liệu sản phẩm mẫu; `seo.py`: sitemap, robots.txt) |
| `cart/` | Giỏ hàng, áp mã giảm giá (gọi Risk Engine ở bước áp mã) |
| `promotion/` | Mã giảm giá, túi voucher, điều kiện nghiệp vụ của mã (`seed.py`: NGUOIMOI, GIAM10) |
| `order/` | Đặt hàng, địa chỉ, chuẩn hóa địa chỉ, cập nhật trạng thái giao hàng (gọi Risk Engine ở bước đặt hàng) |
| `events/` | Ghi sự kiện hành vi (xem sản phẩm, thử mã, đăng ký) làm dữ liệu cho đặc trưng |
| `risk/` | **Risk Engine** (xem 2.3) |
| `cases/` | Case cho analyst: mở, nhận xử lý, kết luận |
| `appeals/` | Khiếu nại của khách, duyệt khiếu nại, miễn trừ |
| `reports/` | Số liệu Tổng quan và Báo cáo của Console |
| `audit/` | Nhật ký thao tác của nhân viên (ai làm gì, lúc nào, trước / sau) |
| `lab/` | Attack Lab (`scenarios.py`: kịch bản tấn công mẫu) và demo reset (`reset.py`) |
| `simulation/` | Bảng lưu lần chạy mô phỏng và nhãn thật (Risk Engine không bao giờ đọc) |

### 2.3. Risk Engine `app/modules/risk/`
| File | Vai trò |
|---|---|
| `service.py` | Luồng chấm điểm: tính đặc trưng → chạy luật → điểm tin cậy → ma trận quyết định → khóa kẻ né lệnh khóa; ghi quyết định; bộ nhớ đệm luật (ADR-017) |
| `features.py` | Tính đặc trưng F01–F18 bằng SQL chỉ đọc (gồm cụm liên kết F18) |
| `rules.py` | Các LOẠI luật (ngưỡng đếm, ngưỡng tỷ lệ, kết hợp) và cách ghép câu giải thích |
| `seed.py` | Bộ luật R01–R18 và ngưỡng quyết định; tạo phiên bản mới khi nội dung đổi |
| `rules_admin.py` | Sửa luật trên Console: chỉ đổi con số, tạo phiên bản mới, ghi audit |
| `backtest.py` | Chạy thử tham số luật trên quyết định cũ (FR-43) |
| `graph.py` | Đồ thị liên kết tài khoản – thiết bị – IP – địa chỉ cho Console |
| `models.py` / `schemas.py` / `router.py` | Bảng luật, quyết định, khóa tài khoản; API Console |

### 2.4. Ngoài `app/`
| Thư mục / file | Vai trò |
|---|---|
| `migrations/` | Lịch sử thay đổi cấu trúc CSDL (Alembic) |
| `worker/main.py` | Tiến trình nền chạy việc trong hàng đợi |
| `tests/` | Test tự động (pytest), chạy trên CSDL test riêng |
| `simulator/` | Bộ mô phỏng: `personas.py` (nhóm khách giả lập, bộ dữ liệu dev / test v1–v5), `runner.py` (chạy qua API thật, chấm kết quả), `baselines.py` (so với cách làm đơn giản), `report.py` (viết báo cáo), `trust_report.py` (phân bố điểm tin cậy), `history.py` (tạo lịch sử 14 ngày cho CSDL demo) |
| `scripts/load_test.py` | Đo độ trễ khi nhiều người đặt hàng cùng lúc (O5) |
| `scripts/audit_check.py` | Kiểm tra tính giải thích được và audit của quyết định (O6) |
| `scripts/demo_attack.py` | Gửi tấn công mẫu cho buổi demo (cảnh 5c, 5e) |
| `scripts/check_links.py` | Tìm link hỏng trong tài liệu sau khi đổi tên / chuyển chỗ file |
| `ruff.toml` | Cấu hình ruff: tìm import / biến thừa, tên chưa định nghĩa (`.venv/Scripts/python -m ruff check .`) |

## 3. Frontend: `frontend/src/`
| Thư mục / file | Vai trò |
|---|---|
| `main.tsx`, `App.tsx` | Khởi động ứng dụng, bản đồ đường dẫn của Shop và Console |
| `index.css` | Màu sắc, kiểu chữ dùng chung (Tailwind) |
| `lib/api/` | Gọi API theo từng module backend (`client.ts`: hàm gọi chung và định dạng lỗi) |
| `lib/` | Tiện ích: `device.ts` (mã thiết bị gửi kèm request), `format.ts` (tiền, ngày giờ), `seo.tsx`, `utils.ts` |
| `components/` | Thành phần dùng chung cả hai phía; `components/ui/` là thành phần shadcn/ui |
| `shop/` | Cửa hàng: `ShopLayout.tsx` (khung trang), `pages/` (trang chủ, danh mục, sản phẩm, giỏ, thanh toán, đơn hàng, khiếu nại, đăng nhập, đăng ký), `components/` (thẻ sản phẩm, header, footer, xem nhanh...) |
| `console/` | Risk Console: `ConsoleLayout.tsx` (menu theo vai trò), `RequireStaff.tsx` / `RequireRole.tsx` (chặn theo vai trò), `pages/` (Tổng quan, Live Monitor, Báo cáo, Case, Khiếu nại, Đơn hàng, Luật, Attack Lab, Audit Log), `components/` (biểu đồ, đồ thị liên kết, chạy thử luật...) |
| `../public/` | Ảnh sản phẩm, danh mục (tên file theo mã SKU) |

## 4. Luồng chính, đi theo file
- **Áp mã giảm giá:** `cart/router.py` → `cart/service.py` → `promotion/service.py` (điều kiện nghiệp vụ) → `risk/service.py` (`evaluate`) → `risk/features.py` + `risk/rules.py`.
- **Đặt hàng:** `order/router.py` → `order/service.py` (`checkout`: giữ tồn kho, lưu địa chỉ, chấm điểm, tạo đơn) → `risk/service.py` → `core/jobs.py` (mở case) → `worker/main.py`.
- **Xử lý case:** Console `console/pages/CaseDetailPage.tsx` → `lib/api/cases.ts` → `cases/router.py` → `cases/service.py` → `audit/service.py`.

## 5. Tài liệu `docs/`
| File / thư mục | Nội dung |
|---|---|
| `TONG_QUAN.md` | Mục tiêu, phạm vi, mục tiêu đo O1–O9 |
| `YEU_CAU.md` | Yêu cầu chức năng / phi chức năng, quy tắc nghiệp vụ, use case |
| `KIEN_TRUC.md` | Kiến trúc và các thành phần |
| `QUYET_DINH.md` | Các quyết định kỹ thuật (ADR) |
| `LO_TRINH.md` | Kế hoạch, milestone |
| `BO_LUAT_RUI_RO.md` | Đặc trưng, luật, ma trận quyết định |
| `ERD.md` | Thiết kế CSDL |
| `KIEM_THU.md` | Kiểm thử và kết quả thực nghiệm (đọc kèm `thuc_nghiem/`) |
| `KICH_BAN_DEMO.md` | Kịch bản demo bảo vệ |
| `NHAT_KY_TIEN_DO.md` | Nhật ký tiến độ từng phiên |
| `BAO_CAO_DAN_Y.md` | Dàn ý quyển báo cáo |
| `BAN_DO_MA_NGUON.md` | File này |
| `thuc_nghiem/` | Kết quả mô phỏng, đo tải, audit ([mục lục](thuc_nghiem/README.md)) |
| `tu_van/` | Bản tư vấn, rà soát, thiết kế (chưa phải quyết định) |
| `so_do/` | Sơ đồ kiến trúc và luồng đặt hàng (HTML) |
| `hinh_anh/` | Mô tả nguồn ảnh sản phẩm |
| `bao-cao/` | Bản báo cáo nộp trường (chỉ trên máy, không đưa lên git) |
