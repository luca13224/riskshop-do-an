---
name: git-flow
description: Quy trình Git đơn giản cho đồ án một người, gồm tạo nhánh, commit, gộp nhánh, xem lịch sử và xử lý xung đột. Dùng khi bắt đầu một tính năng, khi commit, khi Luca hỏi về Git, hoặc khi gặp lỗi hay xung đột Git.
---

# Git cho đồ án

## Quy trình mỗi tính năng
1. Đứng ở `main`, nhánh này luôn chạy được.
2. Tạo nhánh: `feat/<tên-ngắn>` (tính năng), `fix/<tên>` (sửa lỗi), `docs/<tên>` (tài liệu), `spike/<tên>` (thử nghiệm có thể bỏ).
3. Commit nhỏ, mỗi commit một ý; thông điệp tiếng Việt nói **làm gì và vì sao**, ví dụ "Thêm luật R02 đếm tài khoản mới theo thiết bị".
4. Trước khi gộp: chạy test, xem lại diff.
5. Gộp về `main`, xóa nhánh.

## Quy tắc an toàn
- **Không commit:** `.env`, mật khẩu, `.venv/`, `node_modules/`, dữ liệu sinh ra. Trước khi commit, đọc danh sách file trong `git status`.
- Chỉ commit khi Luca đồng ý. Không dùng `push --force`, `reset --hard`, `--no-verify` nếu Luca chưa yêu cầu rõ ràng.
- Mỗi commit do Claude tạo kết thúc bằng dòng `Co-Authored-By` theo hướng dẫn của hệ thống.

## Giải thích cho Luca khi cần
- **commit** = chụp ảnh trạng thái code, có ghi chú.
- **branch** = bản nháp tách riêng; hỏng thì bỏ, `main` không sao.
- **merge** = đưa bản nháp đã ổn vào bản chính.
- **conflict** = hai bên cùng sửa một chỗ, Git không biết giữ bên nào. Mở file, tìm các dấu `<<<<<<<`, `=======`, `>>>>>>>`, giữ phần đúng, xóa các dấu, rồi commit.

## Mốc nên gắn tag
Gắn tag khi đạt mốc báo cáo GVHD, ví dụ `mvp-v1`, `demo-final`, để luôn quay lại được đúng phiên bản đã demo.
