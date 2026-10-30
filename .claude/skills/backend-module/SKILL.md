---
name: backend-module
description: Chuẩn tạo và sửa một module backend FastAPI của đồ án (auth, catalog, cart, promotion, order, fulfillment, events, risk, cases, rules, reports, audit). Dùng khi thêm endpoint, model, migration, service hoặc test ở thư mục backend/.
---

# Module backend FastAPI

## Cấu trúc bắt buộc của mỗi module (`backend/app/modules/<tên>/`)
| File | Chứa gì | Không được chứa |
|---|---|---|
| `models.py` | Bảng SQLAlchemy 2 (kiểu `Mapped[...]`) | Logic nghiệp vụ |
| `schemas.py` | Pydantic: dữ liệu vào/ra API | Truy vấn CSDL |
| `service.py` | Logic nghiệp vụ, transaction; **hàm công khai cho module khác gọi** | Đối tượng Request/Response của HTTP |
| `router.py` | Endpoint: nhận request → gọi service → trả schema | Logic nghiệp vụ, truy vấn trực tiếp |

- Module A cần dữ liệu của module B: gọi hàm trong `B/service.py`. **Không import model của B để tự truy vấn.**
- Module `risk` **không import** `order`, `cart`, `promotion`. Bên gọi phải dựng sẵn ngữ cảnh đánh giá rồi truyền vào (ADR-003).

## Quy ước
- Lỗi nghiệp vụ: raise exception riêng của dự án (định nghĩa ở `app/core/errors.py`). Handler chung trả `{"error": {"code", "message", "request_id"}}`. Không trả stack trace cho client.
- Phân quyền: dùng dependency kiểm tra vai trò ở **từng endpoint**. Frontend ẩn nút chỉ là phần giao diện.
- Tiền tệ: VND lưu bằng **số nguyên** (`BigInteger`), không dùng float.
- Thời gian: lưu **UTC**; chỉ đổi sang giờ Việt Nam khi hiển thị.
- Mọi thay đổi cấu trúc CSDL đi qua **Alembic migration**. Không sửa bảng bằng tay trong phpMyAdmin.
- Secret và chuỗi kết nối CSDL lấy từ biến môi trường (`.env`, không commit). Có `.env.example` mẫu.
- Luồng quan trọng (áp voucher, checkout): một transaction; dùng ràng buộc `UNIQUE` hoặc `SELECT ... FOR UPDATE` chống race condition; checkout có `Idempotency-Key`.
- Log dạng có cấu trúc, kèm `request_id`. **Không log** mật khẩu, token, địa chỉ hay số điện thoại đầy đủ.

## Test (pytest)
- `service.py`: test logic, gồm trường hợp lỗi và trường hợp biên.
- `router.py`: test API, gồm mã HTTP, định dạng lỗi, và phân quyền (vai trò sai bị 403).
- Luồng có race condition: có ít nhất một test gọi đồng thời (ví dụ 2 request dùng voucher còn 1 lượt → đúng 1 thành công).

## Khi làm cùng Luca
Đề xuất chữ ký hàm và schema trước, Luca đồng ý rồi mới viết. Sau khi viết, dùng skill `explain-code` để đi qua luồng chạy.
