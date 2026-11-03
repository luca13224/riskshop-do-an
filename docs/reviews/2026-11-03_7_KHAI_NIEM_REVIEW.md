# Rà soát đồ án theo khung 7 khái niệm (Nhánh A — đang làm)

> Ngày: 2026-11-03 · Tư vấn, **chưa phải quyết định** (quyết định chỉ ở `docs/DECISIONS.md`).
> Nguồn: PROJECT_OVERVIEW, REQUIREMENTS, ROADMAP, TEST_PLAN, BAO_CAO_DAN_Y, DECISIONS (ADR-003 → ADR-011), INITIAL_REVIEW.
> Nhãn: **[ĐỀ XUẤT – cần xác nhận]** = Claude đề xuất, Luca chốt. **[CẦN ĐO]** = chưa có số.

## 0. Thông tin đầu vào (đã có trong repo, không cần dán lại)
- **Đề tài:** Xây dựng hệ thống kiểm soát rủi ro và ngăn ngừa lạm dụng chính sách trên sàn TMĐT.
- **Công nghệ:** FastAPI + SQLAlchemy + Alembic + MariaDB; React 19 + TypeScript + Vite + Tailwind + shadcn; worker tự viết; simulator Python.
- **Tiến độ sản phẩm:** ~85–90% (Shop, Risk Engine v3 có Trust Score, khóa tự động, truy vết né khóa, Case, Khiếu nại, Attack Lab, Báo cáo, 190 test qua). Báo cáo viết: ~10% (dàn ý + report tháng 10).
- **Thời gian:** mục tiêu nội bộ 30/11/2026; hạn nộp khoảng cuối 12/2026 (cần GVHD xác nhận).

## 1. Đánh giá 7 bước

| # | Khái niệm | Đánh giá | Nhận xét ngắn |
|---|---|---|---|
| 1 | Context | ⚠️ | Đúng hướng (voucher tân thủ, COD phổ biến ở TMĐT VN) nhưng **chưa có số liệu thị trường nào có nguồn**. Hội đồng sẽ hỏi "bao nhiêu % đơn là COD?". |
| 2 | Pain point | ⚠️ | Nêu được 3 nỗi đau (farm voucher, bùng COD, xử lý thủ công khó truy vết) nhưng chỉ định tính. Thiếu "hậu quả tính bằng tiền/thời gian" và thiếu nỗi đau thứ 4 mà sản phẩm thực ra đang giải: **chặn nhầm khách thật** và **né lệnh khóa bằng tài khoản mới**. |
| 3 | Objective | ❌ | 4 mục tiêu trong PROJECT_OVERVIEW **không có con số**. Chỉ tiêu cũ trong đề cương (p95 ≤ 45 ms, FPR ≤ 5%) bị chính review 30/10 chỉ ra là định nghĩa chưa đúng, nhưng chưa có bản thay thế. Đây là chỗ hở lớn nhất. |
| 4 | Constraint | ⚠️ | Ràng buộc có nhưng rải rác (không dữ liệu thật, 1 người, ~2 tháng, máy local, không thanh toán thật, Nghị định 13/2023 [XM]). Chưa gom thành mục và **chưa nối "vì ràng buộc này nên chọn rule-based / modular monolith"**. |
| 5 | Method | ✅ | Điểm mạnh nhất: 3 điểm kiểm soát, đặc trưng F01–F17, luật R01–R16 có phiên bản, điểm theo chính sách + Trust Score, ma trận quyết định, case/khiếu nại/audit, 11 ADR giải thích lựa chọn. |
| 6 | Evaluation | ⚠️ | Có số thật, tách dev/test, Wilson CI, có hard negative và biến thể chưa biết (tốt hơn mặt bằng chung). Thiếu: **so sánh với mục tiêu** (vì mục tiêu chưa có số), **đo tải đồng thời**, **đánh giá phía người dùng Console**, v3.1 chưa đo, R12/R14 chưa có số trong mô phỏng. |
| 7 | Impact | ⚠️ | Có trang "tác động nghiệp vụ ước tính" trong Console nhưng chưa có đoạn văn Impact quay lại từng pain point; khả năng mở rộng (tách Risk Engine thành dịch vụ độc lập/plugin) mới chỉ là ý tưởng đã thảo luận. |

