# DECISIONS (Architecture Decision Records)

Mỗi quyết định quan trọng ghi theo mẫu bên dưới. Không xóa quyết định cũ; nếu thay đổi thì tạo ADR mới và đánh dấu ADR cũ là "Superseded".

## Mẫu
```
## ADR-XXX: <Tiêu đề>
- Ngày:
- Trạng thái: Proposed | Accepted | Superseded by ADR-YYY
- Bối cảnh: vấn đề cần quyết định
- Các phương án: A, B, C (ưu/nhược)
- Quyết định: chọn gì
- Lý do:
- Hệ quả / rủi ro:
```

---

## ADR-001: Lưu tài liệu dự án dạng Markdown trong thư mục docs/
- Ngày: 2026-10-30
- Trạng thái: Accepted
- Bối cảnh: Cần một hệ thống tài liệu dài hạn, theo dõi được thay đổi.
- Các phương án: (A) Markdown trong repo; (B) Word/Google Docs rời rạc.
- Quyết định: A.
- Lý do: Dễ quản lý phiên bản bằng Git, đặt cạnh mã nguồn, dễ chuyển thành báo cáo sau.
- Hệ quả: Báo cáo đồ án chính thức (Word/PDF) sẽ được soạn riêng, dựa trên nội dung các file này.

## ADR-002: Kiến trúc lai — WooCommerce làm shop, Risk Service riêng bằng FastAPI
- Ngày: 2026-10-30
- Trạng thái: Superseded by ADR-003 (spike dừng trước khi cài WordPress)
- Bối cảnh: Luca ưu tiên sản phẩm và demo ấn tượng; đã quen PHP/WordPress, biết React ở mức cơ bản. Tự xây shop tốn nhiều thời gian nhưng không phải phần ăn điểm.
- Các phương án:
  - (1) Tự xây toàn bộ (React + FastAPI): toàn quyền kiểm soát, nhưng khối lượng lớn nhất.
  - (2) Lai: WooCommerce làm shop, plugin connector PHP gọi Risk Service (FastAPI), Risk Console bằng React: shop có sẵn, công sức dồn vào lõi rủi ro; rủi ro là khả năng can thiệp hook checkout của WooCommerce.
  - (3) Làm hết trong WordPress (luật viết bằng PHP, Console trong WP Admin): ít code nhất, nhưng kiến trúc yếu và khó thực nghiệm.
- Quyết định (dự kiến): (2). Thay MongoDB bằng MySQL 8 hoặc MariaDB dùng chung cho cả WooCommerce và Risk Service (hai database riêng).
- Lý do: tập trung vào phần lõi; câu chuyện tích hợp "nền tảng rủi ro cắm vào shop có sẵn" sát thực tế; Luca chỉ cần học một hệ quản trị CSDL.
- Điều kiện chốt: spike 2–3 ngày chứng minh plugin connector làm được 3 việc: gỡ coupon, ẩn COD, chuyển đơn sang On hold, dựa trên phản hồi của Risk Service. Spike thất bại thì quay về (1).
- Hệ quả / rủi ro: hội đồng sẽ hỏi sâu vào Risk Service và connector; cần nói rõ shop là "hệ thống TMĐT nguồn" dùng WooCommerce; cần hỏi GVHD có chấp nhận dùng WooCommerce không.

## ADR-003: Tự xây dựng toàn bộ hệ thống theo kiến trúc modular monolith
- Ngày: 2026-10-30
- Trạng thái: Accepted
- Bối cảnh: Luca muốn toàn quyền với sản phẩm và để mọi phần code đều do mình hiểu và giải thích được. Phương án lai WooCommerce (ADR-002) phụ thuộc hook checkout của WooCommerce và buộc làm song song PHP với Python.
- Các phương án:
  - (1) Tự xây toàn bộ: toàn quyền với luồng voucher, checkout, COD; một ngôn ngữ backend; đổi lại khối lượng giao diện shop lớn hơn.
  - (2) Lai WooCommerce + Risk Service (ADR-002): shop có sẵn, nhưng rủi ro tích hợp hook và phải dùng hai stack.
  - (3) Làm hết trong WordPress: kiến trúc yếu, khó thực nghiệm.
