# Kết quả mô phỏng: tập dev_v4 (seed 1, scale 1)

> Tạo lúc 2026-11-05 13:37 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `f270cd66dfcbe367…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 50 | FN = 38 |
| **Hợp lệ (nhãn thật)** | FP = 11 | TN = 195 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 82.0% (50/61; KTC 95%: 70.5%–89.6%) |
| Recall (tất cả kiểu lạm dụng) | 56.8% (50/88; KTC 95%: 46.4%–66.7%) |
| Recall: kiểu đã biết | 56.8% (50/88; KTC 95%: 46.4%–66.7%) |
| Recall: biến thể chưa biết | — |
| FPR (tất cả khách hợp lệ) | 5.3% (11/206; KTC 95%: 3.0%–9.3%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/130; KTC 95%: 0.0%–2.9%) |
| FPR: hard negative | 14.5% (11/76; KTC 95%: 8.3%–24.1%) |
| F1 | 67.1% |
| Accuracy | 83.3% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 7 | 7 | 100% | 2 khóa do liên kết | 0 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 8 | 8 | 100% | 5 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 5 | 0 | 0% | — | 3 |
| Bùng hàng COD | Lạm dụng | 12 | 7 | 58% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 5 | 0 | 0% | — | 0 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 22 | 0 | 0% | — | 17 |
| Farm voucher | Lạm dụng | 33 | 21 | 64% | — | 12 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 23 | 7 | 30% | — | 16 |
| Khách quen | Hợp lệ | 30 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 8 | 8 | 100% | — | 0 |
| Khách mới đặt nhiều đơn COD liền nhau | Hard negative | 8 | 0 | 0% | — | 0 |
| Khách mới bình thường | Hợp lệ | 100 | 0 | 0% | — | 46 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 8 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 25 | 3 | 12% | — | 16 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 7/12 |
| Farm voucher | 6/6 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 4/4 |
| Tài khoản mới treo nhiều đơn COD | 0/5 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 3/3 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 5/5 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 29.9%; Risk Engine gắn cờ 20.8% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | 82.0% | 56.8% | 67.1% | 5.3% | 83.3% | 50 / 11 / 38 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 70.1% | 0 / 0 / 88 |
| B1 · Luật thủ công (2 luật cứng) | 67.5% | 59.1% | 63.0% | 12.1% | 79.2% | 52 / 25 / 36 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | 29.9% | 20.8% | 24.5% | 20.8% | 61.7% | 18.3 / 42.7 / 69.7 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 7/7, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 8/8, Người nhà dùng chung máy với tài khoản bị khóa 3/5, Bùng hàng COD 12/12, Farm voucher 25/33, Khách quen 22/30.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **28** lượt; khách hợp lệ dùng: 82 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 3, Bùng hàng COD CONFIRMED = 5, Tài khoản mới treo nhiều đơn COD CONFIRMED = 18, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 13, Khách quen CONFIRMED = 30, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 4, Khách mới đặt nhiều đơn COD liền nhau CONFIRMED = 21, Khách mới bình thường CONFIRMED = 38, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 24, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 14

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 637 lượt): p50 13.62 ms · p95 18.9 ms · p99 22.57 ms
- Toàn bộ request `voucher_apply` (178 lượt, trong cùng tiến trình, không qua mạng): p50 37.58 ms · p95 47.9 ms · p99 55.44 ms
- Toàn bộ request `place_order` (313 lượt, trong cùng tiến trình, không qua mạng): p50 42.95 ms · p95 55.3 ms · p99 63.21 ms
- Toàn bộ request `payment_options` (181 lượt, trong cùng tiến trình, không qua mạng): p50 28.32 ms · p95 35.98 ms · p99 46.96 ms
- Thời gian chạy: 69.9 giây cho 1602 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
