# Thiết kế Risk Engine v2 — đặc trưng cụm quanh địa chỉ (R11)

> Trạng thái: **đã duyệt và cài đặt (2026-10-31)**, ngưỡng F12 chốt là **5** sau khi hiệu chỉnh trên tập dev_v2 (mục 9). Quyết định: ADR-008.
> Ngày: 2026-10-31. Theo quy trình skill `risk-rule`.

## 1. Bài toán

Kết quả v1 trên tập test (TEST_PLAN mục 3): biến thể **farm phân tán** lọt 100%.
Farm này: mỗi tài khoản một thiết bị riêng, một IP riêng, địa chỉ viết khác nhau nhưng chuẩn hóa về **cùng một địa chỉ**.
Tài khoản thứ n chỉ khớp R01 (+10) và R03 (+30 khi ≥ 5 tài khoản/địa chỉ) = 40 < 50, nên voucher không bị gỡ.

Nhìn từng tín hiệu thì không đủ. Nhìn **đồ thị liên kết** quanh địa chỉ đó thì thấy điểm lạ: nhiều tài khoản **mới**, cùng dùng voucher tân thủ, cùng giao về một nhà, nhưng **mỗi người vào mạng từ một nơi khác nhau**.
Một hộ gia đình thật thì ngược lại: chung địa chỉ **và** thường chung Wi-Fi.

## 2. Đặc trưng mới (lấy từ đồ thị: nút địa chỉ → các tài khoản → các IP của họ)

| Mã | Tên | Cách tính | Ghi chú |
|---|---|---|---|
| F12 | `new_accounts_on_address_7d` | Số tài khoản khách **mới (< 7 ngày)** có địa chỉ đã chuẩn hóa trùng địa chỉ đơn này, tạo trong 7 ngày, tính cả hiện tại | Khác F03: F03 đếm mọi tài khoản trong 30 ngày |
| F13 | `address_ip_diversity_7d` | Số IP (bản băm) khác nhau mà các tài khoản ở F12 đã dùng trong 7 ngày, chia cho F12 | ≈ 1: mỗi tài khoản một mạng riêng; thấp: dùng chung mạng |

- Chỉ dùng dữ liệu **trước** thời điểm đánh giá (địa chỉ và IP của đơn hiện tại được ghi ngay trước khi chấm, như F03).
- Một truy vấn, dùng index sẵn có: `addresses(norm_hash, created_at)` và khóa chính `user_ips(user_id, ip_hash)`. Không cần migration.
- Chỉ tính ở `place_order` (lúc áp voucher chưa có địa chỉ), giống R03.

## 3. Luật mới

| Mã | Tên | Context | Điều kiện | Điểm | Độ mạnh | Chính sách |
|---|---|---|---|---|---|---|
| R11 | `ADDR_VOUCHER_RING` | place_order | Voucher tân thủ **và** F12 ≥ 4 **và** F13 ≥ 0,75 | +25 | Trung bình | voucher |

- **Vì sao "trung bình":** chỉ góp điểm để gỡ voucher, không bao giờ đủ để giữ hay chặn đơn (ma trận yêu cầu luật mạnh). Sai thì khách chỉ mất voucher và khiếu nại được (ADR-006).
- **Vì sao 4 và 0,75:** 4 là mức mà một nhà có nhiều tài khoản mới **cùng lúc** đã bất thường; 0,75 cho phép một hai người trong nhóm dùng chung mạng. Đây là lập luận chuyên gia **[ĐX]**, chỉ được hiệu chỉnh trên tập dev.
- Dùng loại luật `compound` sẵn có, không thêm code luật mới. Lý do hiển thị: "{F12} tài khoản mới cùng địa chỉ giao hàng, phần lớn truy cập từ mạng khác nhau".

## 4. Tính thử (tay)

| Trường hợp | Luật khớp | Điểm | Kết quả |
|---|---|---|---|
| Farm phân tán, tài khoản thứ 4 (F03 = 4, F12 = 4, F13 = 1,0) | R01 + R03(+20) + R11 | 55 | Gỡ voucher (v1: 30, lọt) |
| Farm phân tán, tài khoản thứ 5+ | R01 + R03(+30) + R11 | 65 | Gỡ voucher (v1: 40, lọt) |
| Farm phân tán, tài khoản 1–3 | R01 (+ R03 từ thứ 3) | ≤ 30 | Lọt (không tránh được: chưa đủ dấu vết) |
| Gia đình 4 người, chung Wi-Fi (F13 = 0,25) | R01 + R03(+20) + R04(+10) | 40 | Cho phép, **không đổi so với v1** |
| Gia đình 5–6 người, chung Wi-Fi | R01 + R03(+30) + R04 | 50 | Gỡ voucher, **giữ nguyên giới hạn đã biết của v1** |
| Khách mới lẻ | R01 | 10 | Cho phép |

## 5. Hard negative mới (nói thẳng)

