# DEMO SCRIPT — Kịch bản demo bảo vệ

> Ngày: 2026-10-30 · Trạng thái: **Bản nháp v1, chờ Luca duyệt**
> Mục đích: thiết kế sản phẩm **ngược từ buổi demo**. Chỉ xây những gì kịch bản cần; tính năng nào không xuất hiện trong demo hay thực nghiệm thì để sau.
> Giả định: phạm vi MVP gồm 2 nhóm chính sách là **voucher tân thủ** và **COD** (đề xuất trong bản tư vấn, chưa chốt chính thức). Tên shop tạm gọi **[Tên shop]**.

## Tổng quan

| # | Cảnh | Thời lượng | Chứng minh điều gì | Mức |
|---|---|---|---|---|
| 0 | Mở đầu: bài toán | 0:30 | Vì sao hệ thống cần tồn tại | MVP |
| 0b | Bức tranh tổng thể (Dashboard) | 0:45 | Người quản lý nhìn một màn hình là biết tình trạng và việc cần làm | MVP |
| 1 | Khách hàng bình thường mua sắm | 1:00 | Người dùng hợp lệ không bị làm phiền; quyết định nhanh | MVP |
| 2 | Tấn công: farm voucher | 2:00 | Phát hiện theo thời gian thực, hành động mềm, không lộ luật | MVP |
| 3 | Điều tra case | 1:30 | Giải thích được, quy trình xử lý, audit | MVP |
| 4 | Gia đình chung Wi-Fi (hard negative) | 1:00 | Kiểm soát chặn nhầm | MVP |
| 5 | Bùng hàng COD và khách quen | 1:30 | Quyết định theo chính sách; giữ đơn chờ duyệt | MVP |
| 5c | Cố tình đặt lặp → khóa mua hàng tự động | 0:45 | Quyết định CHẶN duy nhất trong demo; tự động nhưng gỡ được (ADR-010) | MVP |
| 5e | Né lệnh khóa bằng tài khoản mới | 0:45 | Truy vết qua thiết bị/SĐT/địa chỉ; gia đình chung máy không bị khóa oan (ADR-011) | Recommended |
| 5d | Khiếu nại khi bị chặn nhầm | 1:00 | Khách có đường lên tiếng; xét lại bốn mắt; miễn trừ có kiểm soát | MVP |
| 6 | Quản lý luật | 1:00 | Cấu hình được, có phiên bản, phân quyền | MVP (cơ bản) |
| 7 | Kết quả thực nghiệm | 1:00 | Đã kiểm chứng bằng số liệu | MVP |
| 8 | Kết luận và hạn chế | 0:30 | Trung thực học thuật, hướng phát triển | MVP |
| | **Tổng** | **~11:45** | | |

**Bố cục màn hình khi demo:** chia đôi. Bên trái là **Shop** (vai khách hàng hoặc bot); bên phải là **Risk Console** (vai nhân viên rủi ro). Cảnh 7 dùng toàn màn hình.

---

## Cảnh 0 — Mở đầu: bài toán (0:30)
- **Nói:** sàn TMĐT phát voucher tân thủ và cho phép COD để hút khách. Một số người tạo hàng loạt tài khoản để gom voucher, hoặc đặt COD rồi không nhận hàng. Kiểm tra thủ công không theo kịp.
- **Hiển thị:** 1 slide gồm hai luồng chính sách (voucher, COD) và các hình thức lạm dụng tương ứng. Nếu dùng số liệu thiệt hại thì chỉ dùng số **có nguồn kiểm chứng được** [XM].
- **Câu chốt:** "Hệ thống của em quyết định trong vài chục mili-giây, giải thích được vì sao, và để con người có tiếng nói cuối cùng."
  - Con số độ trễ chỉ được nói nếu đã đo ở cảnh 7.

