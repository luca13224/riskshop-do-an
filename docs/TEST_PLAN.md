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
- Điểm tin cậy và túi voucher (`test_trust.py`); khóa quyền mua hàng tự động, gỡ khóa, khiếu nại gỡ khóa (`test_restrictions.py`).
- Né lệnh khóa bằng tài khoản mới, gia đình chung máy, chung IP, khóa thủ công (`test_linked_ban.py`, `test_restrictions.py`).
- Lần chạy gần nhất: **192 test qua** (2026-11-03).

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

## 3h. Né lệnh khóa bằng tài khoản mới (2026-11-03, ADR-011, mục tiêu O7)
Bộ dữ liệu mới `dev_v3` / `test_v3` = bộ v2 + 4 persona (định nghĩa trước khi chạy, xem đầu `simulator/personas.py`). Mỗi nhóm có một tài khoản **nguồn** mua một đơn rồi bị nhân viên khóa vô thời hạn; tài khoản nguồn không được chấm.
- Né khóa chung ≥ 2 điểm (thiết bị, SĐT nhận hàng, địa chỉ; ở test có 4 tổ hợp) — kiểu đã biết.
- Né khóa bằng nhiều tài khoản mới cùng máy, gom mã người mới — kiểu đã biết.
- Né khóa chỉ giữ SĐT nhận hàng cũ (máy mới, địa chỉ mới) — **biến thể chưa biết**, theo ADR-011 chỉ bị trừ điểm + mở case.
- Người nhà dùng chung máy với tài khoản bị khóa — hard negative.
```
.venv/Scripts/python -m simulator --dataset dev_v3 --seed 1
.venv/Scripts/python -m simulator --dataset test_v3 --seed 6 --confirm-test
```

| test_v3 seed 6 (bộ luật v3.1) | Bị gắn cờ | Không lấy được mã | **Bị khóa thanh toán** |
|---|---|---|---|
| Né khóa, chung ≥ 2 điểm (15) | 15/15 (KTC 95%: 79,6%–100%) | 15/15 | **7/15 = 46,7%** (KTC 95%: 24,8%–69,9%) |
| Né khóa, cùng máy gom mã (12) | 12/12 | 12/12 | 8/12 = 66,7% |
| Né khóa, chỉ giữ SĐT (6, chưa biết) | 6/6 | 6/6 | 0/6 (đúng thiết kế) |
| Người nhà dùng chung máy (8, hard negative) | **7/8 bị hạn chế** (gỡ mã, tắt COD) | — | 0/8 |

Toàn bộ tập: precision 78,5%, recall 49,4% (đã biết 60,2%, chưa biết 16,7%), FPR khách thường 0%, FPR hard negative 23,5%. Không so trực tiếp với v2 vì dân số khác (thêm persona). Chi tiết: [test v3](experiments/test_v3_seed6_scale1.md), [dev v3](experiments/dev_v3_seed1_scale1.md).

### Đọc kết quả (trung thực)
- **Lợi ích bị chặn 100%:** không tài khoản né khóa nào dùng được mã người mới, kể cả biến thể chưa biết.
- **O7 (≥ 90% bị khóa thanh toán) chưa đạt: 46,7%.** Nguyên nhân (đã tra trên tập dev): ở bước áp mã, R16 (+45) cộng R01 đủ để gỡ mã; kẻ né khóa bỏ đơn ngay, không tới bước đặt hàng. Lệnh khóa liên kết chỉ được ghi khi có ≥ 2 điểm chung, mà địa chỉ / SĐT chỉ biết lúc đặt hàng; ở bước áp mã hệ thống mới thấy thiết bị (1 điểm). Tài khoản bị khóa là những tài khoản chung máy **và** có từ 2 lần thử mã trên máy đó (điều kiện spam).
- **Cái giá với người nhà: 7/8 bị gỡ mã và tắt COD** vì R16 cộng thẳng vào điểm chính sách voucher / COD. ADR-011 định "chung 1 điểm, không spam → chỉ trừ điểm tin cậy + mở case", nhưng điểm R16 đủ lớn để kích hoạt hạn chế ở lớp giao dịch. Đây là khác biệt giữa thiết kế và cài đặt, cần quyết định (xem đề xuất bên dưới).
- Đề xuất (chưa làm, cần Luca chốt, đo lại trên seed mới):
  - (a) Ghi lệnh khóa ngay ở bước áp mã khi thiết bị chung với tài khoản bị khóa và tài khoản mới đang dùng mã người mới (dùng mã người mới chính là hành vi cần chặn).
  - (b) R16 chỉ trừ điểm tin cậy khi liên kết = 1 (không cộng vào điểm voucher / COD), đúng ý ADR-011; giảm hạn chế nhầm người nhà.
