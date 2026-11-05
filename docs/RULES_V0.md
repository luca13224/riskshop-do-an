# RULES V0 — Bộ luật rủi ro phiên bản đầu

> Ngày: 2026-10-30 · Trạng thái: **v0.1: đã cài đặt (Luca đã duyệt v0)**
> Nguồn gốc các con số: **lập luận chuyên gia ban đầu [ĐX]**, chưa hiệu chỉnh trên dữ liệu. Mọi ngưỡng, điểm và cửa sổ thời gian là **tham số cấu hình**, sẽ hiệu chỉnh trên tập dev rồi khóa trước khi chạy tập test (xem bản tư vấn, mục 6.3 và 7.3).
> Phạm vi: 2 nhóm chính sách là voucher tân thủ và COD (theo `DEMO_SCRIPT.md`).


## 0. Thay đổi khi cài đặt (v0.1, 2026-10-30)
Những điểm dưới đây được điều chỉnh khi lập trình Risk Engine; code và test là nguồn chính xác nhất (`backend/app/modules/risk/seed.py`).
- **Điểm tính riêng theo chính sách:** mỗi lần đánh giá có điểm `voucher` và điểm `cod` riêng (luật thuộc chính sách nào thì cộng vào chính sách đó; R06 thuộc cả hai). Hành động áp theo từng chính sách: điểm voucher quyết định gỡ voucher, điểm COD quyết định tắt COD / giữ đơn / chặn. Quyết định tổng là mức nghiêm trọng nhất.
- **R03 (địa chỉ) chỉ chạy ở `place_order`**, vì lúc áp voucher chưa có địa chỉ. Farm voucher dùng chung địa chỉ sẽ bị chặn voucher ở bước đặt hàng (trả lỗi `VOUCHER_NOT_APPLICABLE`, voucher bị gỡ khỏi giỏ, khách đặt lại với giá gốc).
- **`payment_options` dùng cùng luật COD và cùng ngưỡng với `place_order`** (R06, R08 lên phiên bản 2): đơn sẽ bị hạn chế/chặn thì ẩn COD ngay; đơn sẽ bị giữ chờ duyệt thì vẫn cho chọn COD. Tránh giao diện và lúc đặt hàng mâu thuẫn nhau.
- **Lúc đặt hàng bị hạn chế:** không tạo đơn, hoàn tác giữ chỗ tồn kho, nhưng vẫn lưu quyết định để truy vết.
- **R07** mặc định độ mạnh "vừa"; chỉ bậc ≥ 0,30 là "mạnh". **R08** bậc 3 triệu "vừa", bậc 5 triệu "mạnh".

## 0b. Bộ luật v2 (2026-10-31, ADR-008)
- Thêm **F12** `new_accounts_on_address_7d`, **F13** `address_ip_diversity_7d` và luật **R11** `ADDR_VOUCHER_RING` (mục 2, 3).
- Thiết kế, hiệu chỉnh và lý do chọn ngưỡng: `docs/reviews/2026-10-31_RISK_V2_DESIGN.md`. Kết quả: `TEST_PLAN.md` mục 3c.

## 0c. Bộ luật v3 — Trust Score (2026-10-31, ADR-009)
- Lớp 1: điểm tin cậy tài khoản = min(100, 100 − tổng điểm mọi luật khớp), bậc Bình thường / Theo dõi / Hạn chế / Xem xét / Rất thấp.
- Thêm F14–F16 và R12–R15 (mục 2, 3). Mã TANTHU đổi thành **NGUOIMOI**, cấp sẵn vào túi voucher khi đăng ký.
- Thiết kế: `docs/reviews/2026-10-31_TRUST_SCORE_DESIGN.md`. Kết quả: `TEST_PLAN.md` mục 3d.

## 0d. Khóa quyền mua hàng tự động (2026-10-31, ADR-010)
- Đếm số lần **đặt hàng bị từ chối** (đơn không được tạo) trong 24 giờ, tính từ lần khóa gần nhất. Lần thứ 4 → tạm khóa mua 24 giờ; đã từng bị khóa tự động trong 30 ngày → khóa vô thời hạn. Lần kích hoạt là quyết định **BLOCK**, tự mở case, ghi audit.
- Khi đang khóa: mọi lần đặt hàng bị chặn ngay (không chấm điểm, không cộng dồn); vẫn đăng nhập, xem đơn, khiếu nại được.
- Gỡ: khiếu nại được chấp nhận, hoặc Risk Manager/Admin (bắt buộc lý do ≥ 10 ký tự, audit `account.unrestrict`).
- Đây là quy tắc thực thi theo **hành vi lặp lại**, không phải luật chấm điểm, nên không làm thay đổi nguyên tắc "REVIEW/BLOCK theo điểm cần luật mạnh" ở mục 4.

