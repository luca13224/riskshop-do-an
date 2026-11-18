# Kết quả mô phỏng: tập test_v2 (seed 5, scale 1)

> Tạo lúc 2026-11-03 11:23 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `2fa09e9c88da841a…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 56 | FN = 90 |
| **Hợp lệ (nhãn thật)** | FP = 18 | TN = 274 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 75.7% (56/74; KTC 95%: 64.8%–84.0%) |
| Recall (tất cả kiểu lạm dụng) | 38.4% (56/146; KTC 95%: 30.9%–46.5%) |
| Recall: kiểu đã biết | 53.8% (56/104; KTC 95%: 44.3%–63.1%) |
| Recall: biến thể chưa biết | 0.0% (0/42; KTC 95%: 0.0%–8.4%) |
| FPR (tất cả khách hợp lệ) | 6.2% (18/292; KTC 95%: 3.9%–9.5%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 17.6% (18/102; KTC 95%: 11.5%–26.2%) |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ |
|---|---|---|---|---|
| Bùng hàng COD | Lạm dụng | 15 | 9 | 60% |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 0 | 0% |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 46 | 6 | 13% |
| Farm voucher | Lạm dụng | 47 | 31 | 66% |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 42 | 0 | 0% |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 36 | 16 | 44% |
| Khách quen | Hợp lệ | 40 | 0 | 0% |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 36 | 2 | 6% |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 9/15 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 0/5 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 5/5 |
| Farm voucher | 8/8 |
| Tài khoản mới treo nhiều đơn COD | 0/6 |

## Tác động nghiệp vụ trong lần chạy
- Voucher tân thủ bị kẻ lạm dụng dùng thành công: **78** lượt; khách hợp lệ dùng: 118 lượt.
- Đơn COD theo persona và trạng thái: Bùng hàng COD CONFIRMED = 6, Tài khoản mới treo nhiều đơn COD CONFIRMED = 22, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 28, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 3, Khách mới bình thường CONFIRMED = 81, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 14

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 974 lượt): p50 12.97 ms · p95 26.46 ms · p99 38.99 ms
- Toàn bộ request `voucher_apply` (294 lượt, trong cùng tiến trình, không qua mạng): p50 34.39 ms · p95 70.93 ms · p99 99.94 ms
- Toàn bộ request `payment_options` (250 lượt, trong cùng tiến trình, không qua mạng): p50 24.86 ms · p95 52.75 ms · p99 71.21 ms
- Toàn bộ request `place_order` (473 lượt, trong cùng tiến trình, không qua mạng): p50 38.84 ms · p95 76.77 ms · p99 105.54 ms
- Thời gian chạy: 95.6 giây cho 2290 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