## Cảnh 0b — Bức tranh tổng thể (0:45)
- **Chuẩn bị:** `demo reset` rồi `python -m simulator.history --days 14 --yes` để có 14 ngày lịch sử mô phỏng.
- **Hiển thị:** Console → **Tổng quan**.
  - Thẻ **Tình trạng** (Bình thường / Cần chú ý / Cảnh báo) kèm lý do, suy ra từ dữ liệu.
  - **Việc cần làm trước** xếp theo mức khẩn cấp.
  - **Heatmap thứ × giờ** chỉ ra khung giờ bị lạm dụng.
  - **Phân bố điểm rủi ro**.
- **Nói:** "Người quản lý không cần đọc bảng số: nhìn một màn hình là biết hệ thống có ổn không và phải làm gì trước."
- **Lưu ý trung thực:** dữ liệu lịch sử là mô phỏng (email @sim.test), ghi rõ ở cuối trang.

## Cảnh 1 — Khách hàng bình thường (1:00)
- **Bên trái (Shop):** khách mới hợp lệ "Minh" (đăng ký hôm qua, nên được dùng voucher tân thủ) duyệt trang chủ → chi tiết sản phẩm → thêm vào giỏ → áp mã `NGUOIMOI` → checkout COD → **đặt hàng thành công**.
- **Bên phải (Console):** trang **Live Monitor** hiện hai dòng quyết định `ALLOW` (áp voucher, checkout), mỗi dòng có **thời gian xử lý (ms)**.
- **Chứng minh:** người dùng hợp lệ không gặp trở ngại; mọi giao dịch đều được chấm điểm và ghi nhận.
- **Cần có:** Shop (trang chủ, chi tiết, giỏ, checkout, kết quả), Live Monitor, luồng đánh giá đồng bộ, ghi `risk_decision`.

## Cảnh 2 — Tấn công farm voucher (2:00) ★ cảnh ăn điểm nhất
- **Thao tác:** mở trang **Attack Lab** trong Console (chỉ bật ở chế độ demo, chỉ vai quản trị), chọn kịch bản **"Farm voucher: 20 tài khoản mới, 3 thiết bị, 1 địa chỉ nhận hàng"**, bấm **Chạy**.
- **Bên phải:** Live Monitor đổ dồn sự kiện theo thời gian thực (SSE):
  - 4 tài khoản đầu: `ALLOW`, vì chưa đủ tín hiệu (hệ thống thật cũng vậy).
  - Từ tài khoản thứ 5 (5 tài khoản trên cùng địa chỉ): `ALLOW_WITH_RESTRICTION` (voucher bị gỡ). Từ tài khoản thứ 7 (3 tài khoản mới trên cùng thiết bị): điểm vượt 80. Phép tính xem `RULES_V0.md` mục 5.
  - Một **cảnh báo cụm** hiện lên: *"Cụm 20 tài khoản liên kết qua 3 thiết bị và 1 địa chỉ"* → mở **case** mới.
- **Bên trái:** Luca đăng nhập thủ công một tài khoản của farm trên trình duyệt, áp `NGUOIMOI` → shop báo *"Mã giảm giá không áp dụng được cho đơn hàng này"*. **Không nói lý do**, để kẻ gian không học được luật.
- **Chứng minh:** phát hiện theo thời gian thực; hành động **mềm** (gỡ voucher, vẫn cho mua giá gốc) thay vì chặn; thông điệp không lộ luật.
- **Cần có:** Attack Lab (gọi Simulator), SSE, luật liên kết tài khoản qua thiết bị và địa chỉ, ma trận quyết định ngữ cảnh voucher, tạo case tự động (worker).
- **Recommended:** bot chạy bằng Playwright trên chính giao diện shop, để khán giả *thấy* trình duyệt tự thao tác.

