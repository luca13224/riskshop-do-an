# PROGRESS LOG

Ghi mới nhất ở trên cùng.

## 2026-10-30 — Thiết kế tối thiểu và khung dự án
**Đã hoàn thành**
- Kịch bản demo v1, bộ luật v0, ERD v1 (28 bảng); Luca đã duyệt cả ba.
- Khung backend: FastAPI 0.162.0, SQLAlchemy 2.1.6, Alembic 1.20.1, PyMySQL 1.2.3; cấu hình qua `.env`; định dạng lỗi thống nhất kèm `request_id`; `GET /api/health` kiểm tra CSDL; 6 test qua.
- CSDL `riskshop` và `riskshop_test` với user riêng `riskshop` (chỉ có quyền trên hai CSDL này); migration baseline đã chạy trên cả hai.
- Khung frontend: tạo bằng `shadcn init -t vite` (preset Nova, base Radix): Vite 8, React 19, TypeScript, Tailwind 4, TanStack Query 5.105.0; proxy `/api` sang backend; trang kiểm tra kết nối hiển thị đúng cả khi backend chạy và khi backend tắt.
- 7 skill dự án mới; giọng chat chuyển sang thân thiện, dễ hiểu.

**Ghi chú kỹ thuật**
- `npm audit`: 3 lỗ hổng low (deepmerge qua CLI shadcn), chấp nhận và theo dõi.
- Giữ `httpx` cho TestClient (Starlette gợi ý `httpx2`, nhưng gói này mới phát hành vài ngày).
- Cache pip/npm đặt ở `D:\_cache` (chỉ cho các lệnh trong phiên) để không làm đầy ổ C.

**Bước tiếp theo**
- Module auth + router frontend hai khu vực.

## 2026-10-30 — Chốt kiến trúc, dựng môi trường
**Đã hoàn thành**
- Spike WooCommerce: viết Risk API giả (`spike/risk-mock/`, FastAPI 0.162.0, 7/7 test qua). Hợp đồng `event → decision + actions + reason_codes` sẽ dùng lại cho Risk module thật.
- Cài XAMPP 8.3.36 (PHP 8.3.36, MariaDB 10.11.16), chuyển từ `C:\xampp` sang `D:\xampp`; giới hạn Apache và MariaDB chỉ nhận kết nối từ 127.0.0.1; bật thêm extension PHP gd, intl, sodium, zip (bản sao lưu `php.ini.bak-before-wp`).
- Tạo thêm skill dự án `ui-design-bar`, `defense-prep`; cập nhật `CLAUDE.md`.
- Đánh giá skill `10k-websites` (landing page dùng video AI): không cài, vì không hợp kiến trúc, ép dịch vụ trả phí và chèn link affiliate.

**Quyết định đã chốt**
- ADR-003 (Accepted): tự xây toàn bộ theo modular monolith; React + Vite + TypeScript + Tailwind/shadcn; FastAPI + SQLAlchemy + Alembic; MariaDB; worker dùng bảng jobs; SSE cho realtime.
- ADR-002 (WooCommerce lai) chuyển sang Superseded.
- Cách làm việc: sản phẩm và demo trước, báo cáo viết sau; Luca vừa làm vừa học TypeScript.

**Vấn đề còn mở**
- ~~Phần WooCommerce còn sót sau khi script chạy dở~~: đã xóa database `wp_shop`, user `wp_shop` và thư mục `D:\xampp\htdocs\shop`.
- `C:\xampp` (bản cài cũ, khoảng 0,84 GB) chờ Luca tự xóa.
- Chưa có thời hạn và yêu cầu của GVHD; chưa chốt các loại lạm dụng thuộc MVP.

**Bước tiếp theo**
- Thiết kế tối thiểu: kịch bản demo → danh sách luật v0 → ERD.
- Tạo khung dự án `backend/` và `frontend/`.

## 2026-10-30 — Phản biện đề cương ban đầu
**Đã hoàn thành**
- Đọc đề cương `DeCuong_DATN_HaTienLuc_2251162067_64HTTT4.docx`; viết bản tư vấn 11 phần tại `docs/reviews/2026-10-30_INITIAL_REVIEW.md`.
- Tạo `CLAUDE.md` (nguyên tắc cố vấn, Claude Code tự đọc mỗi phiên) và 2 skill dự án: `adr`, `session-wrap` trong `.claude/skills/`.

**Quyết định đã chốt**
- Chưa có. Mọi nội dung trong bản tư vấn đang ở trạng thái đề xuất.

**Đề xuất chưa chốt (chờ Luca và GVHD)**
- Thu hẹp phạm vi còn 2 nhóm chính sách: voucher tân thủ và COD; bơm đơn ảo đưa ra hướng phát triển.
- Hướng sản phẩm D: Risk Decision Module + Risk Console + Mini Shop tối giản + Simulation & Evaluation Lab, trong một modular monolith.
- Mô hình rủi ro hai lớp (hồ sơ tài khoản + điểm giao dịch dạng scorecard) và ma trận quyết định theo chính sách.
- Stack: PostgreSQL thay MongoDB; bảng `jobs` thay Celery; Redis và LLM là tùy chọn.
- Đổi p95 ≤ 45 ms và FPR ≤ 5% thành mục tiêu dự kiến có điều kiện đo rõ ràng.

**Vấn đề còn mở**
- Ngày bắt đầu tuần 1 và ngày bảo vệ.
- GVHD có yêu cầu bắt buộc nào về công nghệ hoặc phạm vi không.
- Luca thành thạo nhất ngôn ngữ/CSDL nào.
- Tài liệu tham khảo [2] trong đề cương cần xác minh nguồn.

**Bước tiếp theo**
- Luca đọc bản tư vấn, phản hồi các điểm đồng ý/không đồng ý.
- Gặp GVHD xin ý kiến về các thay đổi lớn.

## 2026-10-30 — Phiên khởi động
**Đã hoàn thành**
- Thống nhất vai trò cố vấn và nguyên tắc làm việc.
- Chọn thư mục dự án `D:\do_an`, tạo khung 7 tài liệu trong `docs/`.
- Khởi tạo Git (nhánh `main`) và thêm `.gitignore`.

**Quyết định đã chốt**
- ADR-001: tài liệu dự án lưu dạng Markdown trong `docs/`.

**Nhận định ban đầu (chưa chốt)**
- Phạm vi "lạm dụng chính sách" quá rộng, nên giới hạn MVP ở 2–3 loại.
- Thiếu dữ liệu thật, cần kế hoạch dữ liệu mô phỏng.
- Rule-based làm lõi; ML chỉ là phần Advanced.
- Nên xây sàn mô phỏng tối giản; trọng tâm là Risk Engine và Admin Console.

**Vấn đề còn mở**
- Chưa có đề cương, hạn nộp, yêu cầu của GVHD.

**Bước tiếp theo**
- Luca cung cấp đề cương, hạn nộp và yêu cầu của GVHD.
- Phản biện đề tài và chốt phạm vi MVP.