- Quyết định: (1). Một ứng dụng backend FastAPI chia module theo nghiệp vụ; một ứng dụng frontend React gồm hai khu vực Shop (`/`) và Risk Console (`/console`).
- Stack:
  - Frontend: React + Vite + TypeScript, Tailwind CSS + shadcn/ui, TanStack Query, TanStack Table, React Hook Form + Zod, Recharts.
  - Backend: FastAPI + SQLAlchemy 2 + Alembic + Pydantic; pytest.
  - CSDL: MariaDB (bản trong XAMPP tại `D:\xampp`), sau này có thể chuyển sang MySQL 8 trong Docker. Không dùng MongoDB.
  - Tác vụ nền: bảng `jobs` + một tiến trình worker Python; không dùng Celery hay Redis ở MVP.
  - Realtime cho Console: Server-Sent Events (SSE).
  - Mô phỏng tấn công: Python CLI gọi API thật; Playwright cho bot qua trình duyệt (Recommended).
- Lý do: chiều sâu kỹ thuật (transaction, race condition, idempotency, luật có phiên bản) nằm hoàn toàn trong code của Luca; một ngôn ngữ backend; dùng lại được hợp đồng API của Risk mock trong spike; MariaDB đã cài và Luca quen MySQL.
- Ràng buộc để giữ tiến độ:
  - Shop chỉ làm đủ cho demo: danh sách và chi tiết sản phẩm, giỏ hàng, voucher, checkout COD/trả trước, lịch sử đơn. Không làm đánh giá, chat, tìm kiếm nâng cao, đăng nhập mạng xã hội.
  - Module `risk` không phụ thuộc module `order`; chỉ nhận ngữ cảnh đánh giá và trả về quyết định cùng `actions`.
  - Không đổi hướng kiến trúc lần nữa trừ khi có ADR mới với lý do rõ ràng.
- Hệ quả / rủi ro: khối lượng frontend lớn hơn trong khi Luca chưa học Vite/TypeScript, nên học theo kiểu vừa làm vừa học, có review; Docker hoãn lại vì ổ C còn ít dung lượng.

## ADR-004: Risk Engine đọc dữ liệu của module khác ở chế độ chỉ đọc, qua một lớp "feature store"
- Ngày: 2026-10-30
- Trạng thái: Accepted
- Bối cảnh: Đặc trưng F01–F11 cần dữ liệu của nhiều module (users, user_devices, user_ips, addresses, orders, events). ADR-003 yêu cầu module `risk` không phụ thuộc `order`; trong khi `order` gọi `risk` lúc đặt hàng. Nếu `risk` import code của `order` sẽ tạo vòng phụ thuộc.
- Các phương án:
  - (1) Mỗi module tự cung cấp hàm đếm cho risk: đúng ranh giới nhưng gây vòng import order ↔ risk, và rải logic đặc trưng ra nhiều nơi.
  - (2) Risk đọc bảng của module khác bằng SQL thuần, chỉ đọc, tập trung trong `risk/features.py`.
  - (3) Bảng tổng hợp riêng do worker cập nhật bất đồng bộ (account_risk_profiles): tách biệt hoàn toàn, nhưng phức tạp và có độ trễ dữ liệu.
- Quyết định: (2) cho MVP. (3) để Recommended khi dữ liệu lớn.
- Lý do: không có vòng import; toàn bộ định nghĩa đặc trưng nằm ở một file, dễ đọc và dễ bảo vệ; đúng mô hình thực tế (hệ thống rủi ro đọc dữ liệu giao dịch). Ghi dữ liệu vẫn chỉ qua module sở hữu.
- Hệ quả / rủi ro: risk phụ thuộc vào TÊN bảng và cột của module khác; đổi cấu trúc các bảng đó phải kiểm tra lại `features.py` (test kịch bản trong `tests/test_risk_scenarios.py` sẽ báo lỗi nếu lệch).

## ADR-005: Hướng giao diện "rạp chiếu phim" và gian hàng chỉ bán đồ công nghệ
- Ngày: 2026-10-30
- Trạng thái: Accepted
- Bối cảnh: Shop hiện dùng nền tối, ảnh sản phẩm chỉ là ô gradient kèm icon, danh mục lẫn lộn (thời trang, gia dụng, thể thao...). Luca muốn demo ấn tượng. Có ba nguồn tham khảo (xem `docs/reviews/2026-10-30_UI_DIRECTION.md`): prompt landing "Vertex", video "10K websites" (trang kể chuyện theo nhịp cuộn), mẫu WooCommerce "Neotek".
- Các phương án:
  - (1) Giữ nguyên, chỉ làm đẹp từng chi tiết.
  - (2) Dùng nguyên theme hoặc mẫu có sẵn (Neotek / WordPress): trái với ADR-003.
  - (3) Tự xây, kết hợp các nguyên lý: banner tối kiểu Vertex với vòng 3D các danh mục như những màn ảnh trong rạp phim; phần cửa hàng sáng kiểu Neotek; một ẩn dụ chuyển động riêng.
