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

## ADR-010: Tự động khóa quyền mua hàng khi cố đặt lặp sau nhiều lần bị từ chối
- Ngày: 2026-10-31
- Trạng thái: Accepted
- Bối cảnh: chưa có tình huống nào hệ thống ra quyết định CHẶN. Luca muốn tài khoản cố đặt hàng lặp lại sau khi bị từ chối bị khóa mua, tự động hoàn toàn. Giao diện đã ẩn COD / gỡ mã ngay khi bị từ chối, nên gửi lại đúng thứ đã bị từ chối nhiều lần gần như chắc chắn là gọi API trực tiếp hoặc dùng công cụ.
- Các phương án:
  - (1) Ban vô thời hạn ngay khi vượt ngưỡng: đúng ý ban đầu, nhưng một lỗi (mạng gửi lặp, lỗi giao diện) cũng thành khóa vĩnh viễn.
  - (2) Khóa có bậc, tự động: lần đầu khóa 24 giờ, tái phạm trong 30 ngày thì khóa vô thời hạn; gỡ được qua khiếu nại hoặc Risk Manager.
  - (3) Chỉ mở case, người quyết định khóa: an toàn nhất nhưng không tự động.
- Quyết định: (2), Luca chọn.
  - Ngưỡng: lần đặt hàng bị từ chối thứ 4 trong 24 giờ (đếm từ lần khóa gần nhất; các lần bị chặn vì đang khóa không được đếm).
  - Chỉ khóa **quyền mua hàng**; khách vẫn đăng nhập, xem đơn, khiếu nại.
  - Bảng `account_restrictions`: không xóa, chỉ đánh dấu gỡ (ai, khi nào, lý do). Audit `account.restrict` / `account.unrestrict`.
- Lý do: tự động hoàn toàn như yêu cầu, có phản ứng theo bậc, và không có quyết định nào không đảo ngược được (người bị quyết định tự động có đường để con người xem xét lại).
- Hệ quả / rủi ro:
  - Khách thật bấm lặp do lỗi có thể bị khóa 24 giờ; giảm thiểu: thông điệp hướng dẫn khiếu nại, Risk Manager gỡ được.
  - Kẻ gian có thể tạo tài khoản mới sau khi bị khóa: khóa theo tài khoản, chưa theo thiết bị (hướng phát triển: đưa "thiết bị từng gắn với tài khoản bị khóa" thành dấu hiệu trừ điểm tin cậy).

## ADR-011: Truy vết và khóa tài khoản mới né lệnh khóa
- Ngày: 2026-10-31
- Trạng thái: Accepted
- Bối cảnh: tài khoản bị khóa vô thời hạn (ADR-010) có thể tạo tài khoản mới để tiếp tục spam mã người mới. Luca đề xuất khóa thanh toán 1–2 tháng cho tài khoản mới có dấu hiệu này và truy vết qua thiết bị, SĐT, thẻ/tài khoản ngân hàng.
- Các phương án:
  - (1) Khóa mọi tài khoản dùng chung bất kỳ điểm nào với tài khoản bị ban: bắt oan người nhà dùng chung máy, quán net, Wi-Fi công cộng.
  - (2) Theo mức liên kết: chung IP không tính; chung 1 điểm mạnh → trừ điểm tin cậy + mở case; chung ≥ 2 điểm, hoặc 1 điểm + spam mã người mới → khóa thanh toán có thời hạn.