## Cảnh 3 — Điều tra case (1:30)
- **Bên phải:** mở case vừa tạo. Màn hình **Case Detail** gồm:
  - **Điểm và quyết định**, kèm **bảng phân rã điểm**: từng luật khớp, số điểm cộng, **giá trị đặc trưng thực tế** (ví dụ "7 tài khoản mới trên thiết bị D-02 trong 24 giờ, ngưỡng 3").
  - **Tài khoản liên quan**: danh sách tài khoản trong cụm, cùng thiết bị/địa chỉ (Advanced: sơ đồ liên kết).
  - **Dòng thời gian** sự kiện của cụm.
  - Phiên bản luật đã dùng.
- **Thao tác:** analyst bấm **"Xác nhận lạm dụng"** → hệ thống **bắt buộc nhập lý do** → lưu. Mở **Audit Log** để thấy bản ghi vừa tạo: ai, lúc nào, làm gì, giá trị trước và sau.
- **Chứng minh:** quyết định giải thích được bằng dữ liệu; có quy trình xử lý của con người; mọi thao tác đều truy vết được.
- **Cần có:** Case Queue, Case Detail, hành động resolve có lý do, Audit Log, RBAC (vai Analyst).

## Cảnh 4 — Gia đình chung Wi-Fi (1:00)
- **Thao tác:** Attack Lab → kịch bản **"Gia đình 4 người: cùng IP, khác thiết bị, mỗi người 1 voucher"** → Chạy.
- **Bên phải:** cả 4 giao dịch `ALLOW`. Mở một quyết định: luật "nhiều tài khoản trên cùng IP" **có ghi nhận tín hiệu nhưng điểm thấp**, vì IP chung là tín hiệu yếu và không có tín hiệu mạnh đi kèm, nên tổng điểm dưới ngưỡng.
- **Câu nói:** "IP và fingerprint không đáng tin tuyệt đối. Hệ thống chỉ hành động khi nhiều tín hiệu cùng chỉ về một hướng."
- **Chứng minh:** thiết kế có chủ đích để **giảm chặn nhầm**, trả lời trước câu hỏi hội đồng chắc chắn sẽ hỏi.
- **Cần có:** kịch bản hard negative, màn hình chi tiết quyết định (dùng lại phần phân rã điểm).

## Cảnh 5 — Bùng hàng COD và khách quen (1:30)
- **Chuẩn bị (dữ liệu seed):**
  - Tài khoản "Khang" có lịch sử 5 đơn COD, 4 đơn giao thất bại.
  - Tài khoản "Lan" là khách quen, 30 đơn, giao thành công 100%.
- **5a.** Khang đặt đơn mới → bước chọn thanh toán **không còn COD**, chỉ còn trả trước (`ALLOW_WITH_RESTRICTION`). Thông điệp lịch sự: *"Đơn này chưa dùng được thanh toán khi nhận hàng. Bạn chọn trả trước để tiếp tục."*
- **5b.** Một tài khoản mới đặt đơn COD giá trị cao **bất thường** → `REVIEW` → đơn ở trạng thái **"Chờ xác minh"**, chưa bàn giao vận chuyển. Bên phải, analyst mở case, duyệt → đơn chuyển sang "Đã xác nhận".
- **5c.** Lan đặt COD giá trị cao → `ALLOW` (hard negative). Mở chi tiết: **luật tín hiệu tích cực** (lịch sử giao thành công dài) đã kéo điểm xuống.
- **Chứng minh:** cùng mức rủi ro nhưng hành động khác nhau theo chính sách; vòng đời đơn hàng có bước giữ đơn chờ duyệt; lịch sử tốt được ghi nhận.
- **Cần có:** module fulfillment (giả lập giao thành công/thất bại để có lịch sử), luật tỷ lệ COD thất bại có làm mượt, luật giá trị COD bất thường, luật tích cực, trạng thái `PENDING_REVIEW`, ẩn phương thức thanh toán theo quyết định.

