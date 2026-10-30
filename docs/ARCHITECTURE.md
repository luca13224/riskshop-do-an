# ARCHITECTURE

> Trạng thái: **Chưa thiết kế** — thiết kế sau khi có REQUIREMENTS.

## Định hướng sơ bộ (đề xuất, chưa chốt)
- Sàn TMĐT mô phỏng tối giản → phát sinh sự kiện (đăng ký, đặt hàng, dùng voucher, yêu cầu hoàn tiền).
- Risk Engine: nhận sự kiện → tính đặc trưng → áp rule → điểm rủi ro + lý do → quyết định.
- Admin Console: hàng đợi case, xem lý do, xử lý, khiếu nại, audit log.
- Ưu tiên kiến trúc monolith có module rõ ràng; không dùng microservices/Kubernetes cho MVP.

## Thành phần
_(Chưa có)_

## Công nghệ
_(Chưa chọn — mỗi lựa chọn sẽ ghi vào DECISIONS.md)_
