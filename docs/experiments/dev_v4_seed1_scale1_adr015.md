# Kết quả mô phỏng: tập dev_v4 (seed 1, scale 1)

> Tạo lúc 2026-11-05 18:36 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `e0240c5bbcce8604…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 60 | FN = 28 |
| **Hợp lệ (nhãn thật)** | FP = 16 | TN = 190 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 79.0% (60/76; KTC 95%: 68.5%–86.6%) |
| Recall (tất cả kiểu lạm dụng) | 68.2% (60/88; KTC 95%: 57.9%–77.0%) |
| Recall: kiểu đã biết | 68.2% (60/88; KTC 95%: 57.9%–77.0%) |
| Recall: biến thể chưa biết | — |
| FPR (tất cả khách hợp lệ) | 7.8% (16/206; KTC 95%: 4.8%–12.2%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/130; KTC 95%: 0.0%–2.9%) |
| FPR: hard negative | 21.1% (16/76; KTC 95%: 13.4%–31.5%) |
| F1 | 73.2% |
| Accuracy | 85.0% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 7 | 7 | 100% | 7 khóa do liên kết | 0 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 8 | 8 | 100% | 8 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 5 | 0 | 0% | — | 3 |
| Bùng hàng COD | Lạm dụng | 12 | 12 | 100% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 5 | 5 | 100% | — | 0 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 22 | 0 | 0% | — | 17 |
| Farm voucher | Lạm dụng | 33 | 21 | 64% | — | 12 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 23 | 7 | 30% | — | 16 |
| Khách quen | Hợp lệ | 30 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 8 | 8 | 100% | — | 0 |
| Khách mới đặt nhiều đơn COD liền nhau | Hard negative | 8 | 5 | 62% | — | 0 |
| Khách mới bình thường | Hợp lệ | 100 | 0 | 0% | — | 46 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 8 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 25 | 3 | 12% | — | 16 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 12/12 |
| Farm voucher | 6/6 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 4/4 |
| Tài khoản mới treo nhiều đơn COD | 5/5 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 3/3 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 5/5 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 29.9%; Risk Engine gắn cờ 25.9% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | 79.0% | 68.2% | 73.2% | 7.8% | 85.0% | 60 / 16 / 28 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 70.1% | 0 / 0 / 88 |
| B1 · Luật thủ công (2 luật cứng) | 67.5% | 59.1% | 63.0% | 12.1% | 79.2% | 52 / 25 / 36 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | 29.9% | 25.9% | 27.7% | 25.9% | 59.7% | 22.7 / 53.3 / 65.3 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 7/7, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 8/8, Người nhà dùng chung máy với tài khoản bị khóa 3/5, Bùng hàng COD 12/12, Farm voucher 25/33, Khách quen 22/30.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **28** lượt; khách hợp lệ dùng: 82 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 3, Tài khoản mới treo nhiều đơn COD CONFIRMED = 10, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 13, Khách quen CONFIRMED = 30, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 4, Khách mới đặt nhiều đơn COD liền nhau CONFIRMED = 16, Khách mới bình thường CONFIRMED = 38, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 24, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 14

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 624 lượt): p50 13.33 ms · p95 17.79 ms · p99 20.34 ms
- Toàn bộ request `voucher_apply` (178 lượt, trong cùng tiến trình, không qua mạng): p50 37.17 ms · p95 48.09 ms · p99 60.92 ms
- Toàn bộ request `place_order` (300 lượt, trong cùng tiến trình, không qua mạng): p50 41.8 ms · p95 51.12 ms · p99 54.35 ms
- Toàn bộ request `payment_options` (181 lượt, trong cùng tiến trình, không qua mạng): p50 27.68 ms · p95 33.29 ms · p99 39.92 ms
- Thời gian chạy: 67.8 giây cho 1602 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
