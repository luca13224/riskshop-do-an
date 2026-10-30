# PROGRESS LOG

Ghi mới nhất ở trên cùng.

## 2026-10-30 — Tuần 1 (phần 1): mặt tiền shop theo ADR-005
**Đã hoàn thành**
- Gian hàng chỉ còn đồ công nghệ: 6 danh mục, 24 sản phẩm. Sản phẩm cũ được ẩn chứ không xóa. Thêm cột `products.specs` (thông số kỹ thuật dạng danh sách [nhãn, giá trị]).
- Khu vực Shop luôn ở tông sáng (lớp `.shop` trong `index.css`), không đổi theo chế độ sáng/tối của Console. Màu nhấn vàng chỉ dùng cho nút mua (`variant="buy"`).
- Khung shop: thanh thông báo mã TANTHU, header dính trên cùng, footer tối.
- Trang chủ theo nhịp khối: banner tạm (tuần 2 sẽ thay bằng "rạp chiếu phim"), ô danh mục, "Nổi bật tuần này" cuộn ngang (xen kẽ theo danh mục), banner câu chuyện có vết khuyết, tất cả sản phẩm (tìm kiếm, lọc, phân trang), dải cam kết.
- Thẻ sản phẩm kiểu Neotek: nền `#f2f2f2`, nút "Xem nhanh" hiện khi rê chuột hoặc focus (màn hình cảm ứng thì luôn hiện), nút thêm giỏ nằm trong vết khuyết. Dùng "stretched link" để không lồng nút trong link.
- Popup xem nhanh dùng `<dialog>` của trình duyệt (tự khóa focus, Esc để đóng).
- Trang chi tiết: breadcrumb, bảng thông số, cam kết, sản phẩm cùng danh mục.
- Đã kiểm tra ở 1440 px và 375 px (sửa lỗi tràn ngang trên điện thoại). 140 test qua.

**Bài học**
- React StrictMode ở chế độ dev chạy effect hai lần. Gọi `dialog.close()` trong hàm dọn dẹp sẽ bắn sự kiện `close`, làm popup tắt ngay khi vừa mở.
- Lưới CSS có một cột `auto` sẽ bị phần tử cuộn ngang kéo giãn. Phải dùng `minmax(0, 1fr)`.

**Còn thiếu**
- Ảnh sản phẩm thật (chờ chọn nguồn, xem `docs/assets/IMAGE_BRIEF.md`). Hiện đang dùng icon theo danh mục trên nền xám.
- Mô tả dài cho từng sản phẩm (phần "Mô tả" đang lặp lại mô tả ngắn).

## 2026-10-30 — Giới hạn đăng nhập sai và che dữ liệu cá nhân
**Đã hoàn thành**
- Bảng `login_attempts` (chỉ lưu bản băm HMAC). Sai 5 lần/tài khoản hoặc 20 lần/IP trong 15 phút → 429 `LOGIN_RATE_LIMITED`, kiểm tra trước khi so mật khẩu, áp dụng cả với email không tồn tại (không lộ email nào có thật).
- Chỉ đếm lần sai, và bộ đếm theo tài khoản về 0 khi đăng nhập đúng; nhờ vậy Attack Lab (đăng nhập đúng nhiều lần từ localhost) không bị chặn.
- Mọi API Console trả email đã che, che ở backend bằng kiểu `MaskedEmail` trong schema. Khách vẫn thấy email đầy đủ của chính mình.
- `POST /api/console/users/{id}/reveal-contact`: chỉ Risk Manager/Admin, lý do ≥ 10 ký tự, ghi audit (không chép PII vào log). Thẻ "Liên hệ khách hàng" ở trang chi tiết case; Audit Log có bộ lọc "Khách hàng".
- `test_privacy.py`; tổng 138 test qua. Đã kiểm tra trên trình duyệt: email bị che, xem liên hệ có ghi audit, trang đăng nhập báo lỗi khi vượt giới hạn.

**Giới hạn đã biết**
- Chưa giới hạn đăng ký theo IP (sẽ làm hỏng kịch bản farm của Attack Lab; farm do Risk Engine xử lý).
- `login_attempts` chưa có việc dọn dữ liệu cũ (Recommended: job xóa bản ghi quá 1 ngày).
- Kẻ tấn công có thể cố tình nhập sai để khóa tài khoản người khác 15 phút (đánh đổi phổ biến của cơ chế này).