- Quyết định: (3).
  - Banner trang chủ tối, có vòng danh mục 3D. Bấm vào một danh mục thì "màn hình chiếu chính" phía trước hiện sản phẩm của danh mục đó. Cuộn xuống thì "đèn rạp bật sáng", chuyển sang phần cửa hàng tông sáng.
  - Thẻ sản phẩm kiểu Neotek: ảnh tách nền đặt trên nền xám nhạt, rê chuột thì hiện nút thao tác, nút giá nằm trong vết khuyết bo góc ngược.
  - Màu nhấn: cyan điện cho vùng tối (banner, Risk Console), vàng cho nút mua trên vùng sáng. Không thêm màu nhấn nào khác.
  - Gian hàng chỉ bán đồ công nghệ, 6 danh mục, 24 sản phẩm.
  - Ảnh và video được phép tạo bằng AI hoặc lấy từ nền tảng ảnh có giấy phép. Phải đạt chuẩn chất lượng trong `docs/assets/IMAGE_BRIEF.md` và ghi nguồn vào sổ nguồn ảnh.
- Lý do: banner tạo dấu ấn khi demo; phần cửa hàng sáng giúp khách dễ đọc giá và tạo cảm giác tin cậy; đồ công nghệ giá cao làm kịch bản "COD giá trị cao" (cảnh 5b) tự nhiên hơn.
- Hệ quả / rủi ro:
  - Không làm biến thể sản phẩm (màu, dung lượng) có tồn kho riêng ở MVP, vì phải sửa giỏ hàng, đơn hàng và khóa tồn kho.
  - Không dùng kiến trúc "khung cố định phóng to" của Vertex.
  - Băng chuyền 3D phải dừng khi rê chuột hoặc focus, và phải có hàng nút danh mục thay thế cho bàn phím và điện thoại.
  - Tôn trọng `prefers-reduced-motion`.
  - Kết quả thực nghiệm mô phỏng đã ghi được chạy với danh mục cũ. Bộ luật không đổi nên kết quả vẫn có giá trị, nhưng nếu chạy lại thì phải ghi rõ đó là danh mục v2.


## ADR-006: Khiếu nại và danh sách miễn trừ
- Ngày: 2026-10-31
- Trạng thái: Accepted
- Bối cảnh: thực nghiệm (TEST_PLAN mục 3) cho thấy 20–31% khách "hợp lệ nhưng dễ nhầm" bị hạn chế, ví dụ gia đình dùng chung máy hoặc khách mới đặt COD giá trị cao. Hệ thống cần một đường để khách bị chặn nhầm lên tiếng, và để quyết định của nhân viên được ghi nhận lại.
- Các phương án:
  - (1) Không có khiếu nại, khách tự liên hệ CSKH bên ngoài: không lưu vết, không đo được.
  - (2) Khiếu nại xong thì tắt luật cho khách đó: mất khả năng giải thích, khó kiểm tra lại.
  - (3) Khiếu nại gắn với MỘT quyết định cụ thể; chấp nhận thì miễn trừ HÀNH ĐỘNG của chính sách đó trong 30 ngày, luật vẫn chạy và vẫn ghi lại đã khớp.
- Quyết định: (3).
  - Khách chỉ khiếu nại được quyết định hạn chế của chính mình, trong 30 ngày. Mỗi chính sách (voucher/COD) chỉ có một khiếu nại đang mở (`open_key` UNIQUE).
  - Khách chỉ thấy KẾT QUẢ ("Mã giảm giá không được áp dụng"), không thấy luật hay điểm.
  - Analyst xem được; chỉ Risk Manager/Admin kết luận (nguyên tắc bốn mắt). Bắt buộc có câu trả lời cho khách; ghi audit `appeal.resolve`.
  - Chấp nhận thì: thêm bản ghi `risk_allowlist` cho chính sách đó trong 30 ngày, và duyệt đơn nếu đơn đang bị giữ. Từ chối thì không đổi gì.
  - Risk Engine: `decide(..., exempt)` bỏ qua hành động của chính sách được miễn; `features_snapshot.exempt_policies` ghi lại lý do.