- Quyết định: (2). Khóa 30 ngày, tái phạm 60 ngày; chỉ tài khoản đang bị ban làm nguồn (không lây dây chuyền); cửa sổ 90 ngày (SĐT có thể bị nhà mạng cấp lại). Thêm khóa vô thời hạn thủ công cho Risk Manager/Admin (bắt buộc lý do, audit `account.ban`).
- Lý do: kết hợp liên kết với hành vi thay vì chỉ liên kết; đúng nguyên tắc "không chặn chỉ dựa vào IP hoặc chỉ dựa vào thiết bị"; lý do khóa ghi rõ tài khoản và loại điểm chung để giải thích và khiếu nại.
- Hệ quả / rủi ro:
  - Thẻ / tài khoản ngân hàng: chưa làm được vì thanh toán là giả lập. Hướng phát triển: dùng "dấu vân tay thẻ" (fingerprint) do cổng thanh toán trả về, không bao giờ lưu số thẻ (PCI DSS).
  - Kẻ gian đổi cả máy, SĐT và địa chỉ thì không truy vết được bằng luật; chỉ còn đồ thị liên kết và hành vi.
  - Sửa kèm: lệnh khóa đã được người gỡ (xác định nhầm) không còn tính là "tái phạm" khi xét khóa vô thời hạn.

## ADR-012: Bộ luật v3.1 — luật chỉ mô tả đơn đang đặt không trừ vào điểm tin cậy tài khoản
- Ngày: 2026-11-03
- Trạng thái: Accepted (Luca duyệt 2026-11-03; muốn quay về v3 chỉ cần bỏ khóa `exclude_rules` trong `TRUST`)
- Bối cảnh: đo bộ luật v3 (TEST_PLAN 3d) cho thấy khách mới hợp lệ mua COD giá trị cao có điểm tin cậy thấp hơn cả farm (trung vị 30), vì R08 "COD giá trị cao, ít lịch sử" bị cộng vào điểm TÀI KHOẢN. R08 không nói gì về con người, chỉ nói về đơn đang đặt (giá trị, phương thức). Điểm tin cậy bị kéo xuống thì khách đó bị khóa mã GIAM10 / NGUOIMOI, bị mở case ở các lần sau.
- Các phương án:
  - (1) Giữ v3: đơn giản, nhưng điểm tin cậy lẫn "đơn này rủi ro" với "người này đáng ngờ"; giải thích với khách khó.
  - (2) Hạ điểm R08: giảm cả khả năng giữ đơn COD rủi ro ở lớp giao dịch, tức là sửa sai chỗ.
  - (3) Thêm danh sách luật giao dịch được loại khỏi điểm tin cậy (`trust.exclude_rules` trong ma trận quyết định), lúc đầu chỉ có R08. R08 vẫn tính vào điểm COD của chính đơn đó (vẫn giữ đơn chờ xác minh).
- Quyết định: (3).
- Lý do: tách rõ hai lớp của ADR-009 (lớp 1 = tài khoản, lớp 2 = giao dịch); là cấu hình, có phiên bản, có dấu vân tay trong báo cáo thực nghiệm; không đổi khả năng phát hiện.
- Kết quả đo (tập test_v2 seed 5, seed chưa dùng, mỗi phiên bản chạy một lần; v3 chạy bằng cờ `--trust-all-rules` trên cùng dân số):
  - Precision, recall, FPR **không đổi** (75,7% / 38,4% / 6,2%).
  - Khách mới mua COD giá trị cao: trung vị điểm tin cậy 60 → 100; số tài khoản dưới 50 điểm 3/10 → 0/10. Các nhóm khác không đổi.
  - Đơn của nhóm này vẫn bị giữ chờ xác minh 100% (đúng thiết kế fail-closed của lớp giao dịch).
- Hệ quả / rủi ro:
  - Kẻ gian dùng đơn COD giá trị cao không còn bị trừ điểm tài khoản vì riêng R08; vẫn bị giữ đơn, và R07 / R10 (lịch sử COD) vẫn trừ điểm.
  - Luật giao dịch mới thêm sau này phải được xếp loại (tài khoản hay giao dịch) khi viết luật (cập nhật skill `risk-rule`).
  - Giả định chưa kiểm chứng: các luật còn lại đều mô tả tài khoản; R05 (thử mã liên tục) và R06 (tốc độ như bot) là hành vi theo phiên, có thể cần xem lại.

