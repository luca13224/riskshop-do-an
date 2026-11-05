# Kết quả mô phỏng: tập test_v3 (seed 8, scale 1)

> Tạo lúc 2026-11-05 12:40 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `f270cd66dfcbe367…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 84 | FN = 90 |
| **Hợp lệ (nhãn thật)** | FP = 23 | TN = 279 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 78.5% (84/107; KTC 95%: 69.8%–85.2%) |
| Recall (tất cả kiểu lạm dụng) | 48.3% (84/174; KTC 95%: 41.0%–55.7%) |
| Recall: kiểu đã biết | 62.2% (84/135; KTC 95%: 53.8%–70.0%) |
| Recall: biến thể chưa biết | 0.0% (0/39; KTC 95%: 0.0%–9.0%) |
| FPR (tất cả khách hợp lệ) | 7.6% (23/302; KTC 95%: 5.1%–11.2%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 20.5% (23/112; KTC 95%: 14.1%–28.9%) |
| F1 | 59.8% |
| Accuracy | 76.3% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 13 | 13 | 100% | 5 khóa do liên kết | 0 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | Lạm dụng (chưa biết) | 6 | 0 | 0% | — | 6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 12 | 12 | 100% | 8 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 8 | 0 | 0% | — | 7 |
| Bùng hàng COD | Lạm dụng | 15 | 6 | 40% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 0 | 0% | — | 0 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 41 | 4 | 10% | — | 24 |
| Farm voucher | Lạm dụng | 55 | 39 | 71% | — | 16 |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 33 | 0 | 0% | — | 33 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 34 | 14 | 41% | — | 20 |
| Khách quen | Hợp lệ | 40 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% | — | 0 |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% | — | 65 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 43 | 9 | 21% | — | 23 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 6/15 |
| Tài khoản mới treo nhiều đơn COD | 0/6 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 5/5 |
| Farm voucher | 8/8 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 0/5 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | 0/6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 4/4 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 8/8 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 36.5%; Risk Engine gắn cờ 22.5% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | 78.5% | 48.3% | 59.8% | 7.6% | 76.3% | 84 / 23 / 90 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 63.4% | 0 / 0 / 174 |
| B1 · Luật thủ công (2 luật cứng) | 66.7% | 42.5% | 51.9% | 12.2% | 71.2% | 74 / 37 / 100 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | 36.5% | 22.5% | 27.8% | 22.5% | 57.4% | 39.1 / 67.9 / 134.9 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 11/13, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 12/12, Người nhà dùng chung máy với tài khoản bị khóa 7/8, Bùng hàng COD 15/15, Farm voucher 36/55, Khách quen 30/40.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **75** lượt; khách hợp lệ dùng: 119 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 2, Bùng hàng COD CONFIRMED = 9, Tài khoản mới treo nhiều đơn COD CONFIRMED = 22, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 15, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 2, Khách mới bình thường CONFIRMED = 72, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 23

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 1005 lượt): p50 11.02 ms · p95 15.65 ms · p99 18.73 ms
- Toàn bộ request `payment_options` (239 lượt, trong cùng tiến trình, không qua mạng): p50 22.8 ms · p95 28.98 ms · p99 31.67 ms
- Toàn bộ request `place_order` (507 lượt, trong cùng tiến trình, không qua mạng): p50 34.53 ms · p95 45.21 ms · p99 52.61 ms
- Toàn bộ request `voucher_apply` (333 lượt, trong cùng tiến trình, không qua mạng): p50 30.84 ms · p95 37.71 ms · p99 40.7 ms
- Thời gian chạy: 85.1 giây cho 2581 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
