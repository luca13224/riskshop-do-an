# Kết quả mô phỏng: tập test_v2 (seed 3, scale 1)

> Tạo lúc 2026-10-31 10:17 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `1d9f87d5a9d57e9a…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 67 | FN = 84 |
| **Hợp lệ (nhãn thật)** | FP = 24 | TN = 276 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 73.6% (67/91; KTC 95%: 63.7%–81.6%) |
| Recall (tất cả kiểu lạm dụng) | 44.4% (67/151; KTC 95%: 36.7%–52.3%) |
| Recall: kiểu đã biết | 60.4% (67/111; KTC 95%: 51.1%–69.0%) |
| Recall: biến thể chưa biết | 0.0% (0/40; KTC 95%: 0.0%–8.8%) |
| FPR (tất cả khách hợp lệ) | 8.0% (24/300; KTC 95%: 5.4%–11.6%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 21.8% (24/110; KTC 95%: 15.1%–30.4%) |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ |
|---|---|---|---|---|
| Bùng hàng COD | Lạm dụng | 15 | 13 | 87% |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 0 | 0% |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 49 | 8 | 16% |
| Farm voucher | Lạm dụng | 58 | 42 | 72% |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 40 | 0 | 0% |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 32 | 12 | 38% |
| Khách quen | Hợp lệ | 40 | 0 | 0% |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 41 | 6 | 15% |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 13/15 |
| Farm voucher | 8/8 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 5/5 |
| Tài khoản mới treo nhiều đơn COD | 0/6 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 0/5 |

## Tác động nghiệp vụ trong lần chạy
- Voucher tân thủ bị kẻ lạm dụng dùng thành công: **76** lượt; khách hợp lệ dùng: 125 lượt.
- Đơn COD theo persona và trạng thái: Bùng hàng COD CONFIRMED = 2, Tài khoản mới treo nhiều đơn COD CONFIRMED = 20, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 28, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 2, Khách mới bình thường CONFIRMED = 75, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 24

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 999 lượt): p50 8.44 ms · p95 11.33 ms · p99 13.61 ms
- Toàn bộ request `payment_options` (252 lượt, trong cùng tiến trình, không qua mạng): p50 24.51 ms · p95 29.95 ms · p99 33.87 ms
- Toàn bộ request `place_order` (478 lượt, trong cùng tiến trình, không qua mạng): p50 36.51 ms · p95 44.54 ms · p99 53.97 ms
- Toàn bộ request `voucher_apply` (311 lượt, trong cùng tiến trình, không qua mạng): p50 33.58 ms · p95 41.53 ms · p99 47.87 ms
- Thời gian chạy: 96.7 giây cho 2346 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
