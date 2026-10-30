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
