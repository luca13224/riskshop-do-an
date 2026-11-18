# Kết quả mô phỏng: tập test_v5 (seed 12, scale 1)

> Tạo lúc 2026-11-05 20:46 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `b61c2cc8746e80d9…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 96 | FN = 147 |
| **Hợp lệ (nhãn thật)** | FP = 32 | TN = 352 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 75.0% (96/128; KTC 95%: 66.8%–81.7%) |
| Recall (tất cả kiểu lạm dụng) | 39.5% (96/243; KTC 95%: 33.6%–45.8%) |
| Recall: kiểu đã biết | 56.7% (93/164; KTC 95%: 49.1%–64.0%) |
| Recall: biến thể chưa biết | 3.8% (3/79; KTC 95%: 1.3%–10.6%) |
| FPR (tất cả khách hợp lệ) | 8.3% (32/384; KTC 95%: 6.0%–11.5%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 16.5% (32/194; KTC 95%: 11.9%–22.4%) |
| F1 | 51.7% |
| Accuracy | 71.5% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 14 | 14 | 100% | 14 khóa do liên kết | 0 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | Lạm dụng (chưa biết) | 6 | 0 | 0% | — | 6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 10 | 10 | 100% | 10 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 8 | 0 | 0% | — | 7 |
| Đại gia đình dùng chung máy, giao về nhà bố mẹ | Hard negative | 42 | 1 | 2% | — | 18 |
| Bùng hàng COD | Lạm dụng | 15 | 15 | 100% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 6 | 100% | — | 0 |
| Ký túc xá chung địa chỉ, chung máy tính | Hard negative | 38 | 10 | 26% | — | 7 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 35 | 1 | 3% | — | 23 |
| Farm voucher | Lạm dụng | 50 | 34 | 68% | — | 16 |
| Farm nối chuỗi (thiết bị → SĐT → địa chỉ) | Lạm dụng | 41 | 6 | 15% | — | 35 |
| Farm nối chuỗi có mắt xích đứt | Lạm dụng (chưa biết) | 35 | 1 | 3% | — | 34 |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 38 | 2 | 5% | — | 36 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 28 | 8 | 29% | — | 20 |
| Khách quen | Hợp lệ | 40 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% | — | 0 |
| Khách mới đặt nhiều đơn COD liền nhau | Hard negative | 12 | 7 | 58% | — | 0 |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% | — | 69 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 39 | 3 | 8% | — | 18 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 15/15 |
| Tài khoản mới treo nhiều đơn COD | 6/6 |
| Farm voucher | 8/8 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 2/5 |
| Farm nối chuỗi có mắt xích đứt | 1/4 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 5/5 |
| Farm nối chuỗi (thiết bị → SĐT → địa chỉ) | 5/5 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 8/8 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | 0/6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 4/4 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 38.8%; Risk Engine gắn cờ 20.4% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | 75.0% | 39.5% | 51.7% | 8.3% | 71.5% | 96 / 32 / 147 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 61.2% | 0 / 0 / 243 |
| B1 · Luật thủ công (2 luật cứng) | 58.7% | 34.6% | 43.5% | 15.4% | 65.2% | 84 / 59 / 159 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | 38.8% | 20.4% | 26.7% | 20.4% | 56.6% | 49.6 / 78.4 / 193.4 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 10/14, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 10/10, Người nhà dùng chung máy với tài khoản bị khóa 7/8, Đại gia đình dùng chung máy, giao về nhà bố mẹ 9/42, Bùng hàng COD 15/15, Ký túc xá chung địa chỉ, chung máy tính 12/38, Farm voucher 27/50, Farm nối chuỗi (thiết bị → SĐT → địa chỉ) 13/41, Farm nối chuỗi có mắt xích đứt 9/35, Khách quen 31/40.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **147** lượt; khách hợp lệ dùng: 142 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 4, Đại gia đình dùng chung máy, giao về nhà bố mẹ CONFIRMED = 23, Tài khoản mới treo nhiều đơn COD CONFIRMED = 12, Ký túc xá chung địa chỉ, chung máy tính CONFIRMED = 19, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 18, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 1, Khách mới đặt nhiều đơn COD liền nhau CONFIRMED = 24, Khách mới bình thường CONFIRMED = 75, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 20

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 1344 lượt): p50 21.75 ms · p95 51.02 ms · p99 86.09 ms
- Toàn bộ request `voucher_apply` (442 lượt, trong cùng tiến trình, không qua mạng): p50 55.38 ms · p95 117.42 ms · p99 195.95 ms
- Toàn bộ request `place_order` (671 lượt, trong cùng tiến trình, không qua mạng): p50 62.9 ms · p95 134.36 ms · p99 229.61 ms
- Toàn bộ request `payment_options` (320 lượt, trong cùng tiến trình, không qua mạng): p50 37.34 ms · p95 79.01 ms · p99 134.59 ms
- Thời gian chạy: 204.8 giây cho 3354 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
