# Kết quả mô phỏng: tập dev_v4 (seed 1, scale 1)

> Tạo lúc 2026-11-05 13:41 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `02830f287e740a30…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 58 | FN = 30 |
| **Hợp lệ (nhãn thật)** | FP = 11 | TN = 195 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 84.1% (58/69; KTC 95%: 73.7%–90.9%) |
| Recall (tất cả kiểu lạm dụng) | 65.9% (58/88; KTC 95%: 55.5%–75.0%) |
| Recall: kiểu đã biết | 65.9% (58/88; KTC 95%: 55.5%–75.0%) |
| Recall: biến thể chưa biết | — |
| FPR (tất cả khách hợp lệ) | 5.3% (11/206; KTC 95%: 3.0%–9.3%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/130; KTC 95%: 0.0%–2.9%) |
| FPR: hard negative | 14.5% (11/76; KTC 95%: 8.3%–24.1%) |
| F1 | 73.9% |
| Accuracy | 86.1% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 7 | 7 | 100% | 2 khóa do liên kết | 0 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 8 | 8 | 100% | 5 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 5 | 0 | 0% | — | 3 |
| Bùng hàng COD | Lạm dụng | 12 | 12 | 100% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 5 | 3 | 60% | — | 0 |
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
| Bùng hàng COD | 12/12 |
| Farm voucher | 6/6 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 4/4 |
| Tài khoản mới treo nhiều đơn COD | 3/5 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 3/3 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 5/5 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 29.9%; Risk Engine gắn cờ 23.5% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | 84.1% | 65.9% | 73.9% | 5.3% | 86.1% | 58 / 11 / 30 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 70.1% | 0 / 0 / 88 |
| B1 · Luật thủ công (2 luật cứng) | 67.5% | 59.1% | 63.0% | 12.1% | 79.2% | 52 / 25 / 36 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | 29.9% | 23.5% | 26.3% | 23.5% | 60.7% | 20.7 / 48.3 / 67.3 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 7/7, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 8/8, Người nhà dùng chung máy với tài khoản bị khóa 3/5, Bùng hàng COD 12/12, Farm voucher 25/33, Khách quen 22/30.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **28** lượt; khách hợp lệ dùng: 82 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 3, Tài khoản mới treo nhiều đơn COD CONFIRMED = 15, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 13, Khách quen CONFIRMED = 30, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 4, Khách mới đặt nhiều đơn COD liền nhau CONFIRMED = 21, Khách mới bình thường CONFIRMED = 38, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 24, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 14

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 629 lượt): p50 13.32 ms · p95 17.03 ms · p99 20.56 ms
- Toàn bộ request `voucher_apply` (178 lượt, trong cùng tiến trình, không qua mạng): p50 37.63 ms · p95 47.65 ms · p99 51.39 ms
- Toàn bộ request `place_order` (305 lượt, trong cùng tiến trình, không qua mạng): p50 42.0 ms · p95 52.45 ms · p99 56.02 ms
- Toàn bộ request `payment_options` (181 lượt, trong cùng tiến trình, không qua mạng): p50 27.61 ms · p95 32.06 ms · p99 34.41 ms
- Thời gian chạy: 68.0 giây cho 1602 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
