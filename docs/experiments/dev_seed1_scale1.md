# Kết quả mô phỏng: tập dev (seed 1, scale 1)

> Tạo lúc 2026-10-30 14:36 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `3df073b71c7a9362…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 35 | FN = 6 |
| **Hợp lệ (nhãn thật)** | FP = 8 | TN = 163 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 81.4% (35/43; KTC 95%: 67.4%–90.3%) |
| Recall (tất cả kiểu lạm dụng) | 85.4% (35/41; KTC 95%: 71.6%–93.1%) |
| Recall: kiểu đã biết | 85.4% (35/41; KTC 95%: 71.6%–93.1%) |
| Recall: biến thể chưa biết | — |
| FPR (tất cả khách hợp lệ) | 4.7% (8/171; KTC 95%: 2.4%–9.0%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/130; KTC 95%: 0.0%–2.9%) |
| FPR: hard negative | 19.5% (8/41; KTC 95%: 10.2%–34.0%) |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ |
|---|---|---|---|---|
| Bùng hàng COD | Lạm dụng | 12 | 8 | 67% |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 25 | 0 | 0% |
| Farm voucher | Lạm dụng | 29 | 27 | 93% |
| Khách quen | Hợp lệ | 30 | 0 | 0% |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 8 | 8 | 100% |
| Khách mới bình thường | Hợp lệ | 100 | 0 | 0% |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 8 | 0 | 0% |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 8/12 |
| Farm voucher | 6/6 |

## Tác động nghiệp vụ trong lần chạy
- Voucher tân thủ bị kẻ lạm dụng dùng thành công: **2** lượt; khách hợp lệ dùng: 80 lượt.
- Đơn COD theo persona và trạng thái: Bùng hàng COD CONFIRMED = 4, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 8, Khách quen CONFIRMED = 30, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 3, Khách mới bình thường CONFIRMED = 38, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 24

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 436 lượt): p50 6.0 ms · p95 7.78 ms · p99 11.11 ms
- Toàn bộ request `voucher_apply` (109 lượt, trong cùng tiến trình, không qua mạng): p50 26.29 ms · p95 31.33 ms · p99 33.44 ms
- Toàn bộ request `place_order` (207 lượt, trong cùng tiến trình, không qua mạng): p50 27.69 ms · p95 35.61 ms · p99 45.12 ms
- Toàn bộ request `payment_options` (120 lượt, trong cùng tiến trình, không qua mạng): p50 18.73 ms · p95 21.64 ms · p99 27.64 ms
- Thời gian chạy: 32.0 giây cho 1094 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