## Cảnh 5c — Cố tình đặt lặp sau khi bị từ chối (0:45)
- Khang bị ẩn COD. Người thuyết trình nói: "kẻ gian bỏ qua giao diện, gọi thẳng API đặt COD nhiều lần".
- Gửi 4 lần (công cụ API hoặc script): 3 lần đầu bị từ chối "Đơn này chưa dùng được thanh toán khi nhận hàng…"; lần thứ 4 bị **chặn** và tài khoản **tạm khóa mua hàng 24 giờ**; tái phạm trong 30 ngày thì khóa vô thời hạn.
- Console: case tự mở, dải đỏ "Tạm khóa mua hàng", khung "Quyền mua hàng" có nút Gỡ khóa (chỉ Risk Manager, bắt buộc lý do, ghi audit).
- Điểm nhấn: hoàn toàn tự động nhưng không có quyết định nào "không thể đảo ngược"; khách vẫn đăng nhập và khiếu nại được (chuyển sang cảnh 5d).

## Cảnh 5e — Né lệnh khóa bằng tài khoản mới (0:45)
- Manager mở Case của Khang → **Khóa vô thời hạn** (ghi lý do).
- Chạy `scripts/demo_attack.py evade`: tạo tài khoản mới trên cùng máy, vừa đăng ký đã áp NGUOIMOI, chưa xem sản phẩm nào (dấu hiệu bot) → **khóa thanh toán 30 ngày ngay lần 1** (ADR-015); lần 2 và đặt hàng trả trước đều bị chặn.
- Console: case mới, lý do "Liên kết với tài khoản đang bị khóa #… qua thiết bị"; đồ thị liên kết có vòng đỏ đặc ở Khang.
- Điểm nhấn khi bị hỏi: con dùng chung máy của bố bị khóa, có xem sản phẩm như người bình thường, thì chỉ bị trừ điểm và mở case, không bị khóa (test `test_family_member_on_shared_device_is_not_locked`); chung IP không bao giờ tính. Cái giá đã biết: người nhà vừa đăng ký đã áp mã ngay, không xem sản phẩm, sẽ bị khóa nhầm và phải khiếu nại.

## Cảnh 5d — Khiếu nại khi bị chặn nhầm (1:00)
- **Bên trái:** tài khoản mới ở cảnh 5b (đơn đang bị giữ) mở trang **Khiếu nại**.
  - Khách chỉ thấy "Đơn hàng bị giữ lại chờ xác minh", **không thấy luật hay điểm**.
  - Khách viết lý do và gửi.
- **Bên phải:**
  - Đăng nhập vai **Analyst**, mở khiếu nại: thấy luật đã khớp nhưng **không có nút kết luận**.
  - Đổi sang vai **Risk Manager**: viết câu trả lời cho khách, bấm **Chấp nhận**.
  - Kết quả: đơn chuyển "Đã xác nhận", khách được miễn trừ COD 30 ngày, Audit Log có bản ghi `appeal.resolve`.
- **Chứng minh:**
  - Khép kín vòng xử lý chặn nhầm, đúng điểm yếu mà thực nghiệm đã chỉ ra (hard negative).
  - Nguyên tắc bốn mắt.
  - Miễn trừ không tắt luật: luật vẫn được ghi lại để giải thích.
- **Cần có:** module appeals, `risk_allowlist`, `decide(..., exempt)` (ADR-006).

## Cảnh 6 — Quản lý luật (1:00)
- **Thao tác:**
  - Đăng nhập vai **Risk Manager** → trang **Rules**.
  - Mở luật R02 "tài khoản mới trên cùng thiết bị", đổi bậc thấp từ "≥3 tài khoản: +35" thành "≥2 tài khoản: +40".
  - Bấm **Chạy thử trên dữ liệu cũ** (30 ngày): thấy ngay bao nhiêu lượt / tài khoản sẽ bị hạn chế thêm, có ai là khách quen hay case đã kết luận không vi phạm không. Chưa có gì được lưu.
  - Ghi lý do, bấm lưu → hệ thống **tạo phiên bản mới**, phiên bản cũ vẫn giữ trong lịch sử.
  - Chạy lại kịch bản farm (cảnh 2) → voucher bị gỡ từ tài khoản thứ 2 (10 + 40 = 50) thay vì thứ 3.
