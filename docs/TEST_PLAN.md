# TEST PLAN

> Trạng thái: **Đang dùng**. Kết quả dưới đây là số thật từ các lần chạy đã ghi lại trong `docs/experiments/`.

## 1. Kiểm thử tự động (pytest, `backend/tests`)
Chạy trên CSDL riêng `riskshop_test` (xóa sạch trước mỗi test), qua đúng các migration thật.
- Unit test từng luật và ma trận quyết định (`test_risk_rules.py`).
- Kịch bản end-to-end qua API: mỗi loại lạm dụng có kịch bản "lạm dụng" và "hợp lệ dễ nhầm" (`test_risk_scenarios.py`).
- Checkout: idempotency, khóa tồn kho, lượt dùng voucher (`test_order.py`, `test_cart.py`).
- Case, phân quyền, audit log, Attack Lab, trang luật, báo cáo, demo reset.
- Giới hạn đăng nhập sai, che email trên Console, xem liên hệ có lý do + audit (`test_privacy.py`).
- Bộ mô phỏng: khoảng tin cậy Wilson, tái lập theo seed, chạy quy mô nhỏ (`test_simulator.py`).
- Danh sách sản phẩm: sắp xếp theo giá, lọc khoảng giá, từ chối tham số sai (`test_catalog.py`); Console Đơn hàng: lọc trạng thái, tìm mã đơn, phân trang, đếm theo trạng thái (`test_order.py`); robots.txt, sitemap (`test_seo.py`).
- Lần chạy gần nhất: **164 test qua** (2026-10-31).

## 2. Thực nghiệm mô phỏng (`backend/simulator`)
```
.venv/Scripts/python -m simulator --dataset dev --seed 1
.venv/Scripts/python -m simulator --dataset test --seed 2 --confirm-test
```
- Chạy trên CSDL riêng `riskshop_sim` (bị xóa mỗi lần chạy). Mỗi tài khoản giả gọi **đúng API** của shop qua `TestClient`.
- Nhãn thật lưu ở `sim_labels`; Risk Engine không bao giờ đọc bảng này.
- Persona hợp lệ: khách mới, khách quen. Hard negative (hợp lệ nhưng dễ nhầm): gia đình chung Wi-Fi/địa chỉ, khách mới mua COD giá trị cao, khách quen đặt nhiều đơn.
  Lạm dụng: farm voucher, bùng hàng COD. Tập test thêm 2 **biến thể chưa biết**: farm phân tán (mỗi tài khoản một máy, đổi IP), tài khoản mới treo nhiều đơn COD.
- Đơn vị đo: tài khoản. Bị gắn cờ = có ít nhất một quyết định khác ALLOW.
- **Quy tắc chống học thuộc:** chỉ tinh chỉnh luật trên tập dev; tập test chạy một lần sau khi khóa luật. Báo cáo ghi dấu vân tay bộ luật để kiểm chứng.

## 3. Kết quả (bộ luật v1, dấu vân tay `3df073b71c7a9362…`)
| Chỉ số | Dev (seed 1, 212 tài khoản) | Test (seed 2, 356 tài khoản) |
|---|---|---|
| Precision | 81,4% (35/43) | 74,7% (59/79) |
| Recall tất cả | 85,4% (35/41) | 57,8% (59/102) |
| Recall kiểu đã biết | 85,4% | 85,5% (59/69) |
| Recall biến thể chưa biết | — | **0% (0/33)** |
| FPR khách thông thường | 0% (0/130) | 0% (0/190) |
| FPR hard negative | 19,5% (8/41) | 31,2% (20/64) |
| Độ trễ chấm điểm p95 | 7,78 ms | 11,5 ms |

Chi tiết và KTC 95%: [dev](experiments/dev_seed1_scale1.md), [test](experiments/test_seed2_scale1.md).