## 2026-10-30 — Simulator và thực nghiệm
**Đã hoàn thành**
- `backend/simulator`: persona hợp lệ / hard negative / lạm dụng, gọi đúng API qua `TestClient`, nhãn thật trong `sim_labels` (Risk không đọc). CSDL riêng `riskshop_sim`.
- Báo cáo Markdown + JSON trong `docs/experiments/`: confusion, precision/recall/FPR kèm KTC Wilson 95%, theo persona, theo nhóm, tác động nghiệp vụ, độ trễ.
- Sửa lỗi trong chính bộ mô phỏng: lambda trong vòng lặp đọc nhầm địa chỉ của nhóm cuối (late binding) làm gia đình bị gắn cờ oan 9/25 → sau sửa 0/25.
- Chạy tập test một lần với bộ luật v1 đã khóa. Kết quả và cách đọc: xem TEST_PLAN mục 3.
- `test_simulator.py`; tổng 126 test qua.

**Phát hiện quan trọng**
- Biến thể chưa biết: recall 0/33. Gia đình 5–6 người bị gỡ voucher. Bomber lịch sử ngắn lọt.

**Bước tiếp theo**
- (Đã quyết) Giữ bộ luật v1; các điểm yếu trên đưa vào mục "Giới hạn và hướng phát triển" của báo cáo, không làm luật v2.

## 2026-10-30 — Demo reset
**Đã hoàn thành**
- `python -m app.modules.lab.reset --yes`: xóa toàn bộ dữ liệu, seed lại 16 sản phẩm, voucher TANTHU/GIAM10, luật v1; tạo nhân viên (analyst, manager, admin) và nhân vật Minh (khách mới hợp lệ), Khang (1 đơn COD thành công, 4 thất bại trong quá khứ), Lan (30 đơn giao thành công); mật khẩu ngẫu nhiên ghi vào `backend/.env.accounts`.
- Chốt an toàn: từ chối nếu không có `DEMO_MODE=true` hoặc thiếu `--yes`.
- Test: chạy reset hai lần liên tiếp vẫn ra đúng trạng thái chuẩn; sau reset, Minh dùng được TANTHU, Khang bị ẩn COD, Lan đặt COD 5,49 triệu được xác nhận ngay. 123 test qua.
- Lịch sử đơn của Khang và Lan là dữ liệu seed ghi trực tiếp vào CSDL (có ghi chú "Dữ liệu seed"), không đi qua API.

## 2026-10-30 — Báo cáo/KPI và Audit Log (cảnh 7 của kịch bản demo)
**Đã hoàn thành**
- Module `reports` (chỉ đọc): KPI theo khoảng 24 giờ / 7 / 30 ngày gồm tác động nghiệp vụ ước tính (giá trị voucher ngăn được, chi phí COD tránh được, đơn bị giữ, khách hợp lệ bị giữ nhầm), phân bố quyết định và theo điểm kiểm soát, độ trễ p50/p95/p99 (nearest-rank, đo ở server), thống kê case, hiệu quả từng luật (số lần khớp, kết luận case, tỷ lệ chính xác); các giả định quy đổi tiền được trả kèm báo cáo.
- Audit Log: chỉ Risk Manager/Admin xem (Analyst bị 403), lọc theo case/luật/Attack Lab.
- Risk Engine lưu thêm `voucher_code` vào snapshot để báo cáo tính được giá trị voucher.
- 121 test qua. Đã kiểm tra trên trình duyệt; số "6 tài khoản bị gỡ voucher" được truy ngược và xác nhận đúng: farm1–2 bị gỡ ở bước đặt hàng nhờ luật địa chỉ (địa chỉ farm đã bị các lần chạy trước dùng chung), farm3–6 bị gỡ ở bước áp mã.

**Lưu ý cho thực nghiệm**
- Các lần chạy Attack Lab tích lũy dữ liệu (cùng địa chỉ, cùng IP), nên kết quả lần chạy sau có thể nghiêm hơn lần đầu. Cần script `demo reset` để đưa dữ liệu về trạng thái chuẩn trước buổi demo và trước mỗi đợt đo.
- Độ trễ hiện đo trên máy phát triển với vài chục lượt, chưa phải đo tải; không dùng làm kết luận.

