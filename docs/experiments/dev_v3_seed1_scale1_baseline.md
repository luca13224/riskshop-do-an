# Kết quả mô phỏng: tập dev_v3 (seed 1, scale 1)

> Tạo lúc 2026-11-05 12:39 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `f270cd66dfcbe367…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 50 | FN = 33 |
| **Hợp lệ (nhãn thật)** | FP = 11 | TN = 189 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 82.0% (50/61; KTC 95%: 70.5%–89.6%) |
| Recall (tất cả kiểu lạm dụng) | 60.2% (50/83; KTC 95%: 49.5%–70.1%) |
| Recall: kiểu đã biết | 60.2% (50/83; KTC 95%: 49.5%–70.1%) |
| Recall: biến thể chưa biết | — |
| FPR (tất cả khách hợp lệ) | 5.5% (11/200; KTC 95%: 3.1%–9.6%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/130; KTC 95%: 0.0%–2.9%) |
| FPR: hard negative | 15.7% (11/70; KTC 95%: 9.0%–26.0%) |
| F1 | 69.4% |
| Accuracy | 84.5% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 8 | 8 | 100% | 3 khóa do liên kết | 0 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 7 | 7 | 100% | 4 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 5 | 0 | 0% | — | 3 |
| Bùng hàng COD | Lạm dụng | 12 | 7 | 58% | — | 0 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 22 | 0 | 0% | — | 15 |
| Farm voucher | Lạm dụng | 33 | 21 | 64% | — | 12 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 23 | 7 | 30% | — | 16 |
| Khách quen | Hợp lệ | 30 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 8 | 8 | 100% | — | 0 |
| Khách mới bình thường | Hợp lệ | 100 | 0 | 0% | — | 45 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 8 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 27 | 3 | 11% | — | 14 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 7/12 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 4/4 |
| Farm voucher | 6/6 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 5/5 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 3/3 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 29.3%; Risk Engine gắn cờ 21.6% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | 82.0% | 60.2% | 69.4% | 5.5% | 84.5% | 50 / 11 / 33 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 70.7% | 0 / 0 / 83 |
| B1 · Luật thủ công (2 luật cứng) | 67.5% | 62.6% | 65.0% | 12.5% | 80.2% | 52 / 25 / 31 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | 29.3% | 21.6% | 24.9% | 21.6% | 61.8% | 17.9 / 43.1 / 65.1 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 8/8, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 7/7, Người nhà dùng chung máy với tài khoản bị khóa 3/5, Bùng hàng COD 12/12, Farm voucher 25/33, Khách quen 22/30.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **28** lượt; khách hợp lệ dùng: 77 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 2, Bùng hàng COD CONFIRMED = 5, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 10, Khách quen CONFIRMED = 30, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 4, Khách mới bình thường CONFIRMED = 38, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 24, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 14

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 552 lượt): p50 10.57 ms · p95 13.63 ms · p99 16.94 ms
- Toàn bộ request `payment_options` (138 lượt, trong cùng tiến trình, không qua mạng): p50 21.63 ms · p95 27.81 ms · p99 31.93 ms
- Toàn bộ request `place_order` (276 lượt, trong cùng tiến trình, không qua mạng): p50 32.96 ms · p95 40.19 ms · p99 47.11 ms
- Toàn bộ request `voucher_apply` (180 lượt, trong cùng tiến trình, không qua mạng): p50 29.27 ms · p95 37.32 ms · p99 43.39 ms
- Thời gian chạy: 46.7 giây cho 1495 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