## 0e. Né lệnh khóa bằng tài khoản mới (2026-10-31, ADR-011)
- **F17** `banned_link_types_90d`: số loại điểm chung (thiết bị, SĐT nhận hàng, địa chỉ) với tài khoản **đang bị khóa vô thời hạn** trong 90 ngày. IP không tính. Chỉ tài khoản bị ban làm nguồn (không lây dây chuyền).
- **R16** `LINKED_TO_BANNED` (voucher + COD, mọi context): F17 ≥ 1 → +45; ≥ 2 → +60. Độ mạnh vừa.
- Khóa thanh toán (ngoài ma trận điểm): F17 ≥ 2, **hoặc** F17 ≥ 1 **và** đang thử mã người mới với F05 ≥ 2 lần/10 phút → khóa 30 ngày, đã từng bị khóa do liên kết → 60 ngày. F17 = 1 mà không spam → chỉ R16 + mở case.
- ADR-015: thêm điều kiện khóa ngay ở bước áp mã: F17 ≥ 1 **và** đang dùng mã người mới **và** vừa đăng ký < 60 giây, chưa xem sản phẩm (dấu hiệu bot, khớp R06).
- **F18** (ADR-016) `cluster_new_accounts_30d`, `cluster_voucher_accounts_30d`, `cluster_link_types` (số nhóm cạnh: thiết bị / điểm nhận hàng = SĐT hoặc địa chỉ): thành phần liên thông chứa tài khoản đang chấm, chỉ đi qua tài khoản **mới** (tạo trong 30 ngày), cạnh là chung thiết bị / SĐT nhận hàng / địa chỉ chuẩn hóa (không tính IP), tối đa 60 nút, 8 vòng. Chỉ tính khi đang dùng mã người mới.
- Đồ thị liên kết đánh dấu tài khoản đang bị khóa. Risk Manager khóa vô thời hạn thủ công được (sau khi xem case).

## 1. Ba điểm kiểm soát (evaluation context)

| Context | Khi nào gọi | Quyết định có thể trả | Ghi chú |
|---|---|---|---|
| `voucher_apply` | Khách áp một voucher có cờ `risk_checked` (voucher tân thủ) vào giỏ | `ALLOW`, `ALLOW_WITH_RESTRICTION` (gỡ voucher) | Chạy **sau** kiểm tra nghiệp vụ (đúng đối tượng, còn lượt, đủ giá trị tối thiểu). Voucher sai nghiệp vụ bị từ chối luôn, không chấm điểm |
| `payment_options` | Trang checkout tải danh sách phương thức thanh toán | `ALLOW`, `ALLOW_WITH_RESTRICTION` (ẩn COD) | Chỉ ảnh hưởng giao diện; **không phải** lớp bảo vệ cuối |
| `place_order` | Khách bấm đặt hàng | `ALLOW`, `ALLOW_WITH_RESTRICTION`, `REVIEW`, `BLOCK` | **Lớp bảo vệ cuối, bắt buộc ở server.** Kể cả khi client gian lận gửi thẳng `payment_method=cod` qua API, server vẫn chấm lại và từ chối COD nếu cần. Voucher đã áp cũng được chấm lại ở đây |

## 2. Đặc trưng (features)

Mọi đặc trưng được tính **tại thời điểm đánh giá**, chỉ từ dữ liệu **đã có trước** thời điểm đó (không dùng thông tin tương lai). Mỗi giá trị được lưu vào `features_snapshot` của quyết định.

