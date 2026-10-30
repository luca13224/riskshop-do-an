# PROGRESS LOG

Ghi mới nhất ở trên cùng.

## 2026-10-30 — Risk Engine v1
**Đã hoàn thành**
- Module `events` (signup, login, product_view, voucher_attempt) và `risk` (features F01–F11 đọc chỉ-đọc bằng SQL, 3 loại luật thuần, điểm theo từng chính sách voucher/COD, ma trận quyết định, fail-open/fail-closed, lưu quyết định + rule_hits bất biến, luật có phiên bản; seed R01–R10). Nối vào áp voucher, payment-options, checkout.
- Console Live Monitor (polling 2 giây, bấm dòng để xem lý do). Checkout ẩn COD theo Risk Engine; đơn chờ xác minh có thông báo.
- 90 test qua (20+ test kịch bản demo). Đã chạy thử "tấn công thu nhỏ": farm3 bị gỡ voucher, đơn COD 5,49 triệu chờ duyệt.
- Sửa lỗi logic: payment_options dùng cùng luật/ngưỡng với place_order (R06, R08 lên v2; policy payment_options v2).

- Đã kiểm tra trên trình duyệt: tài khoản mới, giỏ 3,78 triệu → COD bị khóa, tự chọn chuyển khoản; đơn 2,84 triệu của khách đã xem sản phẩm → cho qua (0 điểm, đúng luật).
- ADR-004 (feature store chỉ đọc), RULES_V0 lên v0.1.

**Việc tiếp theo**
- Case Queue / Case Detail (worker mở case khi `open_case`), Rules UI, Attack Lab, Audit Log.

## 2026-10-30 — Đặt hàng: khép kín luồng mua hàng
**Đã hoàn thành**
- Backend `order`: checkout trong một transaction (khóa dòng sản phẩm `FOR UPDATE` theo thứ tự id, kiểm tra lại voucher, chụp giá vào đơn, ghi lượt voucher bằng `UPDATE` có điều kiện + UNIQUE, làm trống giỏ; lỗi thì rollback toàn bộ); bắt buộc header `Idempotency-Key` (gửi lặp trả đơn cũ, 200); địa chỉ chuẩn hóa + băm (cho luật R03); xem đơn của mình (đơn người khác trả 404); Console: danh sách đơn, giả lập giao hàng theo máy trạng thái (giao thất bại thì hoàn kho, COD giao thành công thì PAID). 68 test qua, gồm 2 test tranh chấp đồng thời (2 khách giành món cuối và lượt voucher cuối: đúng 1 thành công).
- Frontend: trang thanh toán (địa chỉ, COD/chuyển khoản giả lập, mã idempotency tạo một lần mỗi lần vào trang), đơn hàng của tôi, chi tiết đơn có dòng thời gian, trang Đơn hàng trong Console có nút giả lập giao hàng (chỉ Admin/Risk Manager); giờ hiển thị theo múi giờ Việt Nam.
- Đã thử trọn luồng trên trình duyệt: đăng ký → thêm vào giỏ → áp TANTHU → đặt hàng COD → Admin giao hàng → "Đã giao".

**Còn mở**
- Chưa có Risk Engine: các chỗ nối `voucher_apply` và `place_order` đã đánh dấu trong code.
- Chưa có hủy đơn phía khách; Console chưa có menu trên điện thoại.

## 2026-10-30 — Giỏ hàng và voucher
**Đã hoàn thành**
- Backend `promotion` (bảng vouchers, kiểm tra điều kiện: tồn tại, còn hạn, còn lượt, thành viên mới trong 30 ngày, giá trị tối thiểu; giảm cố định hoặc % có trần) và `cart` (mỗi khách một giỏ, kiểm tra tồn kho, tự gỡ voucher và báo lý do khi giỏ không còn đủ điều kiện). Cart lấy sản phẩm qua hàm công khai của catalog (giữ ranh giới module). Seed voucher TANTHU (có cờ `risk_checked`), GIAM10. 53 test qua.
- Frontend: nút thêm vào giỏ có chọn số lượng (chưa đăng nhập thì chuyển sang trang đăng nhập rồi quay lại), icon giỏ có số trên thanh trên cùng, trang giỏ hàng (đổi số lượng, xóa, ô mã giảm giá, tóm tắt tiền). Đã thử trên trình duyệt.
- Chỗ nối Risk Engine (context `voucher_apply`) đã đánh dấu trong `cart/service.py`.