- **Gia đình hoặc nhóm bạn ở trọ dùng 4G riêng** (mỗi người một IP), 4+ người cùng tạo tài khoản mới trong 7 ngày, đều dùng voucher tân thủ: bị gỡ voucher từ người thứ 4. Bộ mô phỏng **chưa có** persona này → cần thêm vào tập dev để đo.
- **Ký túc xá, văn phòng** có thể cùng địa chỉ: nhưng thường chung IP (F13 thấp) nên ít bị ảnh hưởng.
- Kẻ gian thích nghi: dùng chung một proxy cho cả farm → F13 thấp, R11 không khớp, nhưng khi đó R04 (IP) lại khớp. Đây là cuộc đua; R11 chỉ nâng chi phí của kẻ gian.

## 6. Giao thức đánh giá (chống "học thuộc đề")

Điểm quan trọng nhất khi bảo vệ: **farm phân tán là biến thể ta đã nhìn thấy trong tập test v1**. Thiết kế R11 sau khi biết nó, rồi đo lại trên chính nó, là học thuộc đề. Vì vậy:

1. **Tập dev mới** thêm hai persona: farm phân tán (tham số khác test) và hard negative "nhóm dùng 4G riêng". Chỉ hiệu chỉnh R11 trên tập dev này.
2. **Khóa bộ luật v2** (ghi dấu vân tay) trước khi chạy test.
3. **Tập test mới, seed 3**, chạy một lần. Báo cáo tách riêng:
   - farm phân tán → giờ là kiểu **đã biết**;
   - một **biến thể chưa biết mới**, định nghĩa trước khi chạy và không tinh chỉnh theo nó (đề xuất: farm "trà trộn" — chung một proxy như gia đình, mỗi tài khoản cách nhau vài ngày để lọt cửa sổ 7 ngày).
4. So sánh v1 và v2 trên **cùng tập test seed 3**: precision, recall theo kiểu, FPR khách thường, FPR từng loại hard negative, độ trễ p95.
5. Kỳ vọng trung thực: recall farm phân tán tăng (không đạt 100% vì 3 tài khoản đầu luôn lọt); biến thể chưa biết mới có thể vẫn lọt — đó là kết quả, không phải thất bại.

## 7. Chia việc (theo CLAUDE.md: phần lõi Luca tự viết, Claude review)

| Việc | Ai |
|---|---|
| Duyệt thiết kế, chốt con số R11 | Luca |
| Viết khai báo R11 trong `risk/seed.py` (dữ liệu luật, ~8 dòng) | **Luca**, Claude review |
| Tính F12, F13 trong `features.py` + unit test 5 trường hợp (mục 7 RULES_V0) | Claude, Luca đọc và giải thích lại |
| Persona mới cho dev/test, chạy dev, khóa luật, chạy test seed 3, viết kết quả | Claude, Luca duyệt số liệu |
| Cập nhật RULES_V0 → v2, ADR-008, TEST_PLAN | Claude |

## 8. Không làm (và lý do)

- **Cụm 2 bước trên toàn đồ thị lúc checkout:** tốn nhiều truy vấn mỗi đơn (độ trễ), khó giải thích; giữ cho màn hình điều tra của Console.
- **ML / phát hiện cộng đồng (community detection):** chưa có dữ liệu thật để huấn luyện; rule 1 bước đồ thị đã giải thích được và đo được.

## 9. Hiệu chỉnh trên tập dev_v2 (seed 1) và lựa chọn ngưỡng

Chạy cùng một dân số dev_v2, có và không có R11; sau đó tính lại "nếu đổi ngưỡng thì sao" từ `features_snapshot` (chỉ dùng tập dev).

| Phương án | Farm phân tán bắt thêm | Nhóm trọ 4G bị gỡ voucher nhầm | Độ chính xác riêng của R11 |
|---|---|---|---|
| F12 ≥ 4 (thiết kế ban đầu) | 11/23 | 7/27 | 61% |
| **F12 ≥ 5 (chốt)** | 7/23 | 3/27 | 70% |

- Độ phân tán mạng (0,75 → 1,0) và số điểm (20 → 25) **không** làm thay đổi kết quả: nhóm trọ dùng 4G riêng và farm phân tán đều có độ phân tán 1,0. Chỉ ngưỡng số tài khoản tạo khác biệt.
- Kết luận trung thực: đặc trưng mạng **không phân biệt được** hai nhóm này; ngưỡng chỉ dời điểm cân bằng. Luca chọn F12 ≥ 5, ưu tiên giảm gỡ nhầm.
- Phát hiện phụ: ở bộ v1, mọi farm cùng loại trong một lần chạy vô tình giao về **một** địa chỉ. Bộ v2 (`dev_v2`, `test_v2`) cho mỗi farm một địa chỉ riêng; bộ v1 giữ nguyên để kết quả cũ tái lập được.