### Đọc kết quả (trung thực)
- Kiểu lạm dụng đã biết được bắt ổn định giữa dev và test (~85%), khách bình thường không bị ảnh hưởng.
- **Biến thể chưa biết lọt hoàn toàn.** Luật dựa vào thiết bị/IP/địa chỉ dùng chung, nên farm tách thiết bị + đổi IP không để lại dấu vết chung. Đây là giới hạn cố hữu của rule-based, là lý do đề xuất hướng phát triển (đồ thị liên kết, ML).
- Hard negative bị ảnh hưởng: khách mới mua COD giá trị cao 100% bị giữ chờ duyệt (đúng thiết kế fail-closed, chấp nhận đánh đổi); gia đình đông người (5–6 người, chỉ có ở tập test) bị gỡ voucher vì vượt ngưỡng "≥5 tài khoản/địa chỉ".
- Bùng hàng COD chỉ bắt được ~50–67%: kẻ có lịch sử ngắn (dưới 3 đơn) chưa đủ dữ liệu cho luật tỉ lệ thất bại.
- Quyết định 2026-10-30: giữ bộ luật v1, các điểm yếu trên trình bày là giới hạn và hướng phát triển (đồ thị liên kết tài khoản, ML).
- Sau lần chạy test, không chỉnh luật dựa trên kết quả này. Nếu sửa luật, phải sinh tập test mới (seed khác) để đánh giá lại.

## 3d. Bộ luật v3 — Trust Score 2 lớp (2026-10-31, ADR-009)
Lệnh so sánh trên cùng dân số (tập `test_v2`, seed 4 mới):
```
.venv/Scripts/python -m simulator --dataset test_v2 --seed 4 --confirm-test
.venv/Scripts/python -m simulator --dataset test_v2 --seed 4 --confirm-test --no-trust     --disable-rule PHONE_MULTI_ACCOUNTS --disable-rule ADDRESS_HOPPING --disable-rule VOUCHER_SUBSIDY_HIGH --disable-rule PROFITABLE_CUSTOMER
```

| Chỉ số (test_v2 seed 4, 425 tài khoản) | v2 | v3 (Trust) |
|---|---|---|
| Precision | 72,3% (47/65) | 72,3% (47/65) |
| Recall | 34,6% (47/136) | 34,6% (47/136) |
| FPR khách thường / hard negative | 0% / 18,2% | 0% / 18,2% |
| Request đặt hàng p95 | 41,2 ms | 42,8 ms |

Trung vị điểm tin cậy thấp nhất của mỗi tài khoản, theo nhóm (v3): khách mới bình thường 100 · khách quen 100 · gia đình 70 · nhóm trọ 4G 80 · farm phân tán 70 · farm 50 · **khách mới mua COD giá trị cao 30** · bùng hàng COD 70 · farm chia nhiều điểm nhận 90. Số tài khoản bị kéo xuống < 30 mà chưa bị hạn chế (cảnh báo sớm thêm): **0**. Dữ liệu: [phân bố](experiments/test_v2_seed4_trust_distribution.json).

### Đọc kết quả (trung thực)
- Lớp Trust **không làm đổi** kết quả trên bộ mô phỏng: ngưỡng khóa mã (< 50) gần trùng ngưỡng gỡ voucher cũ, bậc "Xem xét" chỉ mở case chứ không hạn chế.
- R12 (chung SĐT), R14 (tỷ lệ trợ giá) chưa có số liệu: bộ mô phỏng không giả định các hành vi này (cố ý, để không "đặt ra đề rồi tự giải"). Chúng được kiểm bằng test kịch bản (`tests/test_trust.py`).
- Giá trị của lớp Trust ở chỗ khác: một con số và "sổ trừ điểm" cho analyst, cắt quyền lợi theo bậc thay vì chỉ cho/chặn, túi voucher hiển thị rõ cho khách.
- **Vấn đề thiết kế phát hiện được:** khách mới hợp lệ mua COD giá trị cao có điểm tin cậy ~30, thấp hơn farm, vì luật theo đơn R08 cũng bị tính vào điểm tài khoản. Không sửa trên tập test này; đề xuất v3.1 và đo trên tập test mới.

## 3c. Bộ luật v2 (R11) trên tập dữ liệu mới (2026-10-31, ADR-008)
Lệnh:
```
.venv/Scripts/python -m simulator --dataset dev_v2 --seed 1 [--disable-rule ADDR_VOUCHER_RING]
.venv/Scripts/python -m simulator --dataset test_v2 --seed 3 --confirm-test [--disable-rule ADDR_VOUCHER_RING]
```
- `dev_v2`/`test_v2` thêm: farm phân tán (giờ là kiểu **đã biết**), hard negative mới "nhóm ở trọ dùng 4G riêng", và ở test một **biến thể chưa biết mới** "farm gom hàng về 2–3 điểm nhận" (định nghĩa trước khi chạy, không tinh chỉnh theo nó). Mỗi farm một địa chỉ riêng (bộ v1 vô tình cho mọi farm chung một địa chỉ).
- Ngưỡng R11 chọn trên dev_v2 (xem thiết kế, mục 9). Bộ luật v2 khóa với dấu vân tay `1d9f87d5a9d57e9a…`; chạy "v1" bằng cách tắt R11 trên cùng dân số (`86d43d9a06f10b0d…`).

