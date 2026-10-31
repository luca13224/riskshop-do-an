# DÀN Ý BÁO CÁO ĐỒ ÁN TỐT NGHIỆP

> Bản dàn ý v1 (2026-10-31). **Cần xác nhận với GVHD:** mẫu trình bày của Khoa (số chương, cỡ chữ, cách đánh số hình/bảng), số trang mong muốn, và các điều chỉnh so với đề cương (mục 0).
> Ký hiệu nguồn: **[docs]** viết lại từ tài liệu đã có trong repo · **[đo]** số liệu đã đo, có file kết quả · **[XM]** cần tìm và kiểm chứng tài liệu tham khảo thật, KHÔNG bịa · **[viết mới]** chưa có tư liệu.
> Hình vẽ: **[A]** vẽ bằng Archify (`.claude/skills/archify`, HTML tương tác + xuất PNG) · **[UI]** chụp màn hình sản phẩm.

**Tên đề tài:** Xây dựng hệ thống kiểm soát rủi ro và ngăn ngừa lạm dụng chính sách trên sàn thương mại điện tử.

---

## 0. Việc cần làm TRƯỚC khi viết: thống nhất điều chỉnh so với đề cương
Đề cương ban đầu và sản phẩm thực tế khác nhau ở nhiều điểm. Báo cáo phải giải trình (Mở đầu, mục "Điều chỉnh so với đề cương") và nên trao đổi với GVHD trước.

| Đề cương | Thực tế | Lý do (nguồn) |
|---|---|---|
| React + FastAPI + **MongoDB**, Redis, Celery | React + FastAPI + **MariaDB**, hàng đợi việc nền tự viết (`SKIP LOCKED`) | Dữ liệu đơn hàng, voucher cần giao dịch ACID và ràng buộc; giảm số hạ tầng phải vận hành (ADR-003, review mục 1.2) |
| **Trust Score** một công thức T(u,t), trọng số 35/25/25/15, bán rã 14 ngày | Điểm **riêng theo từng chính sách** (voucher, COD), luật có phiên bản, ma trận quyết định; REVIEW/BLOCK bắt buộc có luật mạnh | Trọng số trong đề cương chưa có cơ sở; tách theo chính sách thì hành động hợp lý hơn (RULES_V0) |
| Luồng bất đồng bộ đẩy vùng 40–70 sang **AI/LLM** tóm tắt | Không dùng LLM; giải thích bằng luật đã khớp + giá trị thực tế | Quyết định phải đồng bộ tại checkout; giải thích bằng luật kiểm chứng được (review mục 1.2, tiêu chí 8) |
| 4 loại lạm dụng (gồm cước vận chuyển) | 2 nhóm chính sách: **voucher tân thủ** và **COD** | Đủ sâu trong 2 tháng; demo và thực nghiệm làm được trọn vẹn |
| p95 ≤ 45 ms | p95 chấm điểm ~8–12 ms **[đo]** (một tiến trình, tuần tự, không phải đo tải) | `docs/experiments/` |
| FPR ≤ 5% | Tổng: dev 4,7%, **test 7,9%**; khách thường 0%; hard negative 19,5% / 31,2% **[đo]** | Nói thẳng là chưa đạt ở tập test; khiếu nại (ADR-006) là biện pháp giảm thiệt hại |
| Bộ 16 biến thể | Simulator 7–9 persona, có hard negative và 2 biến thể chưa biết, tách dev/test | TEST_PLAN mục 2 |

---