## 2026-10-30 — Trang Luật rủi ro (cảnh 6 của kịch bản demo)
**Đã hoàn thành**
- Backend `risk/rules_admin.py`: danh sách luật kèm phiên bản đang dùng và số lần khớp 7 ngày; lịch sử phiên bản; tạo phiên bản mới khi sửa (chỉ Risk Manager/Admin, Analyst bị 403). Chỉ cho sửa con số và bật/tắt: đổi đặc trưng, phép so sánh, độ mạnh hay số bậc đều bị từ chối; điểm trong khoảng -100..100, ngưỡng không âm; bắt buộc lý do; ghi audit log. Phiên bản mới có hiệu lực ngay ở lần chấm điểm kế tiếp.
- Giao diện: luật hiển thị thành câu ("Khi số tài khoản mới trên cùng thiết bị ≥ 3 thì cộng 35 điểm"), ô số chỉ hiện khi sửa, lịch sử phiên bản.
- 118 test qua. Đã diễn lại cảnh 6 trên trình duyệt: R02 v2 (≥2: +40), rồi khôi phục bằng v3 (≥3: +35) để các kịch bản Attack Lab giữ kỳ vọng ban đầu.
- Sửa DEMO_SCRIPT cảnh 6: phải đổi cả điểm (≥2 tài khoản: +40) thì tài khoản thứ 2 mới bị gỡ voucher (10 + 40 = 50); chỉ hạ ngưỡng thì mới được 45 điểm, chưa đủ.

**Còn mở**
- Ngưỡng của ma trận quyết định (decision_policies) chưa có giao diện sửa (hiện chỉ sửa qua seed, có phiên bản).

## 2026-10-30 — Attack Lab (cảnh 2, 4, 5 của kịch bản demo)
**Đã hoàn thành**
- Module `lab`: 4 kịch bản (farm voucher 6 tài khoản/1 thiết bị, gia đình 4 người chung Wi-Fi + địa chỉ, COD 5,49 triệu từ tài khoản mới, khách bùng 4/5 đơn COD). Mỗi bước ghi kỳ vọng và kết quả thực tế; chạy trong worker, gọi API thật qua HTTP (httpx chuyển sang requirements chính).
- Chỉ bật khi `DEMO_MODE=true` (tắt thì API trả 404 như không tồn tại), chỉ vai Admin; mỗi lần chạy ghi audit log.
- Giao diện Attack Lab: thẻ kịch bản (mô tả + kỳ vọng), danh sách lần chạy cập nhật mỗi giây khi đang chạy.
- 107 test qua; test chạy trọn 4 kịch bản qua API, mọi bước khớp kỳ vọng. Đã chạy thử trên trình duyệt: farm voucher "Hoàn tất, đúng kỳ vọng" (2 được dùng voucher, 4 bị gỡ).

**Giới hạn đã biết**
- Mọi lưu lượng của Lab đi từ 127.0.0.1 nên cùng một IP; luật IP (R04, tín hiệu yếu) vì vậy luôn được cộng. Ghi rõ khi trình bày.

## 2026-10-30 — Case management (cảnh 3 của kịch bản demo)
**Đã hoàn thành**
- Hàng đợi việc nền trong CSDL (`app/core/jobs.py`: enqueue cùng transaction, worker lấy việc bằng `FOR UPDATE SKIP LOCKED`, thử lại với thời gian chờ tăng dần, quá số lần thì failed) và worker `python -m worker.main`.
- Risk Engine xếp việc `open_case` khi quyết định có `open_case`; worker mở case mới hoặc gom vào case đang mở của cùng cụm (voucher: theo thiết bị; COD: theo đơn). Mỗi cụm chỉ có một case mở nhờ cột `open_cluster_key` UNIQUE.
- Module `cases`: danh sách, chi tiết (bằng chứng: các quyết định + luật khớp, tài khoản cùng thiết bị, đơn hàng chỉ hiện khu vực, lịch sử xử lý), nhận xử lý, kết luận bắt buộc ghi lý do; chỉ người nhận mới được kết luận; kết luận case COD sẽ duyệt hoặc từ chối đơn chờ xác minh (từ chối thì hoàn kho). Module `audit` ghi mọi thao tác trong cùng transaction.
- Giao diện Case Queue (tự cập nhật 5 giây) và Case Detail. 99 test qua.
- Đã thử trên trình duyệt: tấn công thu nhỏ 5 tài khoản farm → worker mở case cụm 95 điểm và case COD 70 điểm → Admin nhận xử lý → kết luận lạm dụng.

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
