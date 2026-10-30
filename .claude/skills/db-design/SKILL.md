---
name: db-design
description: Chuẩn thiết kế cơ sở dữ liệu MariaDB của đồ án, gồm ERD, bảng, khóa, index, migration Alembic và từ điển dữ liệu. Dùng khi vẽ hoặc sửa ERD, thêm hoặc đổi bảng và cột, viết truy vấn cần index, hoặc khi truy vấn chậm.
---

# Thiết kế CSDL (MariaDB, InnoDB)

## Quy ước bảng và cột
- Tên bảng: số nhiều, `snake_case` (`orders`, `risk_decisions`). Khóa chính `id` dạng `BIGINT` tự tăng; ID lộ ra ngoài (mã đơn, `decision_id`) dùng UUID hoặc mã riêng.
- Mọi bảng có `created_at` (UTC). Bảng sửa được có thêm `updated_at`.
- Charset `utf8mb4`, collation `utf8mb4_unicode_ci` (tiếng Việt và emoji).
- Tiền: `BIGINT` theo đồng. Không dùng `FLOAT` hay `DOUBLE`.
- Trạng thái: chuỗi ngắn có ràng buộc ở tầng ứng dụng (Enum Python); liệt kê giá trị hợp lệ trong từ điển dữ liệu.
- Dữ liệu linh hoạt (payload sự kiện, `features_snapshot`): cột `JSON`.

## Ràng buộc là hàng rào cuối
- Khóa ngoại cho mọi quan hệ.
- `UNIQUE` cho bất biến nghiệp vụ, ví dụ mỗi tài khoản chỉ dùng voucher tân thủ 1 lần: `UNIQUE(voucher_id, user_id)`; idempotency: `UNIQUE(idempotency_key)`.
- Bảng **chỉ ghi thêm** (`risk_decisions`, `audit_logs`, `events`): ứng dụng không có code `UPDATE` hay `DELETE` lên chúng.

## Index theo truy vấn thật
- Mỗi đặc trưng trong `docs/RULES_V0.md` tương ứng một truy vấn đếm theo cửa sổ thời gian; tạo index ghép theo **cột lọc + thời gian**, ví dụ `(device_id, created_at)`, `(address_hash, created_at)`, `(ip, created_at)`.
- Trước khi kết luận "cần Redis", đo truy vấn bằng `EXPLAIN` và thời gian thực tế.

## Migration (Alembic)
- Mỗi thay đổi một migration, có `downgrade`.
- Không sửa migration đã chạy; muốn đổi thì tạo migration mới.
- Dữ liệu demo đi qua script seed hoặc `demo reset`, không nằm trong migration.

## Tài liệu
- ERD viết bằng Mermaid trong `docs/` để Git theo dõi được; kèm **từ điển dữ liệu**: bảng, cột, kiểu, ý nghĩa, ràng buộc, ví dụ giá trị.
- Mỗi bảng ghi rõ **module nào sở hữu**: chỉ module đó được ghi vào bảng.

## Bảo vệ dữ liệu cá nhân
- Chỉ lưu những gì luật rủi ro hoặc nghiệp vụ cần. IP và địa chỉ dùng cho so khớp thì lưu thêm bản **băm** để đếm; Console hiển thị dạng che một phần.