## Phần mở đầu (~4–5 trang)
- Lời cam đoan, lời cảm ơn, mục lục, danh mục hình, bảng, từ viết tắt (theo mẫu Khoa).
- **Lý do chọn đề tài:** voucher tân thủ và COD là công cụ hút khách phổ biến của TMĐT Việt Nam; lạm dụng (farm tài khoản, bùng hàng COD) gây thiệt hại; kiểm tra thủ công không theo kịp. **[XM]** số liệu thị trường TMĐT, tỷ lệ COD, tình trạng bùng hàng (chỉ dùng nguồn kiểm chứng được, ví dụ báo cáo của Bộ Công Thương / VECOM).
- **Mục tiêu:** 4 mục tiêu trong PROJECT_OVERVIEW mục 3, viết lại khớp với sản phẩm cuối.
- **Đối tượng, phạm vi:** 2 nhóm chính sách; dữ liệu mô phỏng; không có thanh toán thật, không triển khai production.
- **Phương pháp:** phân tích nghiệp vụ → thiết kế (kịch bản demo trước, ADR) → xây dựng theo module → kiểm thử tự động → thực nghiệm mô phỏng tách dev/test.
- **Điều chỉnh so với đề cương:** bảng ở mục 0.
- **Bố cục báo cáo.**

## Chương 1. Tổng quan và cơ sở lý thuyết (~12–15 trang)
1.1. **Lạm dụng chính sách trong TMĐT:** định nghĩa; phân biệt với gian lận thanh toán; các dạng: farm tài khoản gom voucher, bùng hàng COD, gian lận hoàn tiền. **[XM]** tài liệu về promotion abuse / fraud trong TMĐT.
1.2. **Các hướng tiếp cận phát hiện:** luật (rule-based), chấm điểm thống kê, học máy (có giám sát, phát hiện bất thường), phân tích đồ thị liên kết. So sánh ưu nhược: khả năng giải thích, cần nhãn, chi phí vận hành. **[XM]**
1.3. **Hệ thống ra quyết định rủi ro thời gian thực:** điểm kiểm soát trong luồng mua hàng; fail-open / fail-closed; human-in-the-loop; case management; khiếu nại. **[XM]** + **[docs]** RULES_V0.
1.4. **Nhận diện thiết bị và mạng:** ID thiết bị trong trình duyệt, IP, giới hạn và sai số (dùng chung Wi-Fi, NAT). **[XM]**
1.5. **Đánh giá hệ thống phát hiện:** confusion matrix, precision, recall, FPR; khoảng tin cậy Wilson; vì sao phải tách tập tinh chỉnh và tập kiểm thử; hard negative. **[XM]** tài liệu thống kê cho Wilson interval.
1.6. **Quyền riêng tư và an toàn:** privacy-by-design, tối thiểu hóa dữ liệu, che PII, băm IP bằng HMAC, audit log, phân quyền tối thiểu. **[XM]** Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân (kiểm tra số hiệu, nội dung trước khi trích).
1.7. **Công nghệ sử dụng:** FastAPI, SQLAlchemy, Alembic, MariaDB, React, TypeScript, Vite, Tailwind, TanStack Query; lý do chọn (ngắn gọn, dẫn ADR-003).
1.8. Tiểu kết.

## Chương 2. Phân tích và thiết kế hệ thống (~20–25 trang)
2.1. **Bài toán nghiệp vụ và tác nhân:** khách hàng, Analyst, Risk Manager, Admin; quy trình mua hàng có kiểm soát rủi ro. **[docs]** DEMO_SCRIPT. Hình: quy trình nghiệp vụ tổng thể **[A] workflow**.
2.2. **Yêu cầu chức năng và phi chức năng:** bảng yêu cầu. **[viết mới]** từ DEMO_SCRIPT "Phạm vi MVP" (REQUIREMENTS.md đang trống, cần bổ sung). Biểu đồ use case **[viết mới]** (Archify không vẽ use case UML: dùng PlantUML hoặc draw.io).
2.3. **Kiến trúc tổng thể:** modular monolith; các module và ranh giới; worker; Risk đọc chỉ đọc qua feature store. **[docs]** ARCHITECTURE, ADR-003, ADR-004. Hình: kiến trúc **[A] architecture** (vẽ từ mã nguồn).
2.4. **Thiết kế Risk Engine:**
  - 3 điểm kiểm soát: áp voucher, chọn thanh toán, đặt hàng. Hình: tuần tự đặt hàng có chấm điểm **[A] sequence**.
  - Đặc trưng F01–F11, 10 luật R01–R10, 3 kiểu luật, điểm theo chính sách, ma trận quyết định, fail-open/closed. **[docs]** RULES_V0. Bảng luật + bảng ma trận.
  - Phiên bản luật, quyết định và rule hit bất biến.
  - Danh sách miễn trừ sau khiếu nại (ADR-006).
