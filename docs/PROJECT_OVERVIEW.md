# PROJECT OVERVIEW

> Cập nhật lần cuối: 2026-10-30 · Trạng thái: **Khởi tạo — chưa chốt phạm vi**

## 1. Đề tài (dự kiến)
**Xây dựng hệ thống kiểm soát rủi ro và ngăn ngừa lạm dụng chính sách trên sàn thương mại điện tử.**

- Sinh viên: Luca — Hệ thống thông tin quản lý, Trường Đại học Thủy Lợi
- Giảng viên hướng dẫn: _(chưa có thông tin)_
- Thời hạn nộp / bảo vệ: _(chưa có thông tin)_

## 2. Problem Statement (bản nháp — cần xác minh)
_Đây là đề xuất của cố vấn, chưa dựa trên đề cương._

Các sàn thương mại điện tử dùng chính sách ưu đãi như voucher người mới hay hoàn tiền/trả hàng để thu hút khách. Một số người dùng lợi dụng chúng, ví dụ tạo nhiều tài khoản để nhận voucher nhiều lần hoặc lạm dụng hoàn tiền, gây thiệt hại cho sàn và người bán. Việc phát hiện thủ công tốn công, thiếu nhất quán và khó truy vết.

## 3. Mục tiêu (bản nháp)
1. Phát hiện và chấm điểm rủi ro cho một số hành vi lạm dụng chính sách đã chọn.
2. Ra quyết định có thể giải thích được (cho phép / xem xét thủ công / chặn).
3. Cung cấp công cụ để quản trị viên xem xét case, xử lý khiếu nại và ghi nhật ký kiểm toán (audit log).
4. Đánh giá hiệu quả bằng dữ liệu mô phỏng có kịch bản rõ ràng.

## 4. Phạm vi
| Mức | Nội dung | Trạng thái |
|---|---|---|
| MVP | Chọn 2–3 loại lạm dụng; Risk Engine dạng rule-based; màn hình quản trị viên | Đề xuất, chưa chốt |
| Recommended | Sàn mô phỏng tối giản để sinh sự kiện; dashboard thống kê; luồng khiếu nại | Đề xuất, chưa chốt |
| Advanced/Optional | Mô hình ML so sánh với rule; phân tích đồ thị liên kết tài khoản | Đề xuất, chưa chốt |

**Ngoài phạm vi (dự kiến):** thanh toán thật, dữ liệu cá nhân thật, triển khai production.

## 5. Hiện trạng
- [x] Thống nhất vai trò cố vấn và nguyên tắc làm việc
- [x] Tạo khung tài liệu dự án
- [ ] Thu thập đề cương, thời hạn, yêu cầu của giảng viên hướng dẫn
- [ ] Chốt các loại lạm dụng thuộc MVP

## 6. Rủi ro chính đã nhận diện
| Rủi ro | Ảnh hưởng | Hướng xử lý |
|---|---|---|
| Không có dữ liệu gian lận thật | Khó đánh giá hiệu quả | Sinh dữ liệu mô phỏng theo kịch bản, mô tả rõ giới hạn |
| Phạm vi quá rộng | Không kịp tiến độ | Giới hạn MVP ở 2–3 loại lạm dụng |
| Lạm dụng ML | Khó giải thích, khó bảo vệ | Rule-based làm lõi, ML chỉ là phần tùy chọn |