Ngoài khung 7 bước: **`docs/REQUIREMENTS.md` vẫn trống** (FR/NFR/BR chưa đánh mã). Chương 2.2 báo cáo cần nó; ma trận truy vết cũng cần mã FR để trỏ về.

## 2. Kiểm tra chuỗi logic

| Kiểm tra | Kết quả |
|---|---|
| Mỗi Pain point có Objective? | ❌ Objective chưa có số nên chưa "khớp" được pain point nào một cách đo được. |
| Mỗi Objective có Method + Metric? | ⚠️ Method có đủ; Metric đã đo (precision, recall, FPR, p95) nhưng chưa gắn vào Objective cụ thể. |
| Constraint giải thích được Method? | ⚠️ Có lý do trong ADR (không nhãn thật → không ML có giám sát; 1 người → monolith) nhưng chưa viết thành chuỗi trong báo cáo. |
| Impact quay về Pain point? | ⚠️ Chưa viết. Có số đo để viết (ví dụ farm phân tán 0% → 37,5% bị bắt), nhưng tiền tiết kiệm chỉ là ước tính theo giả định. |

**Cảnh báo phương pháp (quan trọng):** số liệu đã đo trước khi đặt mục tiêu có số. Nếu bây giờ đặt mục tiêu "vừa khít" kết quả thì là dời cột gôn, hội đồng bắt được ngay. Cách trung thực: (a) giữ nguyên các chỉ tiêu trong đề cương, định nghĩa lại cho đo đúng, rồi báo cáo **đạt/chưa đạt**; (b) mục tiêu mới nào thêm vào thì ghi rõ "đặt ngày 03/11, sau lần đo v3" và kiểm trên **tập test mới (seed mới)**.

## 3. Bản nháp các bước còn thiếu

### 3.1 Context [ĐỀ XUẤT – cần xác nhận]
Sàn TMĐT dùng voucher người mới và thanh toán khi nhận hàng (COD) để hạ rào cản mua lần đầu. Hai chính sách này mở ra hai kiểu lạm dụng: tạo nhiều tài khoản để gom voucher, và đặt COD rồi từ chối nhận. Liên quan: người mua hợp lệ, người bán/sàn, đội vận hành rủi ro. **[XM]** tỷ lệ đơn COD và quy mô TMĐT VN — chỉ lấy từ Sách trắng TMĐT (Bộ Công Thương) hoặc báo cáo VECOM; chưa tra thì không ghi số.

### 3.2 Pain point [ĐỀ XUẤT – cần xác nhận]
| Mã | Vấn đề | Hậu quả |
|---|---|---|
| P1 | Farm tài khoản gom voucher người mới | Ngân sách khuyến mãi chảy vào kẻ lạm dụng, không tạo khách thật |
| P2 | Bùng hàng COD | Mất phí vận chuyển 2 chiều, hàng kẹt, người bán chịu rủi ro |
| P3 | Bị chặn thì tạo tài khoản mới làm lại | Lệnh khóa vô hiệu nếu chỉ khóa theo tài khoản |
| P4 | Kiểm tra thủ công, không nhất quán, khó truy vết | Mỗi người xử lý một kiểu, không giải thích được vì sao chặn |
| P5 | Chặn nhầm khách thật (gia đình chung Wi-Fi, khách mới mua COD giá trị cao) | Mất khách, khiếu nại, ảnh hưởng uy tín |

### 3.3 Objective có số [ĐỀ XUẤT – cần xác nhận]
Phạm vi: 2 nhóm chính sách (voucher tân thủ, COD), dữ liệu mô phỏng, chạy local.

