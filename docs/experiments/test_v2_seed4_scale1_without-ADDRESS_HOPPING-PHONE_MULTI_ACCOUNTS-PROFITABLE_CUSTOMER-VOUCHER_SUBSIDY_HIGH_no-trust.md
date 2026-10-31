# Kết quả mô phỏng: tập test_v2 (seed 4, scale 1)

> Tạo lúc 2026-10-31 12:28 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `6349e1ac0798f3e1…` · Luật bị tắt: PHONE_MULTI_ACCOUNTS, ADDRESS_HOPPING, VOUCHER_SUBSIDY_HIGH, PROFITABLE_CUSTOMER · Tắt lớp điểm tin cậy
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 47 | FN = 89 |
| **Hợp lệ (nhãn thật)** | FP = 18 | TN = 271 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 72.3% (47/65; KTC 95%: 60.4%–81.7%) |
| Recall (tất cả kiểu lạm dụng) | 34.6% (47/136; KTC 95%: 27.1%–42.9%) |
| Recall: kiểu đã biết | 50.0% (47/94; KTC 95%: 40.1%–59.9%) |
| Recall: biến thể chưa biết | 0.0% (0/42; KTC 95%: 0.0%–8.4%) |
| FPR (tất cả khách hợp lệ) | 6.2% (18/289; KTC 95%: 4.0%–9.6%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 18.2% (18/99; KTC 95%: 11.8%–26.9%) |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ |
|---|---|---|---|---|
| Bùng hàng COD | Lạm dụng | 15 | 10 | 67% |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 0 | 0% |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 41 | 3 | 7% |
| Farm voucher | Lạm dụng | 44 | 28 | 64% |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 42 | 0 | 0% |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 29 | 9 | 31% |
| Khách quen | Hợp lệ | 40 | 0 | 0% |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 38 | 5 | 13% |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 10/15 |
| Tài khoản mới treo nhiều đơn COD | 0/6 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 0/5 |
| Farm voucher | 8/8 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 5/5 |

## Tác động nghiệp vụ trong lần chạy
- Voucher tân thủ bị kẻ lạm dụng dùng thành công: **78** lượt; khách hợp lệ dùng: 116 lượt.
- Đơn COD theo persona và trạng thái: Bùng hàng COD CONFIRMED = 5, Tài khoản mới treo nhiều đơn COD CONFIRMED = 20, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 21, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 7, Khách mới bình thường CONFIRMED = 75, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 16

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 937 lượt): p50 9.32 ms · p95 13.05 ms · p99 16.68 ms
- Toàn bộ request `payment_options` (237 lượt, trong cùng tiến trình, không qua mạng): p50 22.16 ms · p95 29.41 ms · p99 32.46 ms
- Toàn bộ request `place_order` (461 lượt, trong cùng tiến trình, không qua mạng): p50 32.66 ms · p95 41.24 ms · p99 48.82 ms
- Toàn bộ request `voucher_apply` (283 lượt, trong cùng tiến trình, không qua mạng): p50 29.98 ms · p95 37.41 ms · p99 44.03 ms
- Thời gian chạy: 75.0 giây cho 2237 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
