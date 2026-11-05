# Kết quả mô phỏng: tập test_v4 (seed 9, scale 1)

> Tạo lúc 2026-11-05 13:55 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `e0240c5bbcce8604…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 95 | FN = 81 |
| **Hợp lệ (nhãn thật)** | FP = 26 | TN = 283 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 78.5% (95/121; KTC 95%: 70.4%–84.9%) |
| Recall (tất cả kiểu lạm dụng) | 54.0% (95/176; KTC 95%: 46.6%–61.2%) |
| Recall: kiểu đã biết | 72.3% (94/130; KTC 95%: 64.1%–79.3%) |
| Recall: biến thể chưa biết | 2.2% (1/46; KTC 95%: 0.4%–11.3%) |
| FPR (tất cả khách hợp lệ) | 8.4% (26/309; KTC 95%: 5.8%–12.0%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 21.9% (26/119; KTC 95%: 15.4%–30.1%) |
| F1 | 64.0% |
| Accuracy | 77.9% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 17 | 17 | 100% | 10 khóa do liên kết | 0 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | Lạm dụng (chưa biết) | 6 | 0 | 0% | — | 6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 9 | 9 | 100% | 5 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 8 | 0 | 0% | — | 7 |
| Bùng hàng COD | Lạm dụng | 15 | 15 | 100% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 6 | 100% | — | 0 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 41 | 6 | 15% | — | 17 |
| Farm voucher | Lạm dụng | 52 | 36 | 69% | — | 16 |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 40 | 1 | 2% | — | 39 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 31 | 11 | 35% | — | 20 |
| Khách quen | Hợp lệ | 40 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% | — | 0 |
| Khách mới đặt nhiều đơn COD liền nhau | Hard negative | 12 | 7 | 58% | — | 0 |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% | — | 59 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 38 | 3 | 8% | — | 16 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 15/15 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 1/5 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 5/5 |
| Farm voucher | 8/8 |
| Tài khoản mới treo nhiều đơn COD | 6/6 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | 0/6 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 8/8 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 4/4 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 36.3%; Risk Engine gắn cờ 24.9% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | 78.5% | 54.0% | 64.0% | 8.4% | 77.9% | 95 / 26 / 81 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 63.7% | 0 / 0 / 176 |
| B1 · Luật thủ công (2 luật cứng) | 65.4% | 39.8% | 49.5% | 12.0% | 70.5% | 70 / 37 / 106 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | 36.3% | 24.9% | 29.6% | 24.9% | 56.9% | 43.9 / 77.1 / 132.1 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 14/17, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 9/9, Người nhà dùng chung máy với tài khoản bị khóa 7/8, Bùng hàng COD 15/15, Farm voucher 32/52, Khách quen 30/40.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **81** lượt; khách hợp lệ dùng: 99 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 2, Tài khoản mới treo nhiều đơn COD CONFIRMED = 12, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 26, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 1, Khách mới đặt nhiều đơn COD liền nhau CONFIRMED = 24, Khách mới bình thường CONFIRMED = 79, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 17

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 1039 lượt): p50 19.08 ms · p95 40.55 ms · p99 65.58 ms
- Toàn bộ request `voucher_apply` (324 lượt, trong cùng tiến trình, không qua mạng): p50 50.88 ms · p95 98.91 ms · p99 166.51 ms
- Toàn bộ request `place_order` (519 lượt, trong cùng tiến trình, không qua mạng): p50 57.0 ms · p95 112.81 ms · p99 184.12 ms
- Toàn bộ request `payment_options` (283 lượt, trong cùng tiến trình, không qua mạng): p50 36.21 ms · p95 65.92 ms · p99 121.93 ms
- Thời gian chạy: 155.1 giây cho 2652 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