| Mã | Mục tiêu | Chỉ số | Ngưỡng đề xuất | Ghi chú |
|---|---|---|---|---|
| O1 | Bắt lạm dụng kiểu đã biết | Recall kiểu đã biết, tập test | ≥ 80% | v1 test seed 2 đã đo 85,5% |
| O2 | Không làm phiền khách bình thường | FPR khách thông thường | ≤ 2% | đã đo 0% ở mọi lần |
| O3 | Hạn chế chặn nhầm ca khó | FPR hard negative | ≤ 20% | đã đo 18,2–31,2% → **có lần chưa đạt, ghi thẳng** |
| O4 | Giữ chỉ tiêu FPR tổng của đề cương | FPR toàn bộ tài khoản hợp lệ | ≤ 5% | test v1 đã đo 7,9% → **chưa đạt** |
| O5 | Không làm chậm checkout | p95 chấm điểm Risk Engine; p95 request đặt hàng ở 1/10/50 người đồng thời | ≤ 50 ms (chấm điểm) | mức tải đồng thời **[CẦN ĐO]** |
| O6 | Quyết định giải thích được, truy vết được | % quyết định REVIEW/BLOCK có rule hit + giá trị đặc trưng + audit | 100% | kiểm bằng script **[CẦN ĐO]** |
| O7 | Lệnh khóa không bị né bằng tài khoản mới | % tài khoản né khóa (chung ≥ 2 điểm) bị khóa thanh toán | ≥ 90% kịch bản test | test tự động có, mô phỏng **[CẦN ĐO]** |
| O8 | Khách bị chặn nhầm có đường sửa sai | % quyết định hạn chế có nút khiếu nại; khiếu nại được chấp nhận thì tự gỡ | 100% | có test, nêu trong báo cáo |
| O9 | Analyst xử lý case nhanh và nhất quán | Thời gian trung vị xử lý 1 case; độ đồng thuận giữa người xử lý | **[CẦN ĐO]**, đặt ngưỡng trước khi đo, ví dụ ≤ 2 phút | xem kịch bản E4 |

### 3.4 Constraint [ĐỀ XUẤT – cần xác nhận]
| Ràng buộc | Hệ quả lên lựa chọn |
|---|---|
| Không có dữ liệu gian lận thật, không có nhãn | Không dùng ML có giám sát làm lõi → rule-based + mô phỏng có nhãn; ML/đồ thị là hướng phát triển |
| 1 người, ~2 tháng | Modular monolith, 1 CSDL, không Redis/Celery (ADR-003) |
| Quyết định phải đồng bộ tại checkout | Không dùng LLM trong luồng chính; giải thích bằng luật đã khớp |
| Dữ liệu cá nhân (Nghị định 13/2023 [XM]) | Che email, băm IP, xem liên hệ phải ghi lý do + audit |
| Chạy local, không thanh toán thật | Thanh toán trả trước giả lập; độ trễ đo trên 1 máy, không phải đo tải production |
| Giới hạn của IP/thiết bị | Không khóa theo IP (ADR-011), chỉ khóa khi trùng ≥ 2 điểm hoặc có spam |

### 3.5 Impact [ĐỀ XUẤT – cần xác nhận]
- **Sàn/người bán:** giảm voucher bị gom (P1), giảm đơn COD rủi ro (P2). Số tiền chỉ là **ước tính theo giả định** (giá trị voucher × tài khoản lạm dụng bị chặn − doanh thu mất do chặn nhầm), không phải số thật.
- **Đội rủi ro:** mỗi quyết định có lý do, case gom theo cụm, audit đầy đủ (P4).
- **Khách thật:** bị hạn chế theo bậc thay vì chặn cứng, có khiếu nại (P5).
- **Mở rộng:** Risk Engine đã tách module, có thể đóng gói thành dịch vụ độc lập gắn vào sàn khác (WordPress/WooCommerce là Advanced-Optional); thêm chính sách mới (hoàn tiền) bằng luật dạng dữ liệu.

## 4. Kịch bản đo cho bước Evaluation (Luca tự chạy, lấy số thật)

| Mã | Đo cái gì | Công cụ | Số lần | So với |
|---|---|---|---|---|
| E1 | v3.1 (tách luật tài khoản / luật giao dịch): precision, recall, FPR hard negative, trust trung vị khách mới COD | `simulator --dataset test_v2 --seed 5` (seed **chưa dùng**) | dev_v2 để chỉnh, test seed 5 chạy **1 lần** sau khi khóa luật | v3 trên cùng seed 5 (tắt bằng cờ) |
| E2 | Độ trễ đặt hàng khi đồng thời | Script Python `httpx` + `asyncio` gọi API checkout (tự viết, ~50 dòng) | 3 mức: 1 / 10 / 50 người, mỗi mức 3 lần × 200 request | O5; ghi rõ cấu hình máy |
| E3 | Tính đầy đủ của giải thích và audit | Script SQL đối chiếu `risk_decisions` ↔ `rule_hits` ↔ `audit_logs` | 1 lần sau mỗi lần mô phỏng | O6 = 100% |
| E4 | Thời gian xử lý case | 3–5 bạn cùng lớp, mỗi người xử lý 5 case trên Console, bấm giờ; mỗi case cho 2 người để so kết luận | 1 buổi ~30 phút | O9; đặt ngưỡng **trước** buổi đo |
| E5 | Né lệnh khóa | Thêm persona "evader" vào test_v2 (tài khoản mới chung thiết bị/SĐT với tài khoản bị ban) | cùng lần chạy E1 | O7 |
| E6 | Ablation từng luật | `--disable-rule` từng luật một trên dev_v2 | 1 lần mỗi luật | Cho biết luật nào thực sự đóng góp, luật nào thừa |

