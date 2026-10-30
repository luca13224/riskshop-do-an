---
name: ui-design-bar
description: Chuẩn chất lượng giao diện và quy trình tự kiểm tra cho Shop và Risk Console (React + Tailwind + shadcn/ui) của đồ án. Dùng khi thiết kế, dựng, chỉnh hoặc review bất kỳ màn hình nào, và trước khi đưa màn hình cho Luca xem.
---

# Chuẩn giao diện đồ án

Mục tiêu: giao diện trông như sản phẩm thật, và **mỗi chi tiết đẹp phục vụ câu chuyện demo**: phát hiện, giải thích, xử lý rủi ro.

## Nền tảng chung (cả shop lẫn Console)
- **Design tokens trước, màn hình sau:** chốt bảng màu (1 màu thương hiệu, 1 màu nhấn dùng tiết kiệm, thang xám trung tính, các màu ngữ nghĩa thành công / cảnh báo / nguy hiểm / thông tin), font, cỡ chữ, khoảng cách theo bội số 4 hoặc 8, bo góc, bóng đổ. Mọi màn hình dùng token, không dùng màu hay số tùy hứng.
- **Font:** một font tiêu đề có cá tính, một font nội dung dễ đọc, **hỗ trợ đầy đủ tiếng Việt có dấu** (kiểm tra thực tế các chữ ư, ơ, ặ, ễ). Dùng font mono cho mã, ID, số liệu.
- **Thương hiệu riêng:** tên, logo và màu của riêng đồ án. Tham khảo luồng mua hàng của các sàn lớn được, nhưng không sao chép giao diện hay nhận diện của họ.
- **Đủ trạng thái** cho mỗi khối dữ liệu: đang tải (skeleton), rỗng (có hướng dẫn), lỗi (nói chuyện gì xảy ra và làm gì tiếp), thành công.
- **Chuyển động:** nhẹ, có mục đích (xuất hiện mềm, chuyển trạng thái mượt). Tôn trọng `prefers-reduced-motion`.
- **Ngôn ngữ trên giao diện:** tiếng Việt tự nhiên, ngắn gọn. Thông điệp cho khách bị hạn chế phải **chung chung, lịch sự, không lộ luật**.

## Riêng Risk Console
- **Mật độ thông tin cao nhưng dễ quét:** bảng có lọc, sắp xếp, phân trang; số căn phải; thời gian hiển thị tương đối kèm giờ chính xác khi rê chuột.
- **Mức rủi ro không chỉ thể hiện bằng màu:** có nhãn chữ hoặc biểu tượng kèm theo (cho người mù màu và khi in báo cáo).
- **Màn hình chi tiết case là "màn hình ăn điểm":** điểm và quyết định, danh sách luật khớp kèm giá trị đặc trưng (vì sao khớp), tài khoản liên quan (cụm cùng thiết bị/địa chỉ), dòng thời gian sự kiện, nút xử lý bắt buộc nhập lý do.
- **Cảm giác thời gian thực khi demo:** case và cảnh báo mới xuất hiện không cần tải lại trang (polling ngắn là đủ cho MVP), có hiệu ứng nhấn nhẹ khi xuất hiện.
- Che dữ liệu cá nhân (IP, số điện thoại) theo vai trò.

## Riêng shop
- Chỉ làm các màn hình cần cho demo (ADR-003), nhưng làm thật kỹ: trang chủ, danh sách và chi tiết sản phẩm, giỏ hàng, checkout, lịch sử đơn.
- Dùng chung design tokens và component với Console; Shop mang cảm giác thương mại (nhiều ảnh, thoáng), Console mang cảm giác công cụ (dày dữ liệu).
- Ảnh sản phẩm cùng tỉ lệ, cùng phong cách. Nguồn ảnh phải có giấy phép rõ ràng.
- Thông báo kết quả từ Risk Service (bị gỡ voucher, chuyển trả trước, chờ xác minh) phải trông là một phần của sản phẩm, không phải lỗi hệ thống.

## Tự kiểm tra trước khi đưa Luca xem (bắt buộc)
1. Chụp màn hình bằng trình duyệt tích hợp ở 3 độ rộng: 375, 768, 1440 px. Tự xem: không tràn ngang, không vỡ chữ, không chồng chéo.
2. Đọc console trình duyệt: không có lỗi đỏ.
3. Bấm thử mọi nút và form trên màn hình, bao gồm trạng thái lỗi và trạng thái rỗng.
4. Độ tương phản chữ đạt tối thiểu WCAG AA. Mọi ô nhập có nhãn. Dùng được bằng bàn phím (Tab, Enter).
5. Rà chữ tiếng Việt: dấu hiển thị đúng, không lẫn câu tiếng Anh chưa dịch, không có từ sáo rỗng.
6. Báo cho Luca những gì đã kiểm tra, đã sửa, và những gì còn chưa kiểm tra được.
