# Thiết kế Trust Score — mô hình rủi ro 2 lớp (bộ luật v3)

> Trạng thái: **Luca duyệt hướng (2026-10-31), đang cài đặt**. Con số là lập luận chuyên gia [ĐX], hiệu chỉnh trên tập dev.
> Ý tưởng gốc: Luca ("mỗi tài khoản 100 điểm, có bất thường thì trừ dần, điểm thấp thì cắt dần mã giảm giá, về 0 thì hạn chế thanh toán và cắm cờ").
> Đây cũng là "Trust Score" trong đề cương ban đầu.

## 1. Hai lớp

| Lớp | Câu hỏi | Ở đâu |
|---|---|---|
| **1. Điểm tin cậy tài khoản (Trust Score)** | Tài khoản này đáng tin tới đâu, xét **mọi** dấu hiệu đang có? | Tính ở mỗi lần chấm, lưu trong `features_snapshot` của quyết định |
| **2. Chấm điểm giao dịch (Risk Engine hiện có)** | Đơn / lần áp mã **này** có rủi ro không, theo từng chính sách? | Giữ nguyên bộ luật và ma trận quyết định |

**Cách tính Trust:** `Trust = min(100, 100 − Σ điểm của mọi luật khớp)`.
- Mọi luật (voucher lẫn COD) có dữ liệu để tính thì đều trừ, **không** lọc theo context như lớp 2. Nhờ vậy cùng một tài khoản, ở bước áp mã hay bước đặt hàng, đều thấy gần cùng một bức tranh.
- Luật tích cực (điểm âm) **cộng lại** điểm tin cậy.
- Có thể **âm**: không chặn dưới ở 0, để phân biệt "hơi xấu" với "rất xấu".
- **Không trừ trùng:** mỗi luật chỉ trừ một lần, ở bậc cao nhất; mọi lần chấm đều tính lại từ hiện trạng, không cộng dồn qua các đơn.
- **Tự hồi điểm:** các đặc trưng có cửa sổ thời gian (24 giờ, 7 ngày, 30 ngày, 90 ngày), nên khi dấu hiệu hết hạn thì điểm trừ tự mất.
- **Nhật ký trừ điểm:** danh sách luật khớp kèm lý do đã được lưu cho từng quyết định (`rule_hits`), Console hiển thị như "sổ trừ điểm".

## 2. Dấu hiệu mới (thêm vào bộ luật, dạng dữ liệu có phiên bản)

| Mã | Đặc trưng | Luật | Điểm | Độ mạnh | Hard negative |
|---|---|---|---|---|---|
| F14 | `accounts_on_phone_30d`, `addresses_on_phone_30d`: một SĐT nhận hàng được bao nhiêu tài khoản dùng, ở bao nhiêu địa chỉ, trong 30 ngày | **R12** `PHONE_MULTI_ACCOUNTS` (place_order): SĐT ở **≥ 2 địa chỉ** và ≥ 3 tài khoản → +15; ≥ 5 → +25 | 15 / 25 | Vừa | Người nhận hộ cho bạn bè ở nhiều nơi. **Đã sửa khi cài đặt:** bản đầu chỉ đếm tài khoản, làm gia đình 4 người chung SĐT bị gỡ voucher (trừ trùng với R03), nên thêm điều kiện "nhiều địa chỉ" |
| F15 | `distinct_addresses_7d`: số địa chỉ khác nhau tài khoản này dùng trong 7 ngày | **R13** `ADDRESS_HOPPING` (place_order): ≥ 3 → +10 | 10 | Yếu | Người hay gửi quà cho người khác |
| F16 | `voucher_subsidy_ratio_90d`: tổng tiền giảm ÷ tổng tiền hàng của các đơn hợp lệ trong 90 ngày (cần ≥ 3 đơn) | **R14** `VOUCHER_SUBSIDY_HIGH` (voucher_apply, place_order): ≥ 15% → +10; ≥ 25% → +20 | 10 / 20 | Vừa | Khách chỉ mua khi có khuyến mãi (hợp lệ nhưng ít lãi) |
| F09, F16 | — | **R15** `PROFITABLE_CUSTOMER` (luật tích cực): ≥ 3 đơn giao thành công **và** tỷ lệ trợ giá < 10% | **−15** | — | — |