## 5. Việc cần làm nốt

| Việc | Đầu ra | Ưu tiên | Ước tính |
|---|---|---|---|
| Viết lại Objective có số, chốt với GVHD | Bảng O1–O9 trong PROJECT_OVERVIEW + Mở đầu báo cáo | Cao | 2 giờ |
| Điền REQUIREMENTS.md (FR/NFR/BR có mã) | Bảng yêu cầu cho Chương 2.2 | Cao | 4 giờ |
| Tra 2–3 nguồn số liệu thật cho Context | Đoạn văn "Lý do chọn đề tài" có trích dẫn | Cao | 3 giờ |
| Bảng "Mục tiêu → Kết quả → Đạt/Chưa đạt" | Bảng trong Chương 4 | Cao | 1 giờ (sau E1, E2) |
| Chạy E1 (v3.1) + E5 | Số mới trong TEST_PLAN | TB | 1 ngày |
| Chạy E2 (đo tải) | Bảng p50/p95/p99 theo mức tải | TB | 0,5 ngày |
| Script E3 | Con số 100% (hoặc lỗi cần sửa) | TB | 2 giờ |
| Buổi đo E4 | Thời gian trung vị, độ đồng thuận | Thấp | 0,5 ngày |
| Gom Constraint thành mục riêng, nối với ADR | Mục 1.x hoặc Mở đầu | TB | 1 giờ |
| Viết đoạn Impact theo P1–P5 | Kết luận báo cáo | TB | 1 giờ |
| Cập nhật PROJECT_OVERVIEW (đang ghi trạng thái 30/10) | File cập nhật | Thấp | 15 phút |

## 6. Đầu ra cuối

### 6.1 Bảng 7 khái niệm
| Bước | Khái niệm | Trả lời câu hỏi | Áp dụng cho đề tài | Khác biệt nổi bật |
|---|---|---|---|---|
| 1 | Context | Chuyện gì, ai liên quan? | Voucher tân thủ + COD trên sàn TMĐT; người mua, người bán, đội rủi ro | Tập trung "lạm dụng chính sách", không phải gian lận thẻ |
| 2 | Pain point | Khó ở đâu, hậu quả? | P1 farm voucher, P2 bùng COD, P3 né khóa, P4 xử lý thủ công, P5 chặn nhầm | Coi chặn nhầm là một nỗi đau ngang hàng |
| 3 | Objective | Cải thiện gì, đo bằng gì? | O1–O9 (recall, FPR, p95, % giải thích, % né khóa bị bắt) | Mục tiêu có cả phía khách thật, không chỉ "bắt được bao nhiêu" |
| 4 | Constraint | Giới hạn gì? | Không dữ liệu thật, 1 người, 2 tháng, đồng bộ tại checkout, PII | Ràng buộc giải thích trực tiếp vì sao rule-based |
| 5 | Method | Giải bằng cách nào? | 3 điểm kiểm soát, luật có phiên bản, Trust Score, khóa theo bậc, case + khiếu nại + audit | Luật là dữ liệu, sửa không cần deploy, mọi quyết định có lý do |
| 6 | Evaluation | Hiệu quả bao nhiêu? | Simulator tách dev/test, hard negative, biến thể chưa biết, Wilson CI | Báo cáo cả chỗ thua (biến thể chưa biết 0%) |
| 7 | Impact | Ai được lợi? | Sàn giảm thất thoát (ước tính), analyst có lý do, khách có khiếu nại | Có thể tách Risk Engine dùng cho sàn khác |

