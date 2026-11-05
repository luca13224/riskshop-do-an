# Kết quả mô phỏng: tập test_v5 (seed 11, scale 1)

> Tạo lúc 2026-11-05 20:39 UTC · Lần chạy #1 · Dấu vân tay bộ luật: `b61c2cc8746e80d9…`
> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`), không chứng minh hiệu quả trên sàn thật.

## Chỉ số chính (đơn vị: tài khoản)
Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).

| | Bị gắn cờ | Không bị gắn cờ |
|---|---|---|
| **Lạm dụng (nhãn thật)** | TP = 102 | FN = 134 |
| **Hợp lệ (nhãn thật)** | FP = 43 | TN = 346 |

| Chỉ số | Giá trị |
|---|---|
| Precision | 70.3% (102/145; KTC 95%: 62.5%–77.2%) |
| Recall (tất cả kiểu lạm dụng) | 43.2% (102/236; KTC 95%: 37.1%–49.6%) |
| Recall: kiểu đã biết | 60.8% (101/166; KTC 95%: 53.2%–67.9%) |
| Recall: biến thể chưa biết | 1.4% (1/70; KTC 95%: 0.2%–7.7%) |
| FPR (tất cả khách hợp lệ) | 11.1% (43/389; KTC 95%: 8.3%–14.6%) |
| FPR: khách hợp lệ thông thường | 0.0% (0/190; KTC 95%: 0.0%–2.0%) |
| FPR: hard negative | 21.6% (43/199; KTC 95%: 16.5%–27.8%) |
| F1 | 53.5% |
| Accuracy | 71.7% |

## Theo persona
| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |
|---|---|---|---|---|---|---|
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | Lạm dụng | 18 | 18 | 100% | 18 khóa do liên kết | 0 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | Lạm dụng (chưa biết) | 6 | 0 | 0% | — | 6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | Lạm dụng | 14 | 14 | 100% | 14 khóa do liên kết | 0 |
| Người nhà dùng chung máy với tài khoản bị khóa | Hard negative | 8 | 0 | 0% | — | 6 |
| Đại gia đình dùng chung máy, giao về nhà bố mẹ | Hard negative | 41 | 4 | 10% | — | 16 |
| Bùng hàng COD | Lạm dụng | 15 | 15 | 100% | — | 0 |
| Tài khoản mới treo nhiều đơn COD | Lạm dụng | 6 | 6 | 100% | — | 0 |
| Ký túc xá chung địa chỉ, chung máy tính | Hard negative | 37 | 11 | 30% | — | 10 |
| Gia đình chung Wi-Fi/địa chỉ | Hard negative | 46 | 7 | 15% | — | 26 |
| Farm voucher | Lạm dụng | 51 | 35 | 69% | — | 16 |
| Farm nối chuỗi (thiết bị → SĐT → địa chỉ) | Lạm dụng | 34 | 5 | 15% | — | 29 |
| Farm nối chuỗi có mắt xích đứt | Lạm dụng (chưa biết) | 29 | 1 | 3% | — | 28 |
| Farm phân tán gom hàng về 2–3 điểm nhận | Lạm dụng (chưa biết) | 35 | 0 | 0% | — | 35 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | Lạm dụng | 28 | 8 | 29% | — | 20 |
| Khách quen | Hợp lệ | 40 | 0 | 0% | — | 0 |
| Khách mới mua hàng giá trị cao (COD) | Hard negative | 10 | 10 | 100% | — | 0 |
| Khách mới đặt nhiều đơn COD liền nhau | Hard negative | 12 | 9 | 75% | — | 0 |
| Khách mới bình thường | Hợp lệ | 150 | 0 | 0% | — | 71 |
| Khách quen đặt nhiều đơn liên tiếp | Hard negative | 10 | 0 | 0% | — | 0 |
| Nhóm ở trọ chung nhà, mỗi người 4G riêng | Hard negative | 35 | 2 | 6% | — | 22 |

## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)
| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |
|---|---|
| Bùng hàng COD | 15/15 |
| Tài khoản mới treo nhiều đơn COD | 6/6 |
| Farm voucher | 8/8 |
| Farm nối chuỗi có mắt xích đứt | 1/4 |
| Farm phân tán (mỗi tài khoản một máy, đổi IP) | 5/5 |
| Farm nối chuỗi (thiết bị → SĐT → địa chỉ) | 5/5 |
| Farm phân tán gom hàng về 2–3 điểm nhận | 0/5 |
| Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa | 8/8 |
| Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ | 0/6 |
| Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới | 4/4 |

## So với baseline (cùng tài khoản, cùng nhãn)
Tỷ lệ kẻ lạm dụng trong dân số: 37.8%; Risk Engine gắn cờ 23.2% tài khoản. B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).

| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |
|---|---|---|---|---|---|---|
| Risk Engine (lần chạy này) | 70.3% | 43.2% | 53.5% | 11.1% | 71.7% | 102 / 43 / 134 |
| B0 · Không kiểm soát | — | 0.0% | 0.0% | 0.0% | 62.2% | 0 / 0 / 236 |
| B1 · Luật thủ công (2 luật cứng) | 59.5% | 37.3% | 45.8% | 15.4% | 66.7% | 88 / 60 / 148 |
| B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng) | 37.8% | 23.2% | 28.7% | 23.2% | 56.6% | 54.8 / 90.2 / 181.2 |

B1 gắn cờ theo persona: Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa 15/18, Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới 14/14, Người nhà dùng chung máy với tài khoản bị khóa 6/8, Đại gia đình dùng chung máy, giao về nhà bố mẹ 9/41, Bùng hàng COD 15/15, Ký túc xá chung địa chỉ, chung máy tính 14/37, Farm voucher 26/51, Farm nối chuỗi (thiết bị → SĐT → địa chỉ) 10/34, Farm nối chuỗi có mắt xích đứt 8/29, Khách quen 31/40.

## Tác động nghiệp vụ trong lần chạy
- Mã người mới bị kẻ lạm dụng dùng thành công: **134** lượt; khách hợp lệ dùng: 151 lượt.
- Đơn COD theo persona và trạng thái: Người nhà dùng chung máy với tài khoản bị khóa CONFIRMED = 3, Đại gia đình dùng chung máy, giao về nhà bố mẹ CONFIRMED = 15, Tài khoản mới treo nhiều đơn COD CONFIRMED = 12, Ký túc xá chung địa chỉ, chung máy tính CONFIRMED = 19, Gia đình chung Wi-Fi/địa chỉ CONFIRMED = 23, Khách quen CONFIRMED = 40, Khách mới mua hàng giá trị cao (COD) PENDING_REVIEW = 3, Khách mới đặt nhiều đơn COD liền nhau CONFIRMED = 24, Khách mới bình thường CONFIRMED = 65, Khách quen đặt nhiều đơn liên tiếp CONFIRMED = 40, Nhóm ở trọ chung nhà, mỗi người 4G riêng CONFIRMED = 14

## Độ trễ
- Thời gian chấm điểm rủi ro (đo ở server, 1339 lượt): p50 21.88 ms · p95 48.69 ms · p99 84.02 ms
- Toàn bộ request `voucher_apply` (443 lượt, trong cùng tiến trình, không qua mạng): p50 55.63 ms · p95 110.06 ms · p99 191.32 ms
- Toàn bộ request `payment_options` (305 lượt, trong cùng tiến trình, không qua mạng): p50 36.56 ms · p95 66.74 ms · p99 114.14 ms
- Toàn bộ request `place_order` (670 lượt, trong cùng tiến trình, không qua mạng): p50 61.63 ms · p95 133.87 ms · p99 229.24 ms
- Thời gian chạy: 202.3 giây cho 3354 bước; lỗi server: 0

## Giới hạn
- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.
- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.
- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.
- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.