- Lý do: khép kín vòng xử lý nhầm, có số liệu để đánh giá, giữ được khả năng giải thích, chống lạm dụng quyền của một người.
- Hệ quả / rủi ro:
  - Kẻ gian có thể khiếu nại để được miễn trừ. Biện pháp giảm thiểu: người kết luận thấy số khiếu nại khác của cùng khách, miễn trừ có hạn 30 ngày, mọi kết luận đều có audit.
  - Miễn trừ theo tài khoản, không theo thiết bị.

## ADR-007: Shop chuyển sang tông navy "rạp chiếu đêm" thống nhất
- Ngày: 2026-10-31
- Trạng thái: Accepted (thay phần "Shop tông sáng" của ADR-005; các phần khác của ADR-005 giữ nguyên)
- Bối cảnh: banner rạp chiếu dùng nền tối, phần còn lại của Shop dùng nền trắng. Khi cuộn xuống, trang chuyển đột ngột từ tối sang trắng, các khối tối (bento, sản phẩm chủ lực, ưu đãi) nằm lọt thỏm trên nền trắng. Luca đánh giá trang "trống trải, lệch lạc" và chọn giữ màu xanh navy của banner.
- Các phương án:
  - (1) Giữ nền trắng, chỉ làm mềm đoạn chuyển: vẫn hai "ngôn ngữ" màu trên một trang.
  - (2) Lai: trang chủ tối, các trang khác (danh mục, chi tiết, giỏ, thanh toán) sáng: đổi trang là đổi tông, cảm giác thiếu nhất quán.
  - (3) Toàn bộ Shop dùng một bộ token navy, banner liền mạch với phần còn lại.
