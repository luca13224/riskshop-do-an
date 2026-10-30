# ROADMAP

> Các mốc thời gian sẽ được điền khi biết hạn nộp/bảo vệ.

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
- [ ] Module events (telemetry: product_view, voucher_attempt, signup, login) + module risk: đặc trưng F01–F11, luật v0, ma trận quyết định, nối vào voucher_apply / payment_options / place_order
- [ ] Console: Live Monitor (SSE), Case Queue, Case Detail, Rules, Attack Lab, Audit Log
- [ ] (Recommended) Giới hạn số lần thử đăng nhập (rate limit)
- [ ] Hỏi hạn nộp và yêu cầu của GVHD; chốt 2 nhóm chính sách (voucher tân thủ + COD)