- **Chứng minh phân quyền:** đăng nhập vai Analyst → chạy thử được nhưng không có nút lưu (tách bạch nhiệm vụ).
- **Chứng minh:** luật cấu hình được, không hardcode; có phiên bản; có phân quyền; mỗi quyết định ghi lại phiên bản luật đã dùng.
- **Cần có:** trang Rules (danh sách, sửa tham số, lịch sử phiên bản), RBAC.
- **Đã làm (FR-43):** chạy thử (replay) tham số mới trên dữ liệu cũ trước khi áp dụng.

## Cảnh 7 — Kết quả thực nghiệm (1:00)
- **Hiển thị:** trang **Reports** hoặc slide kết quả, **chỉ dùng số đã thực sự đo** từ Simulator trên tập test:
  - Confusion matrix theo từng kịch bản (farm, COD, hard negatives, biến thể chưa biết).
  - Precision, recall, FPR tách riêng cho giao dịch thường và hard negatives, kèm khoảng tin cậy.
  - Độ trễ đánh giá rủi ro p50/p95/p99 ở 2–3 mức tải, kèm cấu hình máy đo.
  - Chỉ số nghiệp vụ: giá trị voucher ngăn được, số đơn COD rủi ro bị chuyển trả trước, số khách hợp lệ bị ảnh hưởng.
- **Chứng minh:** đánh giá có phương pháp (tách tập dev/test, có hard negatives và biến thể chưa biết), không chỉ demo "chạy được".
- **Cần có:** Simulator ghi kết quả, script tính chỉ số, trang KPI cơ bản trong Console.

## Cảnh 8 — Kết luận và hạn chế (0:30)
- **Đã làm được:** 3 ý ngắn: phát hiện theo thời gian thực có giải thích, quy trình xử lý có audit, kết quả thực nghiệm.
- **Hạn chế (nói thẳng):** dữ liệu mô phỏng; luật có thể bị lách theo thời gian; fingerprint chỉ là tín hiệu mô phỏng.
- **Hướng phát triển:** ML làm đối chứng; tách Risk module thành service riêng; phân tích đồ thị liên kết; tóm tắt case bằng LLM.

---

## Phạm vi MVP suy ra từ kịch bản

### Màn hình

| Khu vực | Màn hình | Cảnh | Mức |
|---|---|---|---|
| Shop | Đăng ký / Đăng nhập | 1, 2 | MVP |
| Shop | Trang chủ + danh sách sản phẩm | 1 | MVP |
| Shop | Chi tiết sản phẩm | 1 | MVP |
| Shop | Giỏ hàng + áp voucher | 1, 2 | MVP |
| Shop | Checkout (địa chỉ, phương thức thanh toán) | 1, 5 | MVP |
| Shop | Kết quả đặt hàng + lịch sử đơn (có trạng thái "Chờ xác minh") | 1, 5 | MVP |
| Console | Đăng nhập nhân viên | 3, 6 | MVP |
| Console | **Live Monitor** (dòng quyết định realtime + cảnh báo) | 1, 2, 4 | MVP |
| Console | **Case Queue** | 3, 5 | MVP |
| Console | **Case Detail** (phân rã điểm, tài khoản liên quan, timeline, xử lý) | 3, 5 | MVP |
| Console | Chi tiết quyết định (dùng chung phần phân rã điểm) | 4, 5 | MVP |
| Console | **Rules** (danh sách, sửa tham số, lịch sử phiên bản) | 6 | MVP (cơ bản) |
| Console | **Attack Lab** (chọn và chạy kịch bản; chỉ ở chế độ demo) | 2, 4 | MVP |
| Console | Audit Log | 3 | MVP |
| Console | Reports / KPI | 7 | MVP (cơ bản) |
| Console | Sơ đồ liên kết tài khoản | 3 | Advanced |