- Sau lần chạy này không chỉnh luật theo kết quả test; nếu làm (a) / (b) thì đo trên test_v3 seed mới (7 trở đi).

## 3e. Bộ luật v3.1 — luật giao dịch không trừ điểm tài khoản (2026-11-03, ADR-012)
Thay đổi: R08 (COD giá trị cao, ít lịch sử) không còn trừ vào điểm tin cậy tài khoản (`trust.exclude_rules`), vẫn tính vào điểm COD của đơn. Kiểm tra nhanh trên dev_v2 (không có tham số nào để tinh chỉnh: kết quả trùng v3), sau đó chạy **tập test_v2 seed 5 (seed chưa từng dùng)**, mỗi phiên bản một lần, cùng dân số:
```
.venv/Scripts/python -m simulator --dataset test_v2 --seed 5 --confirm-test                      # v3.1
.venv/Scripts/python -m simulator.trust_report --out ../docs/experiments/test_v2_seed5_trust_v3.1.json
.venv/Scripts/python -m simulator --dataset test_v2 --seed 5 --confirm-test --trust-all-rules    # v3
.venv/Scripts/python -m simulator.trust_report --out ../docs/experiments/test_v2_seed5_trust_v3.json
```

| Chỉ số (test_v2 seed 5, 438 tài khoản) | v3 | v3.1 |
|---|---|---|
| Precision | 75,7% (56/74) | 75,7% (56/74) |
| Recall tất cả / kiểu đã biết / biến thể chưa biết | 38,4% / 53,8% / 0% | giống v3 |
| FPR tất cả / khách thường / hard negative | 6,2% / 0% / 17,6% | giống v3 |
| Khách mới mua COD giá trị cao: trung vị điểm tin cậy | 60 | **100** |
| — số tài khoản dưới 50 điểm (bị khóa mã) | 3/10 | **0/10** |
| — đơn bị giữ chờ xác minh | 10/10 | 10/10 |

Dấu vân tay: v3.1 `2fa09e9c88da841a…`, v3 `6879ec96daadcfce…`. Chi tiết: [v3.1](experiments/test_v2_seed5_scale1.md), [v3](experiments/test_v2_seed5_scale1_trust-all-rules.md), phân bố điểm [v3.1](experiments/test_v2_seed5_trust_v3.1.json) / [v3](experiments/test_v2_seed5_trust_v3.json).

### Đọc kết quả (trung thực)
- v3.1 sửa đúng chỗ đã phát hiện ở 3d: khách mới hợp lệ không còn "kém tin cậy hơn farm". Các nhóm khác không đổi điểm, khả năng phát hiện không đổi.
- **Mục tiêu O1 (recall kiểu đã biết ≥ 80%) chưa đạt trên bộ dữ liệu v2:** 53,8% (KTC 95%: 44,3%–63,1%). Con số 85,5% ở mục 3 đo trên bộ v1, nơi mọi farm vô tình chung một địa chỉ (dễ hơn thực tế). Phần lọt chủ yếu là farm phân tán (44% bị bắt) và tài khoản treo nhiều đơn COD (0/6).
- Mục tiêu O3 (FPR hard negative ≤ 20%) đạt ở lần này: 17,6%. O4 (FPR tổng ≤ 5%) chưa đạt: 6,2% (KTC 95%: 3,9%–9,5%).