| Mã | Đặc trưng | Cách tính | Ghi chú độ tin cậy |
|---|---|---|---|
| F01 | `account_age_hours` | now − thời điểm tạo tài khoản | Tin cậy |
| F02 | `new_accounts_on_device_30d` | Số tài khoản **khác nhau, tuổi < 7 ngày** đã xuất hiện trên cùng `device_id` trong 30 ngày, **tính cả tài khoản hiện tại** | `device_id` là ID ngẫu nhiên lưu trong trình duyệt; trong mô phỏng do persona đặt. **Giả mạo được**, nên là tín hiệu mạnh nhưng không tuyệt đối |
| F03 | `accounts_on_address_30d` | Số tài khoản khác nhau dùng cùng **địa chỉ đã chuẩn hóa** trong 30 ngày, tính cả hiện tại | Chuẩn hóa đơn giản: chữ thường, bỏ dấu câu và khoảng trắng thừa, "số 05" → "so 5". Gia đình hay văn phòng dùng chung địa chỉ |
| F04 | `new_accounts_on_ip_24h` | Số tài khoản tuổi < 7 ngày dùng cùng IP trong 24 giờ, tính cả hiện tại | **Tín hiệu yếu:** Wi-Fi gia đình, ký túc xá, NAT của nhà mạng |
| F05 | `voucher_attempts_device_10m` | Số lần áp voucher (thành công hay không) từ cùng `device_id` trong 10 phút | Bắt cả hành vi dò mã |
| F06 | `signup_to_checkout_sec`, `product_views_session` | Từ lúc đăng ký đến lúc đặt hàng; số lượt xem sản phẩm trong phiên | Tín hiệu hành vi kiểu bot (Recommended) |
| F07 | `cod_finished`, `cod_failed` | Số đơn COD đã kết thúc (giao thành công hoặc thất bại) và số đơn thất bại | Chỉ tính đơn **đã có kết quả** trước thời điểm đánh giá |
| F08 | `cod_fail_rate_smoothed` | `(cod_failed + 1) / (cod_finished + 10)` | Làm mượt kiểu Bayes với tỷ lệ nền giả định 10% [XM: tỷ lệ COD thất bại thực tế ở VN chưa có nguồn]. Tránh việc khách mới thất bại 1/1 đơn bị tính 100% |
| F09 | `delivered_orders` | Tổng số đơn giao thành công (mọi phương thức) | Dùng cho luật tích cực |
| F10 | `open_cod_orders` | Số đơn COD đang chờ giao (chưa kết thúc, chưa hủy) | |
| F11 | `order_value` | Tổng giá trị đơn (VND) sau giảm giá | |
| F12 | `new_accounts_on_address_7d` (v2) | Số tài khoản khách **mới (< 7 ngày)** có địa chỉ chuẩn hóa trùng địa chỉ đơn này trong 7 ngày, tính cả hiện tại | Chỉ có ở `place_order` |
| F14 | `accounts_on_phone_30d`, `addresses_on_phone_30d` (v3) | Một SĐT nhận hàng: bao nhiêu tài khoản, ở bao nhiêu địa chỉ, trong 30 ngày | Chỉ có ở `place_order` |
| F15 | `distinct_addresses_7d` (v3) | Số địa chỉ khác nhau tài khoản này dùng trong 7 ngày | |
| F16 | `voucher_subsidy_ratio_90d` (v3) | Tổng tiền giảm ÷ tổng tiền hàng các đơn hợp lệ 90 ngày (cần ≥ 3 đơn) | Thay cho "lãi/lỗ" vì không có giá vốn |
| F13 | `address_ip_diversity_7d` (v2) | Số IP khác nhau các tài khoản ở F12 đã dùng trong 7 ngày ÷ F12 | Gần 1: mỗi người một mạng; thấp: chung Wi-Fi. **Không phân biệt** được nhóm dùng 4G riêng với farm |

## 3. Danh sách luật

**Cách chấm điểm:** `score = clamp(Σ điểm các luật khớp, 0, 100)`. Luật tích cực mang điểm âm.

**Độ mạnh của luật** dùng trong ma trận quyết định: **Mạnh** (S) đủ để giữ đơn chờ duyệt; **Trung bình** (M) và **Yếu** (W) chỉ góp điểm.

