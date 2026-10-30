---
name: debug-helper
description: Gỡ lỗi có phương pháp cho đồ án (backend FastAPI, frontend React, MariaDB, môi trường Windows/XAMPP). Dùng khi có lỗi, test fail, app không chạy, kết quả sai, hoặc Luca dán thông báo lỗi.
---

# Gỡ lỗi có phương pháp

1. **Tái hiện:** lỗi xảy ra khi làm gì, lần nào cũng bị hay thỉnh thoảng? Ghi lại lệnh hoặc thao tác tái hiện.
2. **Đọc lỗi cho đúng:** tìm dòng quan trọng nhất (loại lỗi + file + dòng code của dự án, không phải dòng trong thư viện). Giải thích cho Luca lỗi này **nghĩa là gì** bằng lời thường.
3. **Khoanh vùng:** lỗi ở frontend, API, service, CSDL hay môi trường? Kiểm tra từng lớp: tab Network của trình duyệt → log backend → truy vấn CSDL.
4. **Giả thuyết → kiểm chứng:** nêu 1–2 nguyên nhân khả dĩ nhất, kiểm chứng từng cái bằng một bước nhỏ (in giá trị, chạy một test, chạy truy vấn). Không sửa mò nhiều chỗ cùng lúc.
5. **Sửa tận gốc,** không che lỗi (không `try/except: pass`, không tắt test).
6. **Khóa lỗi lại:** viết một test tái hiện lỗi, test fail trước khi sửa và pass sau khi sửa.
7. **Kể lại ngắn gọn cho Luca:** nguyên nhân, cách sửa, cách lần sau tự phát hiện sớm.

## Lỗi môi trường hay gặp trên máy này
- MariaDB chưa chạy: mở `D:\xampp\xampp-control.exe`, bấm Start ở MySQL.
- Cổng bị chiếm: kiểm tra cổng 8000 (backend) và 5173 (Vite).
- Python sai môi trường: kích hoạt đúng `.venv` của thư mục `backend/`.
- Ổ C gần đầy: cache và cài đặt để ở ổ D.
- Ký tự xuống dòng LF/CRLF: cảnh báo của Git, không phải lỗi.
- `uvicorn --reload` trên Windows hay kẹt ở dòng "Reloading..." (kể cả khi dùng watchfiles), nhất là khi tạo nhiều file mới liên tiếp: API mới trả 404. Quy ước: khi Claude chạy backend thì **không dùng `--reload`**, mà dừng rồi chạy lại sau mỗi đợt sửa backend.
- In tiếng Việt từ script Python ra cửa sổ dòng lệnh Windows bị `UnicodeEncodeError`: gọi `sys.stdout.reconfigure(encoding="utf-8")` ở đầu script.
- Cài thêm gói npm khi `npm run dev` đang chạy: trình duyệt có thể báo "Invalid hook call" hoặc "Outdated Optimize Dep". Tải lại trang (hoặc khởi động lại dev server) là hết.

## Không được làm
Không chạy lệnh tắt hàng loạt tiến trình (ví dụ tắt mọi `python.exe`). Chỉ dừng đúng tiến trình mình đã bật.
