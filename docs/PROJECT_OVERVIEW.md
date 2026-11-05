# PROJECT OVERVIEW

> Cập nhật lần cuối: 2026-11-03 · Trạng thái: **Sản phẩm ~85–90% (bộ luật v3, 190 test qua); đang chuyển sang đo bổ sung và viết báo cáo**

## 1. Đề tài (dự kiến)
**Xây dựng hệ thống kiểm soát rủi ro và ngăn ngừa lạm dụng chính sách trên sàn thương mại điện tử.**

- Sinh viên: Luca — Hệ thống thông tin quản lý, Trường Đại học Thủy Lợi
- Giảng viên hướng dẫn: ThS. Tạ Chí Hiếu
- Mục tiêu nội bộ: hoàn thiện sản phẩm trước 30/11/2026; hạn nộp khoảng cuối 12/2026 (cần GVHD xác nhận). Report tháng 10 gửi GVHD trước 08/11.

## 2. Bối cảnh và vấn đề
**Bối cảnh.** Sàn TMĐT dùng voucher người mới và thanh toán khi nhận hàng (COD) để hạ rào cản mua lần đầu. Hai chính sách này cũng mở ra hai kiểu lạm dụng phổ biến. Liên quan: người mua hợp lệ, người bán / sàn, đội vận hành rủi ro. **[XM]** số liệu quy mô TMĐT và tỷ lệ COD ở Việt Nam: chỉ dùng nguồn kiểm chứng được (Sách trắng TMĐT của Bộ Công Thương, báo cáo VECOM); chưa tra thì không ghi số.

| Mã | Vấn đề | Hậu quả |
|---|---|---|
| P1 | Farm tài khoản gom voucher người mới | Ngân sách khuyến mãi vào tay kẻ lạm dụng, không tạo khách thật |
| P2 | Bùng hàng COD | Mất phí vận chuyển hai chiều, hàng kẹt, người bán chịu rủi ro |
| P3 | Bị chặn thì tạo tài khoản mới làm lại | Lệnh khóa theo tài khoản bị vô hiệu |
| P4 | Kiểm tra thủ công, không nhất quán, khó truy vết | Mỗi người xử lý một kiểu, không giải thích được vì sao chặn |
| P5 | Chặn nhầm khách thật (gia đình chung Wi-Fi, khách mới mua COD giá trị cao) | Mất khách, phát sinh khiếu nại, ảnh hưởng uy tín |

## 3. Mục tiêu đo được
> **Bản đề xuất ngày 2026-11-03, cần Luca chốt và hỏi GVHD.** Các mục tiêu này được viết **sau** các lần đo v1–v3, nên:
> (a) O4 giữ nguyên chỉ tiêu FPR ≤ 5% của đề cương và báo cáo trung thực là chưa đạt;
> (b) mọi kết luận đạt / chưa đạt cho bộ luật mới phải dùng **tập test seed mới** (seed 5 trở đi), chạy một lần sau khi khóa luật.

Phạm vi: 2 nhóm chính sách (voucher tân thủ, COD), dữ liệu mô phỏng, chạy trên máy local. Đơn vị đo trong mô phỏng: tài khoản.

| Mã | Mục tiêu | Chỉ số | Ngưỡng | Vấn đề | Số đã có |
|---|---|---|---|---|---|
| O1 | Bắt lạm dụng kiểu đã biết | Recall kiểu đã biết, tập test | ≥ 80% | P1, P2 | test_v2 seed 5: **53,8%, chưa đạt** (85,5% ở bộ v1 là dữ liệu dễ hơn thực tế, TEST_PLAN 3e) |
| O2 | Không làm phiền khách bình thường | FPR khách thông thường | ≤ 2% | P5 | 0% ở mọi lần đo |
| O3 | Hạn chế chặn nhầm ca khó | FPR hard negative | ≤ 20% | P5 | test_v2 seed 5: 17,6% đạt; các lần trước 18,2% – 31,2%, **có lần chưa đạt** |
| O4 | Chỉ tiêu FPR tổng của đề cương | FPR trên toàn bộ tài khoản hợp lệ | ≤ 5% | P5 | test_v2 seed 5: 6,2%; v1 test: 7,9% · **chưa đạt** |
| O5 | Không làm chậm checkout | p95 chấm điểm; p95 request đặt hàng ở 1 / 10 / 50 người đồng thời | ≤ 50 ms (chấm điểm) | mọi P | p95 chấm điểm ≤ 36,2 ms ở 1/10/50 người: **đạt**; request đặt hàng p95 lên 1,5–1,9 s ở 50 người (TEST_PLAN 3f) |
| O6 | Quyết định giải thích được, truy vết được | % quyết định khác ALLOW có luật đã khớp, giá trị đặc trưng, audit | 100% | P4 | 8/8 mục kiểm tra đạt 100% trên dữ liệu demo: **đạt** (TEST_PLAN 3g) |
| O7 | Lệnh khóa không bị né bằng tài khoản mới | % tài khoản né khóa (chung ≥ 2 điểm) bị khóa thanh toán | ≥ 90% | P3 | test_v4 seed 10 (sau ADR-015): **14/14 = 100% bị khóa, đạt** (KTC 95%: 78,5%–100%, mẫu nhỏ); người nhà 0/8 bị hạn chế (TEST_PLAN 3l). Trước đó 66,7% (3i) |
| O8 | Khách bị chặn nhầm có đường sửa sai | % quyết định hạn chế khiếu nại được; chấp nhận thì tự miễn trừ / gỡ khóa | 100% | P5 | có test |
| O9 | Analyst xử lý case nhanh, nhất quán | Thời gian trung vị xử lý 1 case; tỉ lệ hai người cùng kết luận | đặt ngưỡng **trước** buổi đo (gợi ý ≤ 2 phút, ≥ 80%) | P4 | **[CẦN ĐO]** |