| Chỉ số (tập test_v2, seed 3, 451 tài khoản) | v1 (không R11) | v2 (có R11) |
|---|---|---|
| Precision | 75,3% (55/73) | 73,6% (67/91) |
| Recall tất cả | 36,4% (55/151) | 44,4% (67/151) |
| Farm phân tán (kiểu đã biết) | 0% (0/32) | 37,5% (12/32) |
| Farm gom về nhiều điểm (chưa biết mới) | 0% (0/40) | 0% (0/40) |
| FPR khách thông thường | 0% (0/190) | 0% (0/190) |
| FPR hard negative | 16,4% (18/110) | 21,8% (24/110) |
| — trong đó nhóm trọ 4G | 0% (0/41) | 14,6% (6/41) |
| Độ trễ request đặt hàng p95 (toàn bộ API) | 44,7 ms | 44,5 ms |

Chi tiết và KTC 95%: [test v2](experiments/test_v2_seed3_scale1.md), [test v1 trên cùng dân số](experiments/test_v2_seed3_scale1_without-ADDR_VOUCHER_RING.md), [dev v2](experiments/dev_v2_seed1_scale1.md).

### Đọc kết quả (trung thực)
- R11 bắt được hơn 1/3 farm phân tán mà v1 bỏ lọt hoàn toàn; 4 tài khoản đầu của mỗi farm vẫn lọt (chưa đủ dấu vết cụm).
- Cái giá: 6 trên 41 người trong nhóm ở trọ dùng 4G riêng bị gỡ voucher nhầm. Với dữ liệu hiện có, độ phân tán mạng **không phân biệt** được nhóm này với farm.
- Biến thể chưa biết mới (chia nhỏ cụm ra 2–3 điểm nhận) lọt 100%: luật theo ngưỡng luôn có cách né bằng cách ở dưới ngưỡng. Đây là lý do hướng phát triển là học máy trên đồ thị khi có dữ liệu thật.
- Độ trễ request p95 ở lần chạy này (~44 ms, đo cả request API trong tiến trình mô phỏng) không so trực tiếp được với "độ trễ chấm điểm p95" của v1 (chỉ phần Risk Engine); giữa hai lần chạy cùng ngày, R11 không làm tăng độ trễ đo được.
- Tài khoản "bùng hàng COD" và "treo nhiều đơn COD" không đổi, vì R11 chỉ thuộc chính sách voucher.

## 3b. Kiểm thử thủ công giao diện (2026-10-31, sau khi chuyển Shop sang tông navy, ADR-007)
Chạy trên trình duyệt tích hợp, tài khoản khách Minh (dữ liệu demo), độ rộng 1440 px và 375 px.

| Bước | Kết quả |
|---|---|
| Danh mục: lọc 500.000đ – 2 triệu + giá tăng dần | Đúng: 9 sản phẩm, giá tăng dần; chip "Đang lọc" gỡ được từng bộ lọc; không tràn ngang ở 375 px |
| Thêm giỏ từ thẻ sản phẩm → Giỏ hàng | Đúng, số lượng trên biểu tượng giỏ cập nhật |
| Thanh toán: bấm Đặt hàng khi để trống | Lỗi hiện tại từng ô, viền đỏ, chữ đọc rõ trên nền tối |
| Thanh toán: tên và số điện thoại tự điền | **Lỗi, đã sửa**: ô trống khi thông tin khách tải sau lần vẽ đầu của form |
| Nhãn phương thức trả trước | **Lỗi, đã sửa**: còn chữ "(giả lập)" → "Trả trước (chuyển khoản)" |
| Đặt hàng COD | Tạo đơn, chuyển sang trang đơn với thông báo thành công |
| Khiếu nại (375 px) | Trạng thái rỗng hiển thị đúng, không tràn ngang |
| Console Đơn hàng: lọc "Chờ xác minh" | Ra đúng đơn bị giữ, cột thao tác ghi "Duyệt trong Case" |

Chưa kiểm: luồng bị hạn chế → khiếu nại bằng tài khoản Khang/Lan sau đợt đổi giao diện; độ rộng 768 px.

## 4. Giới hạn
- Dữ liệu hoàn toàn mô phỏng; tham số persona là giả định, không khái quát cho sàn thật.
- Thời gian bị nén; chạy tuần tự nên không phải phép đo tải.