2.5. **Thiết kế xử lý case và khiếu nại:** vòng đời case **[A] lifecycle**; quy trình khiếu nại, bốn mắt **[A] workflow**.
2.6. **Đồ thị liên kết tài khoản:** mô hình hai loại nút, duyệt 2 bước, cửa sổ 30 ngày, che PII. **[docs]** `risk/graph.py`.
2.7. **Thiết kế cơ sở dữ liệu:** ERD theo nhóm, ràng buộc quan trọng (UNIQUE chống trùng, `open_key`), index theo đặc trưng, dữ liệu cá nhân. **[docs]** ERD.md. Hình: ERD **[A] erd**.
2.8. **Thiết kế bảo mật và quyền riêng tư:** phiên đăng nhập, RBAC, che email, xem liên hệ có lý do + audit, giới hạn đăng nhập sai, băm IP. **[docs]** PROGRESS_LOG, ERD mục 6.
2.9. **Thiết kế giao diện:** nguyên tắc (ADR-005), Shop tông sáng, Console dark navy; bố cục dashboard và lý do. **[UI]**
2.10. Tiểu kết.

## Chương 3. Xây dựng hệ thống (~12–15 trang)
3.1. Môi trường, cấu trúc mã nguồn, quy trình Git, CI (GitHub Actions).
3.2. Shop: danh mục, giỏ, checkout một giao dịch (khóa tồn kho, idempotency). **[UI]**
3.3. Risk Engine: feature store, đánh giá luật, ghi quyết định. Trích đoạn code ngắn có giải thích.
3.4. Risk Console: dashboard, Live Monitor, case, khiếu nại, đồ thị liên kết, luật, Attack Lab, báo cáo, audit. **[UI]** mỗi màn hình một hình.
3.5. Việc nền (worker), demo reset, sinh lịch sử mô phỏng.
3.6. Kiểm thử tự động: 157 test; nhóm test theo module; chạy trên MariaDB thật; CI. **[đo]**
3.7. Tiểu kết.

## Chương 4. Thực nghiệm và đánh giá (~10–12 trang)
4.1. **Thiết kế thực nghiệm:** persona, hard negative, biến thể chưa biết; tách dev/test; quy tắc chống học thuộc; đơn vị đo. **[docs]** TEST_PLAN mục 2.
4.2. **Kết quả:** confusion matrix, precision/recall/FPR kèm KTC 95%, theo persona, theo nhóm. **[đo]** `docs/experiments/*.md`.
4.3. **Độ trễ:** p50/p95/p99 chấm điểm và request; nói rõ là đo tuần tự một tiến trình. **[đo]**
4.4. **Phân tích lỗi:**
  - Biến thể chưa biết lọt 0/33. Farm phân tán chỉ có 1 tín hiệu chung (địa chỉ), tổng 40 < 50; đồ thị liên kết nhìn ra được cụm.
  - Gia đình đông người bị gỡ voucher (FPR hard negative 31,2%); khách mới COD giá trị cao luôn bị giữ (đánh đổi có chủ đích).
  - Bùng hàng lịch sử ngắn lọt.
4.5. **Đánh giá theo mục tiêu đề cương:** đạt / chưa đạt từng chỉ tiêu (bảng mục 0).
4.6. **Kịch bản demo:** 10 cảnh (DEMO_SCRIPT) như minh chứng chức năng. **[UI]**
4.7. Tiểu kết.

