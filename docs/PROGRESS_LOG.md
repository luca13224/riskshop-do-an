# PROGRESS LOG

Ghi mới nhất ở trên cùng.

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