### 6.2 Ma trận truy vết
| Pain point | Objective | Method | Metric | Impact |
|---|---|---|---|---|
| P1 Farm voucher | O1, O3 | R01–R05, R11 (cụm địa chỉ), Trust Score, `min_trust` voucher | Recall farm, FPR gia đình/nhóm trọ | Voucher đến đúng khách mới thật |
| P2 Bùng COD | O1 | R07–R10, ẩn COD theo bậc Trust, giữ đơn chờ duyệt | Recall bùng COD | Giảm đơn COD rủi ro |
| P3 Né lệnh khóa | O7 | Khóa tự động 24h/vô thời hạn (ADR-010), F17/R16 truy vết liên kết (ADR-011) | % evader bị khóa thanh toán | Lệnh khóa có hiệu lực thật |
| P4 Xử lý thủ công | O6, O9 | Rule hit + giá trị đặc trưng, Case gom cụm, audit log, đồ thị liên kết | % quyết định có giải thích; thời gian xử lý case | Xử lý nhanh, nhất quán, truy vết được |
| P5 Chặn nhầm | O2, O3, O4, O8 | REVIEW/BLOCK cần luật mạnh, hạn chế theo bậc, khiếu nại tự gỡ khóa, danh sách miễn trừ | FPR khách thường, FPR hard negative, % có khiếu nại | Khách thật không bị mất quyền vô lý |
| Mọi P | O5 | Đặc trưng tính bằng SQL có index, không gọi dịch vụ ngoài | p95 chấm điểm, p95 checkout theo tải | Không làm chậm mua hàng |

### 6.3 Checklist tiếp theo
- [ ] Chốt bảng O1–O9 (sửa ngưỡng nếu muốn) → hỏi GVHD
- [ ] Điền REQUIREMENTS.md
- [ ] Tra nguồn số liệu Context
- [ ] Chạy E1 + E5 trên seed mới
- [ ] Chạy E2 đo tải
- [ ] Script E3
- [ ] (Nếu kịp) buổi E4
- [ ] Bảng Mục tiêu → Kết quả → Đạt/Chưa đạt
- [ ] Viết Constraint và Impact vào báo cáo

### 6.4 Prompt tạo ảnh infographic
> Không có mẫu "PROMPT 3" trong tài liệu được gửi, nên đây là prompt Claude tự soạn theo yêu cầu "mỗi ô ≤ 25 từ" **[ĐỀ XUẤT – cần xác nhận]**. Ô "Evaluation" dùng số đã đo; thay khi có số mới.

```
Tạo infographic dọc, phong cách phẳng, nền navy đậm, chữ trắng, điểm nhấn cyan, tiếng Việt, 7 ô đánh số nối bằng mũi tên từ trên xuống. Tiêu đề: "Kiểm soát rủi ro lạm dụng chính sách trên sàn TMĐT".
1 Ngữ cảnh: Sàn TMĐT dùng voucher người mới và COD để hút khách; người mua, người bán, đội rủi ro đều bị ảnh hưởng.
2 Vấn đề: Farm tài khoản gom voucher, bùng hàng COD, né khóa bằng tài khoản mới, xử lý thủ công, chặn nhầm khách thật.
3 Mục tiêu: Bắt ≥80% lạm dụng đã biết, chặn nhầm khách thường ≤2%, 100% quyết định có lý do, không làm chậm thanh toán.
4 Ràng buộc: Không có dữ liệu thật, một người làm trong hai tháng, quyết định phải tức thời, bảo vệ dữ liệu cá nhân.
5 Giải pháp: Risk Engine dựa trên luật có phiên bản, điểm tin cậy 100, khóa theo bậc, truy vết tài khoản liên kết, case và khiếu nại.
6 Đánh giá: Mô phỏng tách dev/test; recall kiểu đã biết 85,5%, chặn nhầm khách thường 0%, biến thể chưa biết còn lọt.
7 Giá trị: Sàn giảm thất thoát khuyến mãi, đội rủi ro xử lý có căn cứ, khách thật có đường khiếu nại, có thể tách dùng cho sàn khác.
Biểu tượng đơn giản cho từng ô, không logo thương hiệu thật, không ảnh người thật.
```