### Vai trò
- **Customer**
- **Analyst**: xem và xử lý case; không sửa luật.
- **Risk Manager**: sửa luật; xem báo cáo.
- **Admin**: Attack Lab, Audit Log. Có thể gộp với Risk Manager trong MVP.

### Luật cần có (tên tạm, chi tiết làm ở bước "Luật v0")

| Luật | Tín hiệu | Cảnh |
|---|---|---|
| Tài khoản mới dùng mã người mới | tuổi tài khoản | 2 |
| Nhiều tài khoản mới trên cùng thiết bị | đếm theo cửa sổ thời gian | 2, 6 |
| Nhiều tài khoản trên cùng địa chỉ nhận hàng | đếm sau khi chuẩn hóa địa chỉ | 2 |
| Nhiều tài khoản trên cùng IP | tín hiệu **yếu**, điểm thấp | 4 |
| Tần suất thử voucher cao | velocity | 2 |
| Tỷ lệ COD giao thất bại (làm mượt) | lịch sử giao hàng | 5a |
| Giá trị COD bất thường với tài khoản ít lịch sử | giá trị đơn + tuổi/lịch sử | 5b |
| **Luật tích cực:** lịch sử giao thành công dài | trừ điểm | 5c |
| Tốc độ thao tác giống bot | thời gian từ đăng ký đến checkout | 2 (Recommended) |

### Kịch bản mô phỏng cho Attack Lab
1. Farm voucher (cảnh 2, 6).
2. Gia đình chung Wi-Fi (cảnh 4).
3. Seed lịch sử COD cho Khang và Lan (cảnh 5).
4. Đơn COD giá trị cao từ tài khoản mới (cảnh 5b).

### Yêu cầu riêng cho buổi demo
> Đã cài đặt (2026-10-30): `python -m app.modules.lab.reset --yes` tạo lại trạng thái chuẩn gồm Minh (khách mới, đăng ký 20 giờ trước), Khang (5 đơn COD, 4 thất bại), Lan (30 đơn giao thành công), 3 nhân viên analyst / manager / admin; mật khẩu trong `backend/.env.accounts`.

- **Script `demo reset`** đưa CSDL về trạng thái chuẩn trong dưới 1 phút: có sẵn tài khoản Minh, Khang, Lan, nhân viên, sản phẩm, voucher.
- **Lịch sử mô phỏng 14 ngày** (`python -m simulator.history --days 14 --yes`, chạy sau demo reset) để Dashboard có dữ liệu trải theo ngày và giờ. Khách lịch sử dùng thiết bị và IP riêng nên không ảnh hưởng nhân vật Minh, Khang, Lan.
- **Chạy hoàn toàn offline trên laptop**, không phụ thuộc mạng hay API bên ngoài.
- **Video quay sẵn** toàn bộ kịch bản để dự phòng.
- Attack Lab **tắt ở chế độ thường**, chỉ bật bằng cấu hình demo, và chỉ vai Admin dùng được.
- Dữ liệu cá nhân trên Console được che một phần (IP, số điện thoại) để thể hiện privacy-by-design.

### Không cần cho demo (để sau hoặc bỏ)
Đánh giá sản phẩm, tìm kiếm nâng cao, đăng nhập mạng xã hội, cổng thanh toán thật, email thông báo, đa ngôn ngữ, LLM.

## Việc tiếp theo
1. Luca duyệt kịch bản: thêm, bớt hay đổi cảnh nào.
2. Viết **danh sách luật v0**: tham số, điểm, lý do, hard negative bị ảnh hưởng.
3. Vẽ **ERD** từ kịch bản và danh sách luật.