## Kết luận và hướng phát triển (~2–3 trang)
- Kết quả đạt được (3–5 ý).
- Hạn chế: dữ liệu mô phỏng, thời gian bị nén, luật có thể bị lách, ID thiết bị không phải fingerprint thật, chưa đo tải.
- Hướng phát triển (cập nhật 2026-10-31; luật v2 cụm địa chỉ và Trust Score v3 đã làm):
  - **v3.1:** tách luật "về tài khoản" và "về giao dịch", chỉ luật tài khoản tính vào điểm tin cậy (ADR-009); đo lại trên tập test mới.
  - **Chế độ bóng (shadow mode)** cho luật mới; **xác minh thêm (OTP)** thay cho gỡ mã ngay khi điểm tin cậy thấp.
  - **Đổi chính sách thay vì bắt người:** mã người mới giới hạn theo SĐT nhận hàng.
  - **Lan truyền rủi ro trên đồ thị:** khoảng cách tới tài khoản đã xác nhận lạm dụng; thêm nút SĐT nhận hàng.
  - **Học máy khi có nhãn thật:** hồi quy logistic (giải thích được) học điểm từ kết quả case; Isolation Forest chỉ để gợi ý cho analyst.
  - **Tách Risk Engine thành dịch vụ dùng lại được:** API có phiên bản + khóa, API nhận sự kiện, plugin WooCommerce (ARCHITECTURE.md mục 6).
  - **Luồng tranh chấp có bằng chứng video** (ý tưởng của Luca): shop quay lúc đóng gói, shipper chụp lúc bàn giao, khách quay lúc mở hàng; bằng chứng gắn vào khiếu nại "hàng sai/thiếu". Băm SHA-256 và ghi dấu thời gian ở server lúc tải lên để phát hiện chỉnh sửa; chính sách ai được xem, lưu bao lâu, sự đồng ý của người bị quay. Web làm được (ô tải file `capture` hoặc `getUserMedia` + `MediaRecorder`, cần HTTPS) nhưng khó bắt buộc quay trực tiếp và chống chỉnh sửa như app. Cần module đổi trả/hoàn tiền trước; sau đó thêm luật "khiếu nại hàng sai nhiều lần" vào Trust Score. Không dùng thị giác máy tính để tự kiểm hàng.
  - Thẻ / tài khoản ngân hàng dùng chung (cần thanh toán thật); SSE cho Live Monitor; trợ lý tóm tắt case cho analyst (có người duyệt).

## Tài liệu tham khảo
**[XM]** Chỉ đưa tài liệu đã đọc và kiểm chứng được. Đề cương hiện có 2 tài liệu (VECOM EBI 2023; một tài liệu về phát hiện bất thường luồng mạng), cần khoảng 10–15 tài liệu: sách hoặc bài báo về fraud detection, đánh giá mô hình phân loại, link analysis; văn bản pháp luật về dữ liệu cá nhân; tài liệu chính thức của FastAPI, SQLAlchemy, React, MariaDB.

## Phụ lục
- A. Danh sách luật R01–R10 đầy đủ (tham số, điểm, lý do).
- B. Từ điển dữ liệu (ERD.md).
- C. Danh sách API.
- D. Kết quả thực nghiệm chi tiết (`docs/experiments/`).
- E. Danh sách ADR-001 đến ADR-006.
- F. Hướng dẫn cài đặt và chạy (README).

---

## Danh sách hình dự kiến
| Mã | Hình | Cách làm | Trạng thái |
|---|---|---|---|
| H2.1 | Quy trình mua hàng có kiểm soát rủi ro | [A] workflow | Chưa |
| H2.2 | Biểu đồ use case | PlantUML / draw.io | Chưa |
| H2.3 | Kiến trúc tổng thể (modular monolith) | [A] architecture | **Làm ngay** |
| H2.4 | Tuần tự: đặt hàng có chấm điểm rủi ro | [A] sequence | **Làm ngay** |
| H2.5 | Vòng đời case | [A] lifecycle | Chưa |
| H2.6 | Quy trình khiếu nại | [A] workflow | Chưa |
| H2.7 | ERD | [A] erd | Chưa |
| H3.x | Ảnh chụp các màn hình Shop và Console | [UI] | Chưa |
| H4.x | Biểu đồ kết quả thực nghiệm | Từ `docs/experiments/*.json` | Chưa |

## Ước lượng
Khoảng 60–75 trang chính văn. Thứ tự viết đề xuất: Chương 2 → 3 → 4 (đã có sẵn tư liệu) → Chương 1 (cần tìm tài liệu) → Mở đầu, Kết luận (viết sau cùng).
