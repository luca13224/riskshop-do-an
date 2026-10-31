# Kết quả mô phỏng: tập dev_v2 (seed 1, scale 1)

> Tạo lúc 2026-10-31 10:15 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `86d43d9a06f10b0d…` · Luật bị tắt: ADDR_VOUCHER_RING
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 28 | FN = 40 |
| **Hợp lệ (nhãn thật)** | FP = 8 | TN = 187 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 77.8% (28/36; KTC 95%: 61.9%–88.3%) |
| Recall (tất cả kiểu lạm dụng) | 41.2% (28/68; KTC 95%: 30.3%–53.0%) |
| Recall: kiểu đã biết | 41.2% (28/68; KTC 95%: 30.3%–53.0%) |
| Recall: biến thể chưa biết | — |
| FPR (tất cả khách hợp lệ) | 4.1% (8/195; KTC 95%: 2.1%–7.9%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/130; KTC 95%: 0.0%–2.9%) |
| FPR: hard negative | 12.3% (8/65; KTC 95%: 6.4%–22.4%) |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ |
|---|---|---|---|---|
| Bùng hàng COD | Lạm dụng | 12 | 7 | 58% |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 22 | 0 | 0% |
| Farm voucher | Lạm dụng | 33 | 21 | 64% |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 23 | 0 | 0% |
| Khách quen | Hợp lệ | 30 | 0 | 0% |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 8 | 8 | 100% |
| Khách mới bình thường | Hợp lệ | 100 | 0 | 0% |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 8 | 0 | 0% |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 27 | 0 | 0% |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 7/12 |
| Farm voucher | 6/6 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 0/4 |

## Tác động nghiệp vụ trong lần chạy
- Voucher tân thủ bị kẻ lạm dụng dùng thành công: **35** lượt; khách hợp lệ dùng: 74 lượt.
- Đơn COD theo persona và trạng thái: Bùng hàng COD CONFIRMED = 5, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 13, Khách quen CONFIRMED = 30, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 4, Khách mới bình thường CONFIRMED = 38, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 24, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 15

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 525 lượt): p50 8.34 ms · p95 11.1 ms · p99 13.05 ms
- Toàn bộ request `voucher_apply` (160 lượt, trong cùng tiến trình, không qua mạng): p50 33.18 ms · p95 40.29 ms · p99 49.0 ms
- Toàn bộ request `place_order` (255 lượt, trong cùng tiến trình, không qua mạng): p50 36.41 ms · p95 45.61 ms · p99 52.9 ms
- Toàn bộ request `payment_options` (140 lượt, trong cùng tiến trình, không qua mạng): p50 24.41 ms · p95 28.44 ms · p99 33.46 ms
- Thời gian chạy: 51.2 giây cho 1345 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