## ADR-013: R16 chỉ trừ điểm tin cậy; khóa kẻ né lệnh khóa ở bước đặt hàng
- Ngày: 2026-11-03
- Trạng thái: Accepted (Luca chọn 2026-11-03; sửa phần cài đặt của ADR-011, phần quy tắc khóa của ADR-011 giữ nguyên)
- Bối cảnh: đo O7 (TEST_PLAN 3h) cho thấy cài đặt khác thiết kế ADR-011. ADR-011 định "chung 1 điểm → chỉ trừ điểm tin cậy + mở case", nhưng R16 (+45) cộng thẳng vào điểm voucher / COD, nên 7/8 người nhà dùng chung máy bị gỡ mã và tắt COD. Cùng lúc, kẻ né khóa bị gỡ mã ngay ở bước áp mã (lúc đó mới thấy 1 điểm là thiết bị), bỏ đơn, không tới bước đặt hàng nơi có đủ ≥ 2 điểm để bị khóa: chỉ 46,7% bị khóa.
- Các phương án:
  - (1) Khóa ngay ở bước áp mã khi chung máy với tài khoản bị khóa và đang dùng mã người mới: khóa được nhiều hơn, nhưng ở bước này người nhà và kẻ né khóa giống hệt nhau, người nhà bị khóa thanh toán 30 ngày.
  - (2) R16 chỉ trừ điểm tin cậy (contexts rỗng, không cộng vào điểm giao dịch), hạ bậc 1 điểm chung từ 45 xuống 35 để tài khoản mới (R01 −10) vẫn còn ≥ 50 = `min_trust` của NGUOIMOI. Kẻ né khóa đi tiếp tới bước đặt hàng và bị khóa khi chung ≥ 2 điểm.
- Quyết định: (2). Điều kiện khóa của ADR-011 không đổi (≥ 2 điểm, hoặc 1 điểm + spam mã người mới).
- Lý do: đúng ý thiết kế ADR-011; ưu tiên không phạt nhầm người nhà; bằng chứng đầy đủ nhất có ở bước đặt hàng. Con số 35 chọn bằng lập luận trên dev_v3, không chỉnh theo tập test.
- Kết quả đo (test_v3 seed 7, seed mới, chạy một lần; so với seed 6 ở TEST_PLAN 3h là so khác dân số, chỉ mang tính tham khảo):
  - Né khóa chung ≥ 2 điểm: bị khóa 10/15 = 66,7% (seed 6: 46,7%); vẫn 100% bị gắn cờ, 0 mã bị lấy.
  - Người nhà dùng chung máy: 0/8 bị hạn chế (seed 6: 7/8).
  - Đánh đổi đã biết trước: biến thể "chỉ giữ SĐT cũ" (1 điểm, không spam) giờ lấy được mã 6/6 (seed 6: 0/6). Theo ADR-011 trường hợp này chỉ mở case; analyst là lớp xử lý.
- Hệ quả / rủi ro:
  - O7 (≥ 90% bị khóa) vẫn chưa đạt. Phần còn lại: kẻ né khóa thao tác như bot (R06) bị điểm tin cậy kéo xuống dưới 50, bị gỡ mã ở bước áp mã rồi bỏ đơn: không lấy được lợi ích nhưng không bị ghi lệnh khóa.
  - R16 không còn xuất hiện trong danh sách "luật khớp" của giao dịch, chỉ trong "sổ trừ điểm"; lý do khóa vẫn ghi rõ tài khoản và loại điểm chung. Trang Luật hiển thị "chỉ điểm tin cậy tài khoản".
  - Seed đổi luôn: phiên bản luật mới tạo từ seed lấy ghi chú `note` của luật làm lý do thay đổi.