- **Vì sao "tỷ lệ trợ giá" thay cho "lãi/lỗ":** hệ thống không có giá vốn nên không tính được lãi thật; phần sàn bù bằng voucher thì đo chính xác được. "Tiêu 100 triệu, sàn bù 20 triệu" = 20%.
- **Thẻ / tài khoản ngân hàng dùng chung:** **không làm**: thanh toán là giả lập, không có số thẻ. Ghi vào hướng phát triển.

## 3. Bậc tin cậy và hành động

| Trust | Bậc | Hành động thêm (ngoài ma trận quyết định hiện có) |
|---|---|---|
| ≥ 70 | Bình thường | Dùng được mọi mã |
| 50–69 | Theo dõi | Console đánh dấu; **mã giá trị cao (GIAM10) tạm khóa** |
| 30–49 | Hạn chế | **Mọi mã giảm giá tạm khóa** |
| < 30 | Xem xét | Như trên + **mở case** cho analyst xem tài khoản (cắm cờ) |
| ≤ 0 | Rất thấp | Như trên + **tắt COD**, chỉ cho trả trước |

- **"Cắt dần danh sách mã":** mỗi voucher có `min_trust` (NGUOIMOI: 50, GIAM10: 70). Trust dưới mức đó thì mã bị gỡ khi áp hoặc khi đặt hàng; túi voucher hiện "Tạm chưa áp dụng".
- **Không chặn thanh toán chỉ vì điểm thấp.** Chặn hẳn (BLOCK) vẫn chỉ xảy ra khi có ≥ 2 luật mạnh theo ma trận cũ, và luôn qua case. Lý do: đơn trả trước gần như không gây thiệt hại cho sàn; chặn nhầm là mất khách.
- **Cắm cờ thiết bị:** case mở theo cụm thiết bị/địa chỉ như hiện có; không tự động chặn tài khoản khác cùng thiết bị (máy gia đình dùng chung).
- Khiếu nại được chấp nhận → miễn trừ chính sách đó 30 ngày (ADR-006): voucher được miễn thì bỏ qua khóa mã theo Trust.
- Các ngưỡng bậc là **cấu hình** trong `decision_policies` (có phiên bản), tắt được để so sánh thực nghiệm.

## 4. Túi voucher và mã NGUOIMOI

- Đổi mã **TANTHU → NGUOIMOI**.
- Bảng mới `user_vouchers`: khi tạo tài khoản, shop **cấp sẵn** NGUOIMOI vào túi. Mã công khai (GIAM10) ai cũng thấy.
- API `GET /api/vouchers/wallet`: danh sách mã kèm trạng thái *dùng được / đã dùng / tạm chưa áp dụng / chưa đủ điều kiện*. Thông điệp chung chung, không lộ điểm tin cậy hay luật.
- Giỏ hàng: chọn mã từ túi bằng một chạm; vẫn gõ mã tay được.

## 5. Tính thử

| Nhân vật | Luật khớp (mọi context) | Trust | Kết quả thêm |
|---|---|---|---|
| Minh, khách mới | R01 | 90 | Dùng được NGUOIMOI |
| Farm tài khoản thứ 3 cùng máy | R01 + R02(35) + R04 | 45 | Mọi mã tạm khóa (v2 cũng đã gỡ: 55 ≥ 50) |
| Khang, COD thất bại 33% | R07(45) | 55 | GIAM10 tạm khóa, COD đã bị tắt bởi ma trận cũ |
| Lan, khách uy tín | R09(−30) | 100 | Bình thường |
| Khách quen hay "săn sale": 5 đơn, sàn bù 22% | R14(10) | 90 | Bình thường (chỉ bị trừ ít) |
| Tài khoản mới, COD 5,5 triệu | R01? + R08(70) | ≤ 30 | Đơn giữ chờ duyệt (như cũ) + mã tạm khóa |

## 6. Đo lường

- Bộ luật đổi → **tập test mới (seed 4)**, chạy một lần sau khi khóa. So v2 và v3 trên cùng dân số bằng cờ tắt luật mới + tắt bậc Trust.
- Trung thực: bộ mô phỏng **không** giả định farm dùng chung số điện thoại (nếu tự thêm giả định đó thì R12 "đúng" chỉ vì mình đặt ra). R12 được kiểm bằng test kịch bản, không có số liệu mô phỏng.

## 7. Không làm

- Không dùng điểm tin cậy để chặn thanh toán trực tiếp (mục 3).
- Không hiển thị con số Trust cho khách: tránh bị dò ngưỡng.
- Không lưu Trust thành một "số dư" cộng trừ dồn qua thời gian: khó giải thích, dễ trừ trùng, khó sửa khi trừ nhầm.
