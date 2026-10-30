# ROADMAP

> Hạn nộp: khoảng cuối tháng 12/2026 (còn ~2 tháng tính từ 30/10/2026). **Mục tiêu nội bộ: hoàn thiện sản phẩm trước 30/11/2026**, tháng 12 để dự phòng và chỉnh báo cáo theo góp ý của GVHD.

## Kế hoạch 4 tuần (ADR-005)
| Tuần | Thời gian | Nội dung | Xong khi |
|---|---|---|---|
| 1 | 31/10 – 06/11 | Mặt tiền shop: danh mục đồ công nghệ (đã xong), ảnh sản phẩm, tông sáng, thẻ sản phẩm kiểu Neotek, xem nhanh (quick view), trang chi tiết có bảng thông số | Trang chủ, danh mục, chi tiết đều có ảnh thật; đẹp ở 375 px và 1440 px |
| 2 | 07/11 – 13/11 | Banner rạp chiếu phim: vòng danh mục 3D, màn hình chiếu chính, "đèn rạp bật sáng" khi cuộn, nút glow, hiệu ứng vào trang, giảm chuyển động | Mở trang chủ là có "wow", vẫn bấm được bằng bàn phím và trên điện thoại |
| 3 | 14/11 – 20/11 | Dashboard tổng quan (shop + rủi ro + việc cần xử lý) và khiếu nại (appeals) | Quản lý trả lời được 3 câu hỏi trong một màn hình; khách bị chặn nhầm có đường khiếu nại |
| 4 | 21/11 – 30/11 | Hoàn thiện, demo reset trên dữ liệu chuẩn, tập 9 cảnh demo, bản nháp báo cáo và slide | Chạy trọn kịch bản demo không lỗi |

| Giai đoạn | Nội dung chính | Đầu ra | Thời gian |
|---|---|---|---|
| 0. Khởi động | Thu thập đề cương, yêu cầu GVHD, chốt phạm vi | PROJECT_OVERVIEW hoàn chỉnh | _?_ |
| 1. Phân tích | Stakeholder, quy trình nghiệp vụ, yêu cầu, use case | REQUIREMENTS | _?_ |
| 2. Thiết kế | Kiến trúc, ERD, API, rule, UI | ARCHITECTURE, ADR | _?_ |
| 3. Dữ liệu mô phỏng | Kịch bản hành vi hợp lệ & lạm dụng | Bộ sinh dữ liệu | _?_ |
| 4. Xây dựng MVP | Risk Engine, Admin Console, sàn mô phỏng | Mã nguồn chạy được | _?_ |
| 5. Kiểm thử & đánh giá | Test case, đo precision/recall trên dữ liệu mô phỏng | TEST_PLAN, kết quả | _?_ |
| 6. Báo cáo & bảo vệ | Viết báo cáo, slide, demo | Báo cáo, slide | _?_ |

## Việc tiếp theo
- [x] Luca gửi đề cương
- [x] Chốt hướng kiến trúc (ADR-003)
- [x] Viết kịch bản demo v1 (`docs/DEMO_SCRIPT.md`)
- [x] Luca duyệt kịch bản demo
- [x] Danh sách luật v0 (`docs/RULES_V0.md`), chờ Luca duyệt
- [x] ERD v1 (`docs/ERD.md`), chờ Luca duyệt
- [x] Tạo khung dự án `backend/`, `frontend/` và migration đầu tiên (baseline trống)
- [x] Module auth: đăng ký, đăng nhập, đăng xuất, phiên trong CSDL, RBAC, ghi nhận thiết bị và IP
- [x] Router frontend: hai khu vực Shop (`/`) và Console (`/console`, chặn theo vai trò)
- [x] Module catalog + seed 16 sản phẩm; trang danh sách (tìm kiếm, lọc danh mục, phân trang) và chi tiết sản phẩm
- [x] Module cart + promotion: giỏ hàng, áp voucher theo luật nghiệp vụ, tự gỡ voucher khi giỏ hết đủ điều kiện
- [x] Module order + fulfillment: checkout (COD/trả trước, idempotency, ghi lượt dùng voucher chống race condition), lịch sử đơn, giả lập giao hàng
- [x] Module events + module risk: đặc trưng F01–F11, luật v1, ma trận quyết định, nối vào voucher_apply / payment_options / place_order; Live Monitor (polling)
- [x] Case Queue, Case Detail: worker mở/gom case theo cụm, nhận xử lý, kết luận bắt buộc ghi lý do, duyệt/từ chối đơn chờ xác minh, audit log
- [x] Attack Lab: 4 kịch bản demo (farm voucher, gia đình chung Wi-Fi, COD giá trị cao, lịch sử bùng hàng) chạy qua worker, gọi API thật, so sánh kỳ vọng/thực tế
- [x] Trang Luật rủi ro: xem luật dạng câu dễ đọc, số lần khớp 7 ngày, sửa con số tạo phiên bản mới (chỉ Risk Manager/Admin), lịch sử phiên bản, audit
- [x] Báo cáo/KPI (tác động nghiệp vụ ước tính, phân bố quyết định, độ trễ p50/p95/p99, case, hiệu quả từng luật kèm giả định) và Audit Log
- [x] Simulator cho thực nghiệm dev/test (Live Monitor đã có bản polling; SSE là Recommended)
- [x] (Recommended) Giới hạn đăng nhập sai (5 lần/tài khoản, 20 lần/IP trong 15 phút) và che email trên Console; xem liên hệ đầy đủ cần lý do + audit (chỉ Risk Manager/Admin)
- [ ] Hỏi hạn nộp và yêu cầu của GVHD; chốt 2 nhóm chính sách (voucher tân thủ + COD)

- [x] Script `demo reset` (chỉ chạy khi DEMO_MODE, cần --yes; tạo lại nhân vật Minh, Khang, Lan và nhân viên)