| Mã | Tên | Context | Điều kiện (tham số) | Điểm | Độ mạnh | Lý do nghiệp vụ | Hard negative có thể bị ảnh hưởng |
|---|---|---|---|---|---|---|---|
| R01 | `VCH_NEW_ACCOUNT` | voucher_apply, place_order | Voucher tân thủ **và** F01 < 24 giờ | +10 | W | Farm luôn dùng tài khoản vừa tạo; nhưng người mới hợp lệ cũng vậy, nên chỉ cộng ít | V5.4 khách mới hợp lệ |
| R02 | `DEV_MULTI_NEW_ACCOUNTS` | voucher_apply, place_order | F02 ≥ 3 → +35; F02 ≥ 5 → +50 (lấy bậc cao nhất) | +35 / +50 | **S** | Một thiết bị sinh ra nhiều tài khoản mới là dấu hiệu farm rõ nhất | Máy dùng chung (quán net, máy gia đình); giảm thiểu bằng cửa sổ 30 ngày và chỉ đếm tài khoản mới |
| R03 | `ADDR_MULTI_ACCOUNTS` | voucher_apply, place_order | F03 ≥ 3 → +20; F03 ≥ 5 → +30 | +20 / +30 | M | Farm thường gom hàng về một địa chỉ | **V5.1 gia đình**, văn phòng |
| R04 | `IP_MULTI_NEW_ACCOUNTS` | voucher_apply | F04 ≥ 3 | +10 | W | Có giá trị khi đi kèm tín hiệu khác | **V5.1 gia đình chung Wi-Fi**, ký túc xá |
| R05 | `VCH_VELOCITY` | voucher_apply | F05 ≥ 5 | +25 | **S** | Thử voucher liên tục là hành vi dò mã hoặc tự động hóa | Người dùng gõ sai mã vài lần (ngưỡng 5 để chừa chỗ) |
| R06 | `BOT_SPEED` (Recommended) | place_order | F06: đăng ký → đặt hàng < 60 giây **và** 0 lượt xem sản phẩm | +20 | M | Người thật hiếm khi mua mà không xem sản phẩm nào | Khách mua lại qua link trực tiếp (giảm thiểu: chỉ áp cho tài khoản mới) |
| R07 | `COD_FAIL_RATE` | payment_options, place_order (COD) | F07 `cod_finished` ≥ 3 **và** F08 ≥ 0,30 → +45; F08 ≥ 0,20 → +40 (ADR-014; trước đó +25) | +45 / +40 | **S** (bậc 0,30) / M | Lịch sử bùng hàng là căn cứ trực tiếp nhất cho rủi ro COD | Khách gặp sự cố giao hàng thật (giảm thiểu: làm mượt + tối thiểu 3 đơn) |
| R08 | `COD_HIGH_VALUE_LOW_HISTORY` | place_order (COD) | F11 ≥ 3.000.000đ **và** F09 < 2 → +40; F11 ≥ 5.000.000đ **và** F09 < 2 → +70 | +40 / +70 | M / **S** (bậc 5 triệu) | Đơn COD giá trị cao từ người chưa có lịch sử: thiệt hại lớn nếu bùng | Khách mới mua món đắt thật (được giữ đơn và gọi xác minh, không bị chặn) |
| R09 | `GOOD_HISTORY` (luật tích cực) | payment_options, place_order | F09 ≥ 10 **và** tỷ lệ thất bại thực ≤ 5% | **−30** | — | Ghi nhận khách uy tín, giảm chặn nhầm | — (đây là luật giảm chặn nhầm cho **V5.2, V5.3**) |
| R11 | `ADDR_VOUCHER_RING` (v2) | place_order | Voucher tân thủ **và** F12 ≥ 5 **và** F13 ≥ 0,75 | +25 | M | Farm phân tán: nhiều tài khoản mới cùng nhà nhưng mỗi người một mạng | **Nhóm ở trọ dùng 4G riêng** (≈15% bị gỡ voucher trên tập test v2); giảm thiểu: chỉ gỡ voucher, khiếu nại được |
| R12 | `PHONE_MULTI_ACCOUNTS` (v3) | place_order | F14: SĐT ở ≥ 2 địa chỉ **và** ≥ 3 tài khoản → +15; ≥ 5 → +25 | 15 / 25 | M | Farm chia nhiều điểm nhận nhưng một người đi nhận | Người nhận hộ bạn bè ở nhiều nơi (cả nhà chung SĐT ở **một** địa chỉ thì không trừ) |
| R13 | `ADDRESS_HOPPING` (v3) | place_order | F15 ≥ 3 → +10 | 10 | W | Đổi địa chỉ liên tục | Người hay gửi quà |
| R14 | `VOUCHER_SUBSIDY_HIGH` (v3) | voucher_apply, place_order | F16 ≥ 15% → +10; ≥ 25% → +20 | 10 / 20 | M | Sàn bù quá nhiều tiền cho một tài khoản | Khách chỉ mua khi có khuyến mãi |
| R15 | `PROFITABLE_CUSTOMER` (v3, tích cực) | voucher_apply, place_order | F09 ≥ 3 **và** F16 < 10% | **−15** | — | Hồi điểm cho khách mua đều, ít phụ thuộc voucher | — |
| R10 | `COD_OPEN_ORDERS` | payment_options, place_order (COD) | F10 ≥ 3 | +25 | M | "Treo" nhiều đơn COD cùng lúc (từ kịch bản 4 của đề cương) | Khách mua nhiều đợt khuyến mãi liền nhau |
| R17 | `COD_OPEN_NEW_ACCOUNT` | payment_options, place_order (COD) | F09 `delivered_orders` < 1 **và** F10 `open_cod_orders` ≥ 2 (ADR-014) | +40 | M | Tài khoản chưa nhận đơn nào đã treo nhiều đơn COD: đơn thứ 3 phải trả trước | Khách mới mua nhiều đợt liền nhau (giảm thiểu: chỉ ẩn COD, vẫn mua được bằng trả trước; không trừ điểm tin cậy) |
| R18 | `CLUSTER_CHAIN` | voucher_apply, place_order (voucher) | dùng mã người mới **và** cụm nối qua cả thiết bị lẫn điểm nhận hàng (F18 `cluster_link_types` = 2) **và** `cluster_voucher_accounts_30d` ≥ 5 (ADR-016) | +40 | M | Farm nối chuỗi: mỗi cặp tài khoản chỉ chung một thứ nên R02/R03/R12 không thấy, cả chuỗi là một cụm gom mã | Đại gia đình, ký túc xá dùng chung máy và địa chỉ (giảm thiểu: chỉ đi qua tài khoản mới, cần ≥ 2 loại điểm chung, chỉ gỡ mã) |

