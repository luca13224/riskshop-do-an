# Rà soát toàn bộ sản phẩm (2026-11-05)

> Tư vấn, chưa phải quyết định. Dữ liệu: CSDL demo sau *demo reset* + lịch sử 14 ngày, tài khoản admin1–3 / user1–3.

## Cách rà
- Script điều khiển Edge chạy ẩn qua DevTools: 74 lượt chụp (khách chưa đăng nhập, 3 khách, Admin, Analyst) ở 1440 / 768 / 375 px. Mỗi trang ghi lỗi JavaScript, lỗi console, request ≥ 400, tràn ngang, trang bị treo.
- Chạy thật trên server đang chạy: cảnh demo 5c (cố đặt COD lặp → khóa) và 5e (khóa vô thời hạn → tài khoản mới né khóa).
- Đã có sẵn: 194 test backend.

## Không có lỗi
- Không có lỗi JavaScript; không trang nào tràn ngang ở cả 3 độ rộng.
- Lần rà đầu bị treo ở trang Đơn hàng của Khang; lần này (có giới hạn thời gian) **không tái hiện**.
- Cảnh 5c: lần đặt thứ 4 bị chặn và khóa 24 giờ. Cảnh 5e: tài khoản mới chung máy bị khóa ngay ở lần thử mã thứ 2.
- Footer "rèm" ở trang ngắn: ảnh chụp cả trang trông như bị đè, kiểm lại trong khung nhìn thật thì hiển thị đúng (lỗi do cách chụp).

## Lỗi và việc cần sửa

| # | Mức | Vấn đề | Ở đâu | Đề xuất |
|---|---|---|---|---|
| 1 | P1 | Analyst thấy mục Audit Log và Attack Lab trong menu; bấm vào là trang gần trống và 3 lần lỗi 403 (tự gọi lại) | Console, menu trái | Ẩn mục menu theo vai trò; không gọi lại khi lỗi 401/403 |
| 2 | P1 | Câu báo khi COD bị tắt khó hiểu: "Đơn hàng này hỗ trợ thanh toán trước." | Shop, lúc chọn thanh toán / đặt hàng | Viết lại: "Đơn này chưa dùng được thanh toán khi nhận hàng. Bạn chọn trả trước để tiếp tục." |
| 3 | P1 | Bảng Audit Log và bảng Đơn hàng của Console ở 375 px: chữ bị bẻ từng từ, đọc không được | Console, điện thoại | Ẩn cột phụ trên điện thoại hoặc chuyển sang dạng thẻ |
| 4 | P2 | Đã đăng nhập vẫn vào được `/login`, `/register` và thấy form | Shop | Chuyển về trang chủ (khách) hoặc Console (nhân viên) |
| 5 | P2 | Lúc tải trang, header nháy "Đăng nhập / Đăng ký" trước khi biết đã đăng nhập | Shop, header | Hiện khung chờ trong lúc kiểm tra phiên |
| 6 | P2 | Chưa đăng nhập mở `/orders`: gọi API đơn hàng trước rồi mới chuyển sang đăng nhập (401 thừa) | Shop | Chỉ gọi API khi đã có phiên |
| 7 | P2 | Còn từ cũ "voucher tân thủ" | Trang đăng ký; tên luật R01 | Đổi thành "mã người mới" (R01 đổi tên qua seed, tạo phiên bản luật mới) |
| 8 | P2 | Trang Đơn hàng của khách không phân trang (khách 30 đơn: danh sách rất dài) | Shop, `/orders` | Phân trang hoặc "Xem thêm" |
| 9 | P2 | Trang Báo cáo: khối "Nguyên nhân rủi ro" trùng ý với bảng "Hiệu quả từng luật" | Console, Báo cáo | Gộp khi tinh gọn (giai đoạn 2) |
| 10 | P3 | Lỗi 401 `/api/auth/me` trên console trình duyệt khi chưa đăng nhập | Shop | Bình thường (kiểm tra phiên); có thể đổi API trả 200 + `null` nếu muốn sạch console |
| 11 | P3 | Nút "Dùng" trong túi voucher được trình đọc màn hình nhận là chữ thường, không phải nút | Shop, giỏ hàng | Kiểm tra lại cấu trúc nút (truy cập bằng bàn phím) |

## Thứ tự đề xuất
1. P1 (1–3) trước buổi tổng duyệt demo.
2. P2 (4–8) cùng đợt, mỗi lỗi một commit, có test nếu là backend.
3. #9 để giai đoạn tinh gọn.

## Cập nhật 2026-11-05: đã sửa việc 1–8
- 1: menu ẩn Attack Lab (chỉ Admin) và Audit Log (Risk Manager, Admin) theo vai trò; gõ thẳng URL thì hiện trang "không thuộc quyền"; TanStack Query không gọi lại khi lỗi 4xx.
- 2: câu báo tắt COD viết lại như đề xuất.
- 3: bảng Audit Log và Đơn hàng (Console) gom cột phụ vào cột đầu trên màn hẹp.
- 4: đã đăng nhập mở `/login`, `/register` thì chuyển về trang chủ hoặc Console.
- 5: header hiện khung chờ trong lúc kiểm tra phiên.
- 6: đơn hàng, khiếu nại của khách chỉ gọi API khi đã là khách đăng nhập.
- 7: "voucher tân thủ" thành "mã người mới" (R01 có phiên bản luật mới; lý do của quyết định cũ giữ nguyên để truy vết).
- 8: trang Đơn hàng của khách hiện 10 đơn, nút "Xem thêm".
- Kiểm chứng: 195 test backend qua; chụp lại bằng Edge chạy ẩn (Analyst, Admin, khách, chưa đăng nhập); chỉ còn 401 `/api/auth/me` (việc 10, P3).