- Quyết định: (3).
  - Token `.shop` đổi sang navy (nền #070b14, bề mặt thẻ #111a2a, chữ #e9eef7, chữ phụ #93a0b6, viền mờ). Màu vàng `buy` vẫn là màu hành động; cyan là màu nhấn.
  - Biến thể `dark:` áp dụng cho cả `.shop` (các thành phần dùng chung như huy hiệu trạng thái đơn tự lấy màu cho nền tối).
  - Bỏ hiệu ứng "đèn rạp bật sáng" (lớp trắng phủ banner) và cơ chế header đổi tông khi nằm trên banner, vì không còn cần.
- Lý do: một bộ màu cho cả cửa hàng; ảnh sản phẩm (ảnh chụp thật) nổi bật hơn trên nền tối; Shop và Risk Console cùng họ màu tối nhưng vẫn phân biệt bằng màu nhấn và mật độ thông tin.
- Hệ quả / rủi ro:
  - Phải giữ độ tương phản chữ đạt WCAG AA trên nền tối (đã tính theo công thức WCAG: chữ phụ #93a0b6 đạt 7.45:1 trên nền #070b14 và 6.59:1 trên thẻ #111a2a; chữ chính trên 14:1).
  - Trang dài trên nền tối dễ "chìm": mỗi chương cần một điểm nhấn ánh sáng (quầng cyan/vàng, viền mờ) thay cho khoảng trắng.

## ADR-008: Bộ luật v2 — luật R11 dựa trên cụm tài khoản quanh địa chỉ
- Ngày: 2026-10-31
- Trạng thái: Accepted
- Bối cảnh: bộ luật v1 bỏ lọt 100% farm "phân tán" (mỗi tài khoản một máy, một mạng, cùng giao về một nhà). Đồ thị liên kết trên Console cho thấy cụm này rõ ràng, nhưng Risk Engine chưa dùng thông tin cụm.
- Các phương án:
  - (1) Tính cụm 2 bước trên toàn đồ thị ở mỗi đơn: bắt rộng hơn nhưng nhiều truy vấn mỗi đơn, khó giải thích.
  - (2) Đặc trưng 1 bước quanh nút địa chỉ (F12 số tài khoản mới, F13 độ phân tán mạng) + luật `compound` sẵn có: một truy vấn, dùng index sẵn có, giải thích được.
  - (3) Học máy / phát hiện cộng đồng: chưa có dữ liệu thật để huấn luyện và đánh giá.
- Quyết định: (2). R11 = voucher tân thủ và F12 ≥ 5 và F13 ≥ 0,75 → +25, độ mạnh trung bình (chỉ gỡ voucher, không giữ hay chặn đơn).
  - Ngưỡng 5 (thiết kế ban đầu là 4) chọn trên tập **dev_v2**: ở ngưỡng 4 độ chính xác riêng của R11 là 61%, ở ngưỡng 5 là 70%.
  - Đánh giá theo giao thức chống học thuộc đề: tập dev và test **mới** (`dev_v2`, `test_v2` seed 3), khóa luật trước khi chạy test, so v1/v2 trên cùng dân số, có một biến thể chưa biết mới (farm gom hàng về nhiều điểm nhận).
- Lý do: tăng recall tổng từ 36,4% lên 44,4% trên tập test mới, khách thông thường không bị ảnh hưởng (0/190), không tăng độ trễ đo được.
- Hệ quả / rủi ro:
  - Hard negative mới: nhóm ở trọ dùng 4G riêng bị gỡ voucher nhầm 14,6% (6/41) trên tập test; đặc trưng mạng không phân biệt được nhóm này với farm. Giảm thiểu: chỉ gỡ voucher, khiếu nại (ADR-006).
  - Farm gom hàng về nhiều điểm nhận vẫn lọt 100% (0/40): kẻ gian chỉ cần chia nhỏ cụm. Đây là giới hạn của luật theo ngưỡng.

## ADR-009: Mô hình rủi ro 2 lớp — Trust Score tài khoản + chấm điểm giao dịch (bộ luật v3)
- Ngày: 2026-10-31
- Trạng thái: Accepted
- Bối cảnh: Luca đề xuất "mỗi tài khoản 100 điểm, bất thường thì trừ dần, điểm thấp thì cắt dần mã giảm giá, về 0 thì hạn chế thanh toán và cắm cờ". Đề cương ban đầu cũng có Trust Score; bộ luật v1/v2 chỉ chấm theo từng giao dịch.
- Các phương án:
  - (1) Thay hẳn bộ luật bằng một "số dư tin cậy" cộng trừ dồn qua thời gian: dễ trừ trùng, khó giải thích, khó sửa khi trừ nhầm.
  - (2) Hai lớp: lớp 1 tính điểm tin cậy từ hiện trạng (mọi luật khớp, mỗi luật một lần, cửa sổ thời gian tự hồi điểm); lớp 2 giữ ma trận quyết định theo giao dịch. Lớp 1 chỉ **thêm** hạn chế theo bậc.
- Quyết định: (2).
  - Bậc: ≥ 70 Bình thường; 50–69 Theo dõi; 30–49 Hạn chế; < 30 Xem xét (mở case lúc đặt hàng); ≤ 0 Rất thấp (tắt COD).
  - Khóa mã theo `min_trust` của từng mã (NGUOIMOI 50, GIAM10 70): danh sách mã "co lại" dần khi điểm giảm.
  - Không chặn thanh toán chỉ vì điểm thấp; BLOCK vẫn cần ≥ 2 luật mạnh. Không hiển thị điểm cho khách.
  - Thêm R12–R15 (SĐT nhận hàng ở nhiều địa chỉ, đổi địa chỉ liên tục, tỷ lệ trợ giá voucher, luật tích cực khách mua đều).
  - Đổi mã TANTHU → NGUOIMOI, túi voucher (`user_vouchers`), cấp NGUOIMOI khi đăng ký.
- Lý do: một con số dễ hiểu cho Console, phản ứng theo bậc thay vì cho/chặn, bám đề cương, thêm góc nhìn tiền bạc (tỷ lệ trợ giá).
- Hệ quả / rủi ro:
  - Trên bộ mô phỏng, v3 cho kết quả **trùng hoàn toàn** với v2 (TEST_PLAN mục 3d): không bắt thêm, không nhầm thêm. Bộ mô phỏng không có hành vi chung SĐT hay "săn sale" nên R12, R14 chưa được đo.
  - Phát hiện trên tập test: luật theo đơn (R08 COD giá trị cao) kéo điểm tin cậy của khách mới hợp lệ xuống ~30. Đề xuất v3.1: chỉ tính các luật "về tài khoản" vào lớp 1; muốn đổi phải đo lại trên tập test mới.