## ADR-014: Bùng hàng COD lịch sử ngắn và tài khoản mới treo nhiều đơn COD
- Ngày: 2026-11-05
- Trạng thái: Accepted (Luca chọn ngưỡng R17 = 2 đơn treo ngày 2026-11-05, duyệt toàn bộ ADR ngày 2026-11-06)
- Bối cảnh: thí nghiệm baseline (TEST_PLAN 3j) cho thấy Risk Engine chỉ bắt 6/15 kẻ bùng hàng COD, trong khi luật thủ công bắt 15/15. Nguyên nhân: R07 dùng tỷ lệ thất bại làm mượt (cộng thêm 10 đơn giả định, 10% thất bại), kẻ có 2/3 hoặc 3/5 đơn thất bại chỉ còn 0,23–0,29, rơi vào bậc 0,20 (+25), chưa đủ ngưỡng ẩn COD (40). Ngoài ra "tài khoản mới treo nhiều đơn COD" (cod_hoarder) chưa bao giờ bị bắt: R10 cần ≥ 3 đơn treo và chỉ +25.
- Các phương án:
  - (1) Bỏ làm mượt, dùng tỷ lệ thô như luật thủ công: bắt hết kẻ ít đơn, nhưng phạt khách quen vì một lần giao thất bại (luật thủ công bắt nhầm 30/40 khách quen).
  - (2) Giữ làm mượt, nâng bậc 0,20 của R07 từ +25 lên +40 để bậc này tự đủ ẩn COD. Bậc 0,20 = gấp đôi mức nền 10%; muốn chạm cần ≥ 2 lần thất bại trên ≤ 5 đơn, hoặc ≥ 3 trên ≤ 10 đơn. Khách quen có 1 lần thất bại không chạm.
  - (3) Thêm luật mới R17 `COD_OPEN_NEW_ACCOUNT`: tài khoản chưa có đơn giao thành công nào và đã có ≥ 2 đơn COD đang chờ giao → +40 (đơn COD thứ 3 phải trả trước). Độ mạnh vừa: chỉ ẩn COD, không giữ hay chặn đơn; không trừ điểm tin cậy (cùng lý do ADR-012). Biến thể ngưỡng 3 đơn treo cũng được đo.
- Quyết định: (2) + (3) với ngưỡng 2 đơn treo (Luca chọn).
- Lý do: giữ nguyên tắc không phạt khách quen vì một lần (ADR-009) mà vẫn chặn kẻ có lịch sử ngắn; hành động nhẹ (vẫn mua được bằng trả trước) nên cái giá của bắt nhầm thấp. Số điểm và ngưỡng chọn trên dev_v4, không chỉnh theo tập test.
- Dữ liệu: thêm bộ dev_v4 / test_v4, định nghĩa trước khi đổi luật: dev có thêm cod_hoarder; hard negative MỚI `new_multi_cod` (khách mới hợp lệ đặt 2–4 đơn COD liền nhau và nhận đủ hàng), là người dễ bị R17 bắt nhầm nhất.
- Kết quả đo:
  - dev_v4 seed 1, trước → sau: bùng hàng 7/12 → 12/12; treo đơn 0/5 → 5/5; khách mới đặt nhiều đơn COD 0/8 → 5/8 phải trả trước ở đơn thứ 3; FPR hard negative 14,5% → 21,1%; F1 67,1% → 73,2%. Ngưỡng 3 đơn treo: treo đơn 3/5, khách mới 0/8, F1 73,9%.
  - test_v4 seed 9 (seed mới, chạy một lần, dấu vân tay `e0240c5bbcce8604…`): bùng hàng 15/15; treo đơn 6/6; khách mới đặt nhiều đơn COD 7/12 phải trả trước; khách quen 0/40. Precision 78,5%, recall 54,0%, F1 64,0%, FPR 8,4%. Luật thủ công cùng lần chạy: F1 49,5%, FPR 12,0%.
- Hệ quả / rủi ro:
  - Khách mới mua nhiều đợt liền nhau phải trả trước từ đơn thứ 3 cho tới khi nhận được đơn đầu tiên: đánh đổi có chủ đích, cần ghi trong thông điệp và chính sách.
  - Kẻ treo đơn vẫn treo được 2 đơn COD trước khi bị chặn.
  - Bộ luật có 17 luật; RULES_V0 cập nhật R07 và R17.
