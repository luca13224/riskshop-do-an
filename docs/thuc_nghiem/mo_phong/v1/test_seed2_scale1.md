# Kết quả mô phỏng: tập test (seed 2, scale 1)

> Tạo lúc 2026-10-30 14:41 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `3df073b71c7a9362…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 59 | FN = 43 |
| **Hợp lệ (nhãn thật)** | FP = 20 | TN = 234 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 74.7% (59/79; KTC 95%: 64.1%–83.0%) |
| Recall (tất cả kiểu lạm dụng) | 57.8% (59/102; KTC 95%: 48.1%–67.0%) |
| Recall: kiểu đã biết | 85.5% (59/69; KTC 95%: 75.3%–91.9%) |
| Recall: biến thể chưa biết | 0.0% (0/33; KTC 95%: 0.0%–10.4%) |
| FPR (tất cả khách hợp lệ) | 7.9% (20/254; KTC 95%: 5.1%–11.8%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 31.2% (20/64; KTC 95%: 21.2%–43.4%) |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ |
|---|---|---|---|---|
| Bùng hàng COD | Lạm dụng | 15 | 7 | 47% |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng (chưa biết) | 6 | 0 | 0% |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 44 | 10 | 23% |
| Farm voucher | Lạm dụng | 54 | 52 | 96% |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng (chưa biết) | 27 | 0 | 0% |
| Khách quen | Hợp lệ | 40 | 0 | 0% |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 7/15 |
| Tài khoản mới treo nhiều đơn COD | 0/6 |
| Farm voucher | 8/8 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 0/4 |

## Tác động nghiệp vụ trong lần chạy
- Voucher tân thủ bị kẻ lạm dụng dùng thành công: **29** lượt; khách hợp lệ dùng: 126 lượt.
- Đơn COD theo persona và trạng thái: Bùng hàng COD CONFIRMED = 8, Tài khoản mới treo nhiều đơn COD CONFIRMED = 23, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 19, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 3, Khách mới bình thường CONFIRMED = 68, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 831 lượt): p50 7.46 ms · p95 11.5 ms · p99 14.0 ms
- Toàn bộ request `payment_options` (215 lượt, trong cùng tiến trình, không qua mạng): p50 23.61 ms · p95 30.97 ms · p99 35.3 ms
- Toàn bộ request `place_order` (399 lượt, trong cùng tiến trình, không qua mạng): p50 35.25 ms · p95 46.59 ms · p99 54.7 ms
- Toàn bộ request `voucher_apply` (217 lượt, trong cùng tiến trình, không qua mạng): p50 33.31 ms · p95 46.28 ms · p99 52.0 ms
- Thời gian chạy: 80.2 giây cho 1898 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
