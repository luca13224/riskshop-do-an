# Kết quả mô phỏng: tập dev_v5 (seed 1, scale 1)

> Tạo lúc 2026-11-05 20:31 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `e78d4daaf03d03e0…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 62 | FN = 51 |
| **Hợp lệ (nhãn thật)** | FP = 30 | TN = 231 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 67.4% (62/92; KTC 95%: 57.3%–76.1%) |
| Recall (tất cả kiểu lạm dụng) | 54.9% (62/113; KTC 95%: 45.7%–63.7%) |
| Recall: kiểu đã biết | 54.9% (62/113; KTC 95%: 45.7%–63.7%) |
| Recall: biến thể chưa biết | — |
| FPR (tất cả khách hợp lệ) | 11.5% (30/261; KTC 95%: 8.2%–15.9%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/130; KTC 95%: 0.0%–2.9%) |
| FPR: hard negative | 22.9% (30/131; KTC 95%: 16.5%–30.8%) |
| F1 | 60.5% |
| Accuracy | 78.3% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 6 | 6 | 100% | 6 khóa do liên kết | 0 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 7 | 7 | 100% | 7 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 5 | 0 | 0% | — | 3 |
| Đại gia đình dùng chung máy, giao về nhà bố mẹ | Hard negative | 26 | 3 | 12% | — | 9 |
| Bùng hàng COD | Lạm dụng | 12 | 12 | 100% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 5 | 5 | 100% | — | 0 |
| Ký túc xá chung địa chỉ, chung máy tính | Hard negative | 27 | 10 | 37% | — | 2 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 22 | 1 | 5% | — | 18 |
| Farm voucher | Lạm dụng | 33 | 21 | 64% | — | 12 |
| Farm nối chuỗi (thiết bị → SĐT → địa chỉ) | Lạm dụng | 27 | 4 | 15% | — | 23 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 23 | 7 | 30% | — | 16 |
| Khách quen | Hợp lệ | 30 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 8 | 8 | 100% | — | 0 |
| Khách mới đặt nhiều đơn COD liền nhau | Hard negative | 8 | 2 | 25% | — | 0 |
| Khách mới bình thường | Hợp lệ | 100 | 0 | 0% | — | 45 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 8 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 27 | 6 | 22% | — | 13 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 12/12 |
| Farm voucher | 6/6 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 4/4 |
| Farm nối chuỗi (thiết bị → SĐT → địa chỉ) | 4/4 |
| Tài khoản mới treo nhiều đơn COD | 5/5 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 5/5 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 3/3 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 30.2%; Risk Engine gắn cờ 24.6% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | 67.4% | 54.9% | 60.5% | 11.5% | 78.3% | 62 / 30 / 51 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 69.8% | 0 / 0 / 113 |
| B1 · Luật thủ công (2 luật cứng) | 59.2% | 51.3% | 55.0% | 15.3% | 74.6% | 58 / 40 / 55 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | 30.2% | 24.6% | 27.1% | 24.6% | 60.1% | 27.8 / 64.2 / 85.2 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 6/6, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 7/7, Người nhà dùng chung máy với tài khoản bị khóa 3/5, Đại gia đình dùng chung máy, giao về nhà bố mẹ 6/26, Bùng hàng COD 12/12, Ký túc xá chung địa chỉ, chung máy tính 9/27, Farm voucher 25/33, Farm nối chuỗi (thiết bị → SĐT → địa chỉ) 8/27, Khách quen 22/30.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **51** lượt; khách hợp lệ dùng: 90 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 3, Đại gia đình dùng chung máy, giao về nhà bố mẹ CONFIRMED = 14, Tài khoản mới treo nhiều đơn COD CONFIRMED = 10, Ký túc xá chung địa chỉ, chung máy tính CONFIRMED = 11, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 12, Khách quen CONFIRMED = 30, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 4, Khách mới đặt nhiều đơn COD liền nhau CONFIRMED = 16, Khách mới bình thường CONFIRMED = 38, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 24, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 20

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 791 lượt): p50 16.48 ms · p95 23.5 ms · p99 27.63 ms
- Toàn bộ request `payment_options` (209 lượt, trong cùng tiến trình, không qua mạng): p50 30.03 ms · p95 39.32 ms · p99 42.7 ms
- Toàn bộ request `voucher_apply` (235 lượt, trong cùng tiến trình, không qua mạng): p50 44.6 ms · p95 55.76 ms · p99 63.71 ms
- Toàn bộ request `place_order` (389 lượt, trong cùng tiến trình, không qua mạng): p50 48.27 ms · p95 62.39 ms · p99 70.51 ms
- Thời gian chạy: 90.4 giây cho 1972 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
