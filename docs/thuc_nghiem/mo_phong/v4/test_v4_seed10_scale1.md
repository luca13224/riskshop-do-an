# Kết quả mô phỏng: tập test_v4 (seed 10, scale 1)

> Tạo lúc 2026-11-05 18:39 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `e0240c5bbcce8604…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 98 | FN = 80 |
| **Hợp lệ (nhãn thật)** | FP = 27 | TN = 286 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 78.4% (98/125; KTC 95%: 70.4%–84.7%) |
| Recall (tất cả kiểu lạm dụng) | 55.1% (98/178; KTC 95%: 47.7%–62.2%) |
| Recall: kiểu đã biết | 73.1% (98/134; KTC 95%: 65.1%–79.9%) |
| Recall: biến thể chưa biết | 0.0% (0/44; KTC 95%: 0.0%–8.0%) |
| FPR (tất cả khách hợp lệ) | 8.6% (27/313; KTC 95%: 6.0%–12.3%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 21.9% (27/123; KTC 95%: 15.6%–30.0%) |
| F1 | 64.7% |
| Accuracy | 78.2% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 14 | 14 | 100% | 14 khóa do liên kết | 0 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | Lạm dụng (chưa biết) | 6 | 0 | 0% | — | 6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 12 | 12 | 100% | 12 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 8 | 0 | 0% | — | 6 |
| Bùng hàng COD | Lạm dụng | 15 | 15 | 100% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 6 | 100% | — | 0 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 49 | 8 | 16% | — | 29 |
| Farm voucher | Lạm dụng | 53 | 37 | 70% | — | 16 |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 38 | 0 | 0% | — | 38 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 34 | 14 | 41% | — | 20 |
| Khách quen | Hợp lệ | 40 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% | — | 0 |
| Khách mới đặt nhiều đơn COD liền nhau | Hard negative | 12 | 7 | 58% | — | 0 |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% | — | 79 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 34 | 2 | 6% | — | 20 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 15/15 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 5/5 |
| Tài khoản mới treo nhiều đơn COD | 6/6 |
| Farm voucher | 8/8 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 0/5 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 8/8 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | 0/6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 4/4 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 36.2%; Risk Engine gắn cờ 25.5% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | 78.4% | 55.1% | 64.7% | 8.6% | 78.2% | 98 / 27 / 80 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 63.7% | 0 / 0 / 178 |
| B1 · Luật thủ công (2 luật cứng) | 66.0% | 36.0% | 46.6% | 10.5% | 70.1% | 64 / 33 / 114 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | 36.2% | 25.5% | 29.9% | 25.5% | 56.8% | 45.3 / 79.7 / 132.7 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 8/14, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 12/12, Người nhà dùng chung máy với tài khoản bị khóa 6/8, Bùng hàng COD 15/15, Farm voucher 29/53, Khách quen 27/40.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **80** lượt; khách hợp lệ dùng: 134 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 3, Tài khoản mới treo nhiều đơn COD CONFIRMED = 12, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 29, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 3, Khách mới đặt nhiều đơn COD liền nhau CONFIRMED = 24, Khách mới bình thường CONFIRMED = 79, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 23

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 1112 lượt): p50 19.77 ms · p95 39.87 ms · p99 67.13 ms
- Toàn bộ request `voucher_apply` (344 lượt, trong cùng tiến trình, không qua mạng): p50 54.3 ms · p95 102.3 ms · p99 174.49 ms
- Toàn bộ request `payment_options` (298 lượt, trong cùng tiến trình, không qua mạng): p50 37.97 ms · p95 69.84 ms · p99 112.54 ms
- Toàn bộ request `place_order` (539 lượt, trong cùng tiến trình, không qua mạng): p50 59.27 ms · p95 125.01 ms · p99 202.9 ms
- Thời gian chạy: 161.1 giây cho 2737 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
