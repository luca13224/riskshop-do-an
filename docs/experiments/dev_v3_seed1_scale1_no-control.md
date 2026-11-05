# Kết quả mô phỏng: tập dev_v3 (seed 1, scale 1)

> Tạo lúc 2026-11-05 12:37 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `22cacc7292a5bd96…` · **B0 không kiểm soát**: tắt mọi luật, lớp điểm tin cậy và khóa kẻ né lệnh khóa
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 0 | FN = 83 |
| **Hợp lệ (nhãn thật)** | FP = 0 | TN = 200 |

| Chỉ số | Giá trị |
|---|---|
| Precision | — |
| Recall (tất cả kiểu lạm dụng) | 0.0% (0/83; KTC 95%: 0.0%–4.4%) |
| Recall: kiểu đã biết | 0.0% (0/83; KTC 95%: 0.0%–4.4%) |
| Recall: biến thể chưa biết | — |
| FPR (tất cả khách hợp lệ) | 0.0% (0/200; KTC 95%: 0.0%–1.9%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/130; KTC 95%: 0.0%–2.9%) |
| FPR: hard negative | 0.0% (0/70; KTC 95%: 0.0%–5.2%) |
| F1 | 0.0% |
| Accuracy | 70.7% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 8 | 0 | 0% | — | 8 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 7 | 0 | 0% | — | 7 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 5 | 0 | 0% | — | 3 |
| Bùng hàng COD | Lạm dụng | 12 | 0 | 0% | — | 0 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 22 | 0 | 0% | — | 15 |
| Farm voucher | Lạm dụng | 33 | 0 | 0% | — | 33 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 23 | 0 | 0% | — | 23 |
| Khách quen | Hợp lệ | 30 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 8 | 0 | 0% | — | 0 |
| Khách mới bình thường | Hợp lệ | 100 | 0 | 0% | — | 45 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 8 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 27 | 0 | 0% | — | 17 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 0/12 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 0/4 |
| Farm voucher | 0/6 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 0/5 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 0/3 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 29.3%; Risk Engine gắn cờ 0.0% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | — | 0.0% | 0.0% | 0.0% | 70.7% | 0 / 0 / 83 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 70.7% | 0 / 0 / 83 |
| B1 · Luật thủ công (2 luật cứng) | 67.5% | 62.6% | 65.0% | 12.5% | 80.2% | 52 / 25 / 31 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | — | 0.0% | 0.0% | 0.0% | 70.7% | 0 / 0 / 83 |

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **71** lượt; khách hợp lệ dùng: 80 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 2, Bùng hàng COD CONFIRMED = 12, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 10, Khách quen CONFIRMED = 30, Khách mới mua hàng giá trị cao (COD) CONFIRMED = 8, Khách mới bình thường CONFIRMED = 38, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 24, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 14

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 588 lượt): p50 9.61 ms · p95 12.93 ms · p99 16.69 ms
- Toàn bộ request `payment_options` (138 lượt, trong cùng tiến trình, không qua mạng): p50 21.13 ms · p95 27.98 ms · p99 36.97 ms
- Toàn bộ request `place_order` (312 lượt, trong cùng tiến trình, không qua mạng): p50 32.45 ms · p95 40.09 ms · p99 47.0 ms
- Toàn bộ request `voucher_apply` (180 lượt, trong cùng tiến trình, không qua mạng): p50 28.74 ms · p95 35.23 ms · p99 39.41 ms
- Thời gian chạy: 48.4 giây cho 1495 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
