---
name: adr
description: Ghi một Architecture Decision Record (ADR) vào docs/DECISIONS.md khi Luca chốt hoặc đề xuất một quyết định kỹ thuật, phạm vi hay nghiệp vụ quan trọng. Dùng khi Luca nói "ghi quyết định", "chốt", "ADR", hoặc khi một quyết định ảnh hưởng kiến trúc, CSDL, công nghệ, phạm vi hay mô hình rủi ro.
---

# Ghi ADR

1. Đọc `docs/DECISIONS.md` để lấy số ADR lớn nhất hiện có; ADR mới = số đó + 1, định dạng `ADR-XXX` (3 chữ số).
2. Xác nhận với Luca trạng thái: `Proposed` (đang cân nhắc) hay `Accepted` (Luca đã đồng ý rõ ràng). **Không bao giờ ghi `Accepted` nếu Luca chưa nói đồng ý.**
3. Thêm ADR vào cuối file theo đúng mẫu có trong file:
   - Ngày (YYYY-MM-DD), Trạng thái
   - Bối cảnh: vấn đề cần quyết định, ràng buộc
   - Các phương án: ít nhất 2, mỗi phương án có ưu/nhược
   - Quyết định
   - Lý do: gắn với mục tiêu đồ án (khả thi, kiểm chứng được, bảo vệ được)
   - Hệ quả / rủi ro: điều gì trở nên dễ hơn hoặc khó hơn, việc cần làm tiếp
4. Nếu ADR mới thay thế ADR cũ: **không xóa ADR cũ**, sửa trạng thái ADR cũ thành `Superseded by ADR-YYY`.
5. Nếu quyết định ảnh hưởng tài liệu khác (ARCHITECTURE, REQUIREMENTS, ROADMAP, PROJECT_OVERVIEW), cập nhật luôn các chỗ liên quan hoặc liệt kê cho Luca những chỗ cần sửa.
6. Viết bằng tiếng Việt, ngắn gọn; ghi rõ phần nào là giả định chưa kiểm chứng.
