# Kết quả mô phỏng: tập test_v3 (seed 8, scale 1)

> Tạo lúc 2026-11-05 12:42 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `22cacc7292a5bd96…` · **B0 không kiểm soát**: tắt mọi luật, lớp điểm tin cậy và khóa kẻ né lệnh khóa
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 0 | FN = 174 |
| **Hợp lệ (nhãn thật)** | FP = 0 | TN = 302 |

| Chỉ số | Giá trị |
|---|---|
| Precision | — |
| Recall (tất cả kiểu lạm dụng) | 0.0% (0/174; KTC 95%: 0.0%–2.2%) |
| Recall: kiểu đã biết | 0.0% (0/135; KTC 95%: 0.0%–2.8%) |
| Recall: biến thể chưa biết | 0.0% (0/39; KTC 95%: 0.0%–9.0%) |
| FPR (tất cả khách hợp lệ) | 0.0% (0/302; KTC 95%: 0.0%–1.3%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 0.0% (0/112; KTC 95%: 0.0%–3.3%) |
| F1 | 0.0% |
| Accuracy | 63.4% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 13 | 0 | 0% | — | 13 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | Lạm dụng (chưa biết) | 6 | 0 | 0% | — | 6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 12 | 0 | 0% | — | 12 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 8 | 0 | 0% | — | 7 |
| Bùng hàng COD | Lạm dụng | 15 | 0 | 0% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 0 | 0% | — | 0 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 41 | 0 | 0% | — | 28 |
| Farm voucher | Lạm dụng | 55 | 0 | 0% | — | 55 |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 33 | 0 | 0% | — | 33 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 34 | 0 | 0% | — | 34 |
| Khách quen | Hợp lệ | 40 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 0 | 0% | — | 0 |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% | — | 65 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 43 | 0 | 0% | — | 32 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 0/15 |
| Tài khoản mới treo nhiều đơn COD | 0/6 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 0/5 |
| Farm voucher | 0/8 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 0/5 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | 0/6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 0/4 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 0/8 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 36.5%; Risk Engine gắn cờ 0.0% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | — | 0.0% | 0.0% | 0.0% | 63.4% | 0 / 0 / 174 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 63.4% | 0 / 0 / 174 |
| B1 · Luật thủ công (2 luật cứng) | 66.7% | 42.5% | 51.9% | 12.2% | 71.2% | 74 / 37 / 100 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | — | 0.0% | 0.0% | 0.0% | 63.4% | 0 / 0 / 174 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 11/13, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 12/12, Người nhà dùng chung máy với tài khoản bị khóa 7/8, Bùng hàng COD 15/15, Farm voucher 36/55, Khách quen 30/40.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **153** lượt; khách hợp lệ dùng: 132 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 2, Bùng hàng COD CONFIRMED = 15, Tài khoản mới treo nhiều đơn COD CONFIRMED = 22, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 15, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) CONFIRMED = 10, Khách mới bình thường CONFIRMED = 72, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 23

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 1046 lượt): p50 9.17 ms · p95 13.15 ms · p99 16.97 ms
- Toàn bộ request `payment_options` (239 lượt, trong cùng tiến trình, không qua mạng): p50 19.83 ms · p95 26.91 ms · p99 31.73 ms
- Toàn bộ request `place_order` (548 lượt, trong cùng tiến trình, không qua mạng): p50 31.45 ms · p95 41.13 ms · p99 44.64 ms
- Toàn bộ request `voucher_apply` (333 lượt, trong cùng tiến trình, không qua mạng): p50 28.05 ms · p95 34.23 ms · p99 40.22 ms
- Thời gian chạy: 81.8 giây cho 2581 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
