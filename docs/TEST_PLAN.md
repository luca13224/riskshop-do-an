# TEST PLAN

> Trạng thái: **Đang dùng**. Kết quả dưới đây là số thật từ các lần chạy đã ghi lại trong `docs/experiments/`.

## 1. Kiểm thử tự động (pytest, `backend/tests`)
Chạy trên CSDL riêng `riskshop_test` (xóa sạch trước mỗi test), qua đúng các migration thật.
- Unit test từng luật và ma trận quyết định (`test_risk_rules.py`).
- Kịch bản end-to-end qua API: mỗi loại lạm dụng có kịch bản "lạm dụng" và "hợp lệ dễ nhầm" (`test_risk_scenarios.py`).
- Checkout: idempotency, khóa tồn kho, lượt dùng voucher (`test_order.py`, `test_cart.py`).
- Case, phân quyền, audit log, Attack Lab, trang luật, báo cáo, demo reset.
- Bộ mô phỏng: khoảng tin cậy Wilson, tái lập theo seed, chạy quy mô nhỏ (`test_simulator.py`).
- Lần chạy gần nhất: **126 test qua** (2026-10-30).

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
- Sau lần chạy test, không chỉnh luật dựa trên kết quả này. Nếu sửa luật, phải sinh tập test mới (seed khác) để đánh giá lại.

## 4. Giới hạn
- Dữ liệu hoàn toàn mô phỏng; tham số persona là giả định, không khái quát cho sàn thật.
- Thời gian bị nén; chạy tuần tự nên không phải phép đo tải.
