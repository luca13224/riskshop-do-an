# Kết quả mô phỏng: tập test_v3 (seed 7, scale 1)

> Tạo lúc 2026-11-03 12:10 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `f270cd66dfcbe367…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 90 | FN = 92 |
| **Hợp lệ (nhãn thật)** | FP = 17 | TN = 276 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 84.1% (90/107; KTC 95%: 76.0%–89.8%) |
| Recall (tất cả kiểu lạm dụng) | 49.5% (90/182; KTC 95%: 42.3%–56.6%) |
| Recall: kiểu đã biết | 65.2% (90/138; KTC 95%: 57.0%–72.7%) |
| Recall: biến thể chưa biết | 0.0% (0/44; KTC 95%: 0.0%–8.0%) |
| FPR (tất cả khách hợp lệ) | 5.8% (17/293; KTC 95%: 3.6%–9.1%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 16.5% (17/103; KTC 95%: 10.6%–24.9%) |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 15 | 15 | 100% | 10 khóa do liên kết | 0 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | Lạm dụng (chưa biết) | 6 | 0 | 0% | — | 6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 15 | 15 | 100% | 11 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 8 | 0 | 0% | — | 6 |
| Bùng hàng COD | Lạm dụng | 15 | 9 | 60% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 0 | 0% | — | 0 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 38 | 4 | 11% | — | 23 |
| Farm voucher | Lạm dụng | 55 | 39 | 71% | — | 16 |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 38 | 0 | 0% | — | 38 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 32 | 12 | 38% | — | 20 |
| Khách quen | Hợp lệ | 40 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% | — | 0 |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% | — | 74 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 37 | 3 | 8% | — | 22 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 9/15 |
| Farm voucher | 8/8 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 5/5 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 0/5 |
| Tài khoản mới treo nhiều đơn COD | 0/6 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 8/8 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | 0/6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 4/4 |

## Tác động nghiệp vụ trong lần chạy
- Voucher tân thủ bị kẻ lạm dụng dùng thành công: **80** lượt; khách hợp lệ dùng: 125 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 5, Bùng hàng COD CONFIRMED = 6, Tài khoản mới treo nhiều đơn COD CONFIRMED = 20, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 20, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 5, Khách mới bình thường CONFIRMED = 76, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 21

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 1010 lượt): p50 10.51 ms · p95 14.49 ms · p99 18.11 ms
- Toàn bộ request `voucher_apply` (339 lượt, trong cùng tiến trình, không qua mạng): p50 29.64 ms · p95 39.31 ms · p99 45.25 ms
- Toàn bộ request `payment_options` (247 lượt, trong cùng tiến trình, không qua mạng): p50 21.45 ms · p95 27.52 ms · p99 30.28 ms
- Toàn bộ request `place_order` (496 lượt, trong cùng tiến trình, không qua mạng): p50 33.29 ms · p95 44.52 ms · p99 52.5 ms
- Thời gian chạy: 82.7 giây cho 2580 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