Ngưỡng tiền (3 triệu, 5 triệu) là **giả định** cho shop mô phỏng [XM], cấu hình được.

## 4. Ma trận quyết định

| Context | Điều kiện | Quyết định | Hành động |
|---|---|---|---|
| `voucher_apply` | score < 50 | `ALLOW` | Áp voucher |
| | 50 ≤ score | `ALLOW_WITH_RESTRICTION` | Gỡ voucher, thông điệp chung chung |
| | score ≥ 80 **hoặc** R02 ở bậc ≥ 5 | (như trên) + **mở case cụm** | Worker mở hoặc gộp vào case theo `device_id`/địa chỉ, mỗi cụm chỉ một case đang mở |
| `payment_options` | score < 40 | `ALLOW` | Hiện COD |
| | score ≥ 40 | `ALLOW_WITH_RESTRICTION` | Ẩn COD, chỉ hiện trả trước |
| `place_order` (COD) | score < 40 | `ALLOW` | Đơn `CONFIRMED` |
| | 40 ≤ score < 70 | `ALLOW_WITH_RESTRICTION` | Từ chối COD, yêu cầu chọn trả trước (đơn chưa được tạo) |
| | score ≥ 70 **và** có ≥ 1 luật mạnh | `REVIEW` | Đơn `PENDING_REVIEW`, chưa bàn giao vận chuyển, mở case |
| | score ≥ 90 **và** có ≥ 2 luật mạnh | `BLOCK` | Từ chối đặt hàng, mở case. **Không dùng trong demo**; định nghĩa để đủ vòng đời |
| `place_order` (trả trước) | Chỉ chấm lại voucher (R01–R05) | Như `voucher_apply` | Gỡ voucher nếu cần; tiền đã trả trước nên rủi ro COD không áp dụng |

**Nguyên tắc an toàn:**
- `REVIEW` và `BLOCK` **luôn cần ít nhất một luật mạnh**. Không bao giờ giữ hay chặn chỉ vì các tín hiệu yếu cộng dồn.
- Thông điệp cho khách **không bao giờ** nêu tên luật hay tín hiệu.
- Khi Risk module lỗi (chính sách fail-open/fail-closed, cấu hình được): `voucher_apply` → fail-open (cho áp); `place_order` COD ≥ 3 triệu → fail-closed (yêu cầu trả trước); còn lại fail-open. Mọi lần lỗi đều ghi log.

## 5. Tính thử trên các nhân vật của kịch bản demo

