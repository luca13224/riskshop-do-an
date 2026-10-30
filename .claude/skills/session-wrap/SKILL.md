---
name: session-wrap
description: Tổng kết một phiên làm việc đồ án và ghi vào docs/PROGRESS_LOG.md. Dùng khi Luca nói "tổng kết", "kết thúc phiên", "lưu tiến độ", hoặc khi kết thúc một phiên có quyết định hay thay đổi quan trọng.
---

# Tổng kết phiên

1. Xem lại những gì đã làm trong phiên: file đã tạo/sửa (`git status`, `git diff --stat`), quyết định đã chốt, vấn đề phát sinh.
2. Thêm một mục mới **ở đầu** `docs/PROGRESS_LOG.md` (ngay dưới dòng "Ghi mới nhất ở trên cùng."), dạng:

   ```
   ## YYYY-MM-DD — <tiêu đề ngắn của phiên>
   **Đã hoàn thành**
   **Quyết định đã chốt** (chỉ những gì Luca đã đồng ý; ghi số ADR nếu có)
   **Đề xuất chưa chốt**
   **Vấn đề còn mở**
   **Bước tiếp theo**
   ```

3. Chỉ ghi sự thật đã xảy ra. Không ghi kết quả test hay số liệu chưa thực sự chạy.
4. Nếu trạng thái dự án thay đổi, cập nhật mục "Hiện trạng" trong `docs/PROJECT_OVERVIEW.md` và "Việc tiếp theo" trong `docs/ROADMAP.md`.
5. Đưa cho Luca bản tóm tắt ngắn trong chat, rồi hỏi Luca có muốn commit không. Không tự commit nếu Luca chưa đồng ý.