Yêu cầu chi tiết (FR / NFR / BR / UC) ở `docs/REQUIREMENTS.md`. Kịch bản đo cho các ô **[CẦN ĐO]** ở `docs/reviews/2026-11-03_7_KHAI_NIEM_REVIEW.md` mục 4.

## 4. Phạm vi
| Mức | Nội dung | Trạng thái |
|---|---|---|
| MVP | 2 nhóm chính sách (voucher tân thủ, COD); Risk Engine rule-based có phiên bản; Shop; Risk Console (Monitor, Case, Luật, Báo cáo, Audit, Attack Lab); khiếu nại | Xong |
| Recommended | Trust Score 2 lớp (ADR-009); khóa quyền mua tự động (ADR-010); truy vết né khóa (ADR-011); túi voucher; simulator dev/test | Xong |
| Advanced/Optional | Đồ thị liên kết tài khoản (xong, bản cơ bản); ML so sánh với rule; tách Risk Engine thành dịch vụ dùng cho sàn khác; bằng chứng camera đóng gói | Đồ thị xong; phần còn lại là hướng phát triển |

**Ngoài phạm vi:** thanh toán thật, dữ liệu cá nhân thật, triển khai production.

## 5. Hiện trạng
- [x] Kiến trúc modular monolith (ADR-003), 11 ADR đã chốt
- [x] Shop, Risk Engine v3, Risk Console, khiếu nại, khóa tự động, truy vết né khóa
- [x] Thực nghiệm v1, v2, v3 trên tập dev / test (TEST_PLAN mục 3, 3c, 3d)
- [x] Report tháng 10 (bản Word, chưa gửi)
- [x] REQUIREMENTS.md bản 1 (2026-11-03)
- [ ] Chốt bảng mục tiêu O1–O9 với GVHD
- [x] Đo bổ sung 2026-11-03: v3.1 trên seed 5 (ADR-012), tải đồng thời, script đối chiếu giải thích / audit
- [x] Đo O7 (TEST_PLAN 3h), sửa theo ADR-013 và đo lại trên seed 7 (3i): 46,7% → 66,7%, vẫn chưa đạt
- [x] ADR-015: khóa kẻ né khóa thao tác như bot ngay ở bước áp mã; test_v4 seed 10: 100% bị khóa (3l)
- [ ] Còn đo: buổi đo thời gian xử lý case (O9)
- [ ] Tra nguồn số liệu cho phần bối cảnh
- [ ] Viết báo cáo theo `docs/BAO_CAO_DAN_Y.md`

## 6. Rủi ro chính
| Rủi ro | Ảnh hưởng | Hướng xử lý |
|---|---|---|
| Không có dữ liệu gian lận thật | Khó khái quát kết quả | Mô phỏng có hard negative và biến thể chưa biết; ghi rõ giới hạn |
| Đặt mục tiêu sau khi đã đo | Bị coi là dời cột gôn | Giữ chỉ tiêu đề cương, báo cáo chưa đạt; kiểm bộ luật mới trên seed mới |
| Phạm vi phình to | Không kịp viết báo cáo | Dừng thêm tính năng sau 30/11, chỉ sửa lỗi |
| Lạm dụng ML | Khó giải thích, khó bảo vệ | Rule-based làm lõi, ML là hướng phát triển |
