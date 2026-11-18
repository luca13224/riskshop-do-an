# Kết quả mô phỏng: tập test_v3 (seed 6, scale 1)

> Tạo lúc 2026-11-03 11:41 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `2fa09e9c88da841a…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 84 | FN = 86 |
| **Hợp lệ (nhãn thật)** | FP = 23 | TN = 265 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 78.5% (84/107; KTC 95%: 69.8%–85.2%) |
| Recall (tất cả kiểu lạm dụng) | 49.4% (84/170; KTC 95%: 42.0%–56.9%) |
| Recall: kiểu đã biết | 60.2% (77/128; KTC 95%: 51.5%–68.2%) |
| Recall: biến thể chưa biết | 16.7% (7/42; KTC 95%: 8.3%–30.6%) |
| FPR (tất cả khách hợp lệ) | 8.0% (23/288; KTC 95%: 5.4%–11.7%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 23.5% (23/98; KTC 95%: 16.2%–32.8%) |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 15 | 15 | 100% | 7 khóa do liên kết | 0 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | Lạm dụng (chưa biết) | 6 | 6 | 100% | — | 0 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 12 | 12 | 100% | 8 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 8 | 7 | 88% | — | 0 |
| Bùng hàng COD | Lạm dụng | 15 | 6 | 40% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 0 | 0% | — | 0 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 36 | 3 | 8% | — | 19 |
| Farm voucher | Lạm dụng | 52 | 36 | 69% | — | 16 |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 36 | 1 | 3% | — | 35 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 28 | 8 | 29% | — | 20 |
| Khách quen | Hợp lệ | 40 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% | — | 0 |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% | — | 78 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 34 | 3 | 9% | — | 21 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 6/15 |
| Farm voucher | 8/8 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 1/5 |
| Tài khoản mới treo nhiều đơn COD | 0/6 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 5/5 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 8/8 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | 6/6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 4/4 |

## Tác động nghiệp vụ trong lần chạy
- Voucher tân thủ bị kẻ lạm dụng dùng thành công: **71** lượt; khách hợp lệ dùng: 118 lượt.
- Đơn COD theo persona và trạng thái: Bùng hàng COD CONFIRMED = 9, Tài khoản mới treo nhiều đơn COD CONFIRMED = 20, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 14, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 1, Khách mới bình thường CONFIRMED = 70, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 11

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 955 lượt): p50 10.91 ms · p95 14.76 ms · p99 19.55 ms
- Toàn bộ request `voucher_apply` (322 lượt, trong cùng tiến trình, không qua mạng): p50 29.71 ms · p95 36.92 ms · p99 40.56 ms
- Toàn bộ request `place_order` (479 lượt, trong cùng tiến trình, không qua mạng): p50 32.98 ms · p95 44.09 ms · p99 50.79 ms
- Toàn bộ request `payment_options` (223 lượt, trong cùng tiến trình, không qua mạng): p50 22.19 ms · p95 27.35 ms · p99 29.15 ms
- Thời gian chạy: 81.9 giây cho 2485 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