**Sự cố**
- `uvicorn --reload` vẫn kẹt kể cả khi dùng watchfiles: từ nay chạy backend không reload, khởi động lại sau mỗi đợt sửa (ghi trong skill `debug-helper`, README).

**Chưa commit** (theo cách làm mới: commit khi xong trọn luồng MVP).

## 2026-10-30 — Module catalog (làm trực tiếp trên trang xem trước)
**Đã hoàn thành**
- Backend `app/modules/catalog`: bảng `products` (migration đã thử lên/xuống); API `GET /api/products` (tìm kiếm có escape ký tự `%`/`_`, lọc danh mục, phân trang tối đa 48), `GET /api/products/{slug}`, `GET /api/categories`; seed 16 sản phẩm mẫu; 11 test mới, tổng 34 test qua.
- Frontend: trang chủ có tìm kiếm, lọc danh mục, lưới sản phẩm, phân trang, đủ trạng thái tải/rỗng/lỗi; trang chi tiết sản phẩm; bộ lọc nằm trên URL; tự cuộn lên đầu khi đổi trang; ảnh minh họa tự vẽ theo danh mục (chạy offline, không vướng bản quyền ảnh).
- Đã kiểm tra trên trình duyệt: lọc, tìm, không có kết quả, link sản phẩm hỏng, màn hình điện thoại 375px (không tràn ngang).

**Sự cố và cách xử lý**
- `uvicorn --reload` lại kẹt: đã cài `watchfiles` (thêm vào `requirements-dev.txt`) để nạp lại code ổn định trên Windows.
- ESLint bắt lỗi gọi `setState` trong `useEffect` và dùng `? :` như câu lệnh: đã sửa (dùng `key` để tạo lại ô tìm kiếm, tách hàm `setOrDelete`).

## 2026-10-30 — Module auth và hai khu vực giao diện
**Đã hoàn thành**
- Backend `app/modules/auth`: bảng users, devices, user_devices, user_ips, auth_sessions (migration `auth tables`, đã thử upgrade/downgrade/upgrade); API register/login/logout/me; mật khẩu Argon2id; phiên lưu bản băm token, cookie HttpOnly + SameSite=Lax; thông báo đăng nhập sai không lộ email; `require_roles` chặn theo vai trò ở backend; ghi nhận thiết bị (header `X-Device-Id`) và IP (chỉ lưu bản băm HMAC + bản che); CLI tạo tài khoản nhân viên. 23 test qua, chạy trên CSDL `riskshop_test` qua migration thật.
- Frontend: React Router v8; Shop layout (đăng ký, đăng nhập, đăng xuất), Console layout có menu theo kịch bản demo và người gác cổng `RequireStaff`; form dùng React Hook Form + Zod; thông báo lỗi tiếng Việt.
- Đã kiểm tra trên trình duyệt: báo lỗi form, đăng ký → vào Shop, khách vào `/console` bị chặn, chưa đăng nhập bị chuyển sang trang đăng nhập kèm `next`, đăng nhập sai và đúng, giao diện điện thoại 375px, tab mới không có lỗi console.

**Sự cố đã gặp và cách xử lý**
- `downgrade` tự sinh của Alembic lỗi trên MariaDB (lỗi 1553, xóa index đang làm chỗ dựa cho khóa ngoại): bỏ `drop_index` riêng; đã ghi vào skill `db-design`.
- CLI in tiếng Việt lỗi trên cửa sổ dòng lệnh Windows; `uvicorn --reload` bị kẹt khi nạp lại: đã sửa hoặc ghi cách xử lý vào skill `debug-helper`.

**Còn mở**
- Chưa có rate limit cho đăng nhập (Recommended).
- Console chưa có menu cho màn hình điện thoại (Console ưu tiên desktop).
- Chưa ghi sự kiện `signup`/`login` vào bảng `events` (làm cùng module events, phục vụ luật R06).

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