| Nhân vật (cảnh) | Context | Luật khớp | Điểm | Kết quả | Khớp kịch bản? |
|---|---|---|---|---|---|
| Minh, khách **mới** hợp lệ, đăng ký hôm qua (1) | voucher_apply | R01 (+10) | 10 | ALLOW | ✓ |
| Farm, tài khoản thứ 1 (2) | voucher_apply | R01 | 10 | ALLOW | ✓ (chưa đủ tín hiệu) |
| Farm, thứ 4 (F02=2, F03=4, F04=4) | voucher_apply | R01 + R03(+20) + R04(+10) | 40 | ALLOW | ✓ |
| Farm, thứ 5 (F02=2, F03=5, F04=5) | voucher_apply | R01 + R03(+30) + R04 | 50 | Gỡ voucher | ✓ |
| Farm, thứ 7 (F02=3, F03=7) | voucher_apply | R01 + R02(+35) + R03(+30) + R04 | 85 | Gỡ voucher + mở case cụm | ✓ |
| Gia đình, người thứ 4: cùng IP, cùng địa chỉ, khác thiết bị (4) | voucher_apply | R01 + R03(+20) + R04(+10) | 40 | ALLOW | ✓ |
| Khang: 5 đơn COD xong, 4 thất bại → F08 = 5/15 = 0,33 (5a) | payment_options | R07(+45) | 45 | Ẩn COD | ✓ |
| Tài khoản mới, COD 5,5 triệu (5b) | place_order | R08(+70, mạnh) | 70 | REVIEW → Chờ xác minh | ✓ |
| Lan: 30 đơn giao thành công, COD 4 triệu (5c) | place_order | R09(−30); R08 không khớp vì F09 ≥ 2 | 0 | ALLOW | ✓ |
| Khách thường: 5 đơn COD, 1 thất bại → F08 = 2/15 = 0,13 | payment_options | — | 0 | Hiện COD | ✓ |
| Khách mới: 1 đơn COD, thất bại 1/1 | payment_options | — (cod_finished < 3) | 0 | Hiện COD | ✓ (nhờ làm mượt + tối thiểu 3 đơn) |

Giả định thứ tự farm: 20 tài khoản luân phiên trên 3 thiết bị, cùng 1 địa chỉ và 1 IP.

**Giới hạn đã biết (nói thẳng khi bảo vệ):** gia đình **5 người trở lên** cùng địa chỉ và cùng Wi-Fi, ai cũng dùng voucher tân thủ, sẽ có người thứ 5 bị gỡ voucher (10 + 30 + 10 = 50). Đây là đánh đổi có chủ đích: chính sách "voucher tân thủ" vốn để thu hút **người dùng mới thật**. Cách giảm thiểu: khiếu nại, hoặc analyst đưa địa chỉ vào danh sách ngoại lệ (Recommended).

## 6. Biểu diễn luật dưới dạng dữ liệu (cấu hình được, có phiên bản)

Code định nghĩa **loại luật** (hàm thuần); CSDL lưu **thể hiện luật** cùng tham số và phiên bản. Ví dụ:

```json
{
  "code": "DEV_MULTI_NEW_ACCOUNTS",
  "version": 1,
  "type": "count_threshold_tiers",
  "contexts": ["voucher_apply", "place_order"],
  "feature": "new_accounts_on_device_30d",
  "params": { "tiers": [ { "gte": 5, "points": 50 }, { "gte": 3, "points": 35 } ] },
  "strength": "strong",
  "enabled": true,
  "reason_template": "{value} tài khoản mới trên cùng thiết bị trong 30 ngày (ngưỡng {threshold})"
}
```

Các loại luật cần cài đặt cho v0:

| Loại luật | Dùng cho |
|---|---|
| `count_threshold_tiers` (đặc trưng đếm, nhiều bậc) | R02, R03, R04, R05, R10 |
| `rate_threshold_tiers` (tỷ lệ có điều kiện số mẫu tối thiểu) | R07 |
| `compound` (nhiều điều kiện AND) | R01, R06, R08, R09 |

Ma trận quyết định (mục 4) cũng là **cấu hình**, có phiên bản riêng.

## 7. Unit test tối thiểu cho mỗi luật
Với mỗi luật, viết ít nhất:
1. Ngay **dưới ngưỡng**: không khớp.
2. **Đúng ngưỡng**: khớp, đúng số điểm.
3. **Bậc cao**: lấy đúng bậc cao nhất, không cộng dồn các bậc.
4. **Trường hợp biên của hard negative** liên quan (ví dụ R07 với 1/1 đơn thất bại → không khớp).
5. **Context không áp dụng**: không khớp (ví dụ R07 ở `voucher_apply`).

Và test cho ma trận quyết định: score 69 cộng luật mạnh → không REVIEW; score 70 không có luật mạnh → không REVIEW; score 70 có luật mạnh → REVIEW.

## 8. Việc tiếp theo
- Luca duyệt danh sách luật và các con số.
- Thiết kế ERD: các bảng cần để tính F01–F11 (tài khoản, thiết bị, địa chỉ, sự kiện, đơn, giao hàng, voucher) và lưu quyết định, luật, case.