## 3f. Độ trễ khi nhiều người đặt hàng cùng lúc (2026-11-03, kịch bản E2, mục tiêu O5)
Script [`backend/scripts/load_test.py`](../backend/scripts/load_test.py): mỗi người dùng ảo có tài khoản, thiết bị riêng, lặp "thêm giỏ → đặt hàng trả trước". 3 mức tải × 3 lượt × 200 lần đặt hàng. Máy: Windows 11, 16 luồng CPU AMD, Python 3.11; **1 tiến trình uvicorn**, MariaDB XAMPP cùng máy, CSDL mô phỏng. Không phải đo năng lực production.

| Người dùng đồng thời | Request đặt hàng p50 / p95 / p99 (ms) | Chấm điểm Risk Engine p50 / p95 / p99 (ms) | Thông lượng (đơn/giây) |
|---|---|---|---|
| 1 | 33–34 / 38,6–39,4 / 40–46 | 12,4–13,1 / 15,1–16,1 / 16–20 | 19,6–20,3 |
| 10 | 167–177 / 268–342 / 332–780 | 17,9–18,9 / 32,6–35,5 / 76–96 | 28,3–29,6 |
| 50 | 695–870 / 1.547–1.858 / 2.008–2.155 | 18,4–19,9 / 34,0–36,2 / 44–46 | 26,7–28,8 |

(Khoảng giá trị = nhỏ nhất – lớn nhất của 3 lượt.) Mọi request đều thành công (1.800/1.800 mã 201). Dữ liệu: [load_test_20261103.json](experiments/load_test_20261103.json).

### Đọc kết quả (trung thực)
- **O5 đạt ở phần Risk Engine:** p95 chấm điểm ≤ 36,2 ms ở cả 3 mức (ngưỡng 50 ms). p99 ở 10 người lên 76–96 ms: có đuôi chậm, chưa rõ nguyên nhân (cần đo thêm nếu muốn kết luận).
- **Request đặt hàng chậm dần khi đông người, nhưng nút thắt không nằm ở Risk Engine:** thông lượng dừng ở khoảng 28 đơn/giây từ mức 10 người, nên thêm người chỉ làm hàng đợi dài ra (50 người: p95 khoảng 1,5–1,9 giây, phần chấm điểm chỉ khoảng 35 ms trong đó). Nguyên nhân khả dĩ (chưa đo tách): một tiến trình uvicorn, khóa dòng tồn kho / lượt dùng voucher trong giao dịch, MariaDB cấu hình mặc định của XAMPP.
- Hướng cải thiện nếu cần (Advanced): chạy nhiều worker uvicorn, đo tách thời gian từng bước của checkout.

## 3g. Tính giải thích được và audit (2026-11-03, kịch bản E3, mục tiêu O6)
Script chỉ đọc [`backend/scripts/audit_check.py`](../backend/scripts/audit_check.py), 8 mục kiểm tra (quyết định khác ALLOW có lý do; quyết định có ảnh chụp đặc trưng và phiên bản ma trận; luật khớp có câu lý do và giá trị thực tế; case, khiếu nại, lệnh khóa, gỡ khóa, sửa luật đều có audit).

| CSDL | Kết quả |
|---|---|
| Dữ liệu demo (657 quyết định, 118 khác ALLOW, 708 luật khớp, 8 case đóng, 3 lệnh khóa, 2 lần gỡ) | **8/8 mục đạt 100%** · [chi tiết](experiments/audit_check_main_20261103.json) |
| CSDL đo tải (1.810 quyết định, đều ALLOW) | 8/8 đạt (chỉ mục "có ảnh chụp và phiên bản ma trận" có dữ liệu) |

- Lần chạy đầu bắt được 5 quyết định không có phiên bản ma trận. Tra lại: đều là lần chặn vì tài khoản **đang bị khóa** (ADR-010, không chấm điểm, lý do khóa lưu trong ảnh chụp đặc trưng). Đúng thiết kế; script được sửa để nhận diện trường hợp này.
- Giới hạn: chưa có dữ liệu khiếu nại đã kết luận và sửa luật trên CSDL demo (0 bản ghi), hai mục này mới được kiểm bằng test tự động. Nên chạy lại script sau buổi tập demo.

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
