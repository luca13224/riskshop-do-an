# Rà soát đồ án theo khung 7 khái niệm, lần 2

> Ngày: 2026-11-19 · Tư vấn, **chưa phải quyết định** (quyết định chỉ ở [QUYET_DINH.md](../QUYET_DINH.md)). Lần 1: [2026-11-03](2026-11-03_7_KHAI_NIEM_REVIEW.md).
> Nguồn đọc: [TONG_QUAN](../TONG_QUAN.md), [YEU_CAU](../YEU_CAU.md), [KIEM_THU](../KIEM_THU.md) mục 3–3p, [QUYET_DINH](../QUYET_DINH.md) ADR-003 → ADR-017, [BAO_CAO_DAN_Y](../BAO_CAO_DAN_Y.md), [KIEN_TRUC](../KIEN_TRUC.md), kết quả trong [thuc_nghiem/](../thuc_nghiem/README.md).
> Nhãn: **[CẦN ĐO: …]** số chưa đo · **[THIẾU]** tài liệu chưa có · **[XM]** cần tra nguồn thật · **Đề xuất** = ý của Claude, Luca chốt.

**Đầu vào:** đề tài "Xây dựng hệ thống kiểm soát rủi ro và ngăn ngừa lạm dụng chính sách trên sàn thương mại điện tử" (ngành Hệ thống thông tin quản lý, ĐH Thủy Lợi, GVHD ThS. Tạ Chí Hiếu). Yêu cầu riêng của Khoa/GVHD: **[THIẾU]** mẫu trình bày báo cáo của Khoa; thang điểm GVHD nêu trong buổi họp 04/11: hình thức 20%, nội dung 70%, sáng tạo 10%; mức đăng ký B (MVP), muốn lên A cần MVP + phần nâng cấp có bằng chứng.

**Điểm mốc chính thức đề xuất:** bộ luật cuối là ADR-016 (R18) + ADR-017 (chỉ đổi tốc độ, không đổi quyết định). Lần chạy test_v5 seed 12 (chạy một lần, sau khi khóa luật) là **số đo chính thức** cho O1–O4, O7; O5 lấy từ KIEM_THU 3p. Không cần đốt thêm seed test.

---

## Phần 1. Chẩn đoán nhanh

| Bước | Trạng thái | Điểm /10 | Vấn đề chính | So với 03/11 |
|---|---|---|---|---|
| 1 Context | ⚠️ | 5 | Vẫn chưa có một số liệu thị trường nào có nguồn (tỷ lệ COD, quy mô TMĐT, mức bùng hàng). | Không đổi |
| 2 Pain point | ⚠️ | 6 | P1–P5 rõ, có hậu quả, nhưng chưa định lượng; chỉ có thể định lượng trong mô phỏng (B0 không kiểm soát). | Không đổi |
| 3 Objective | ⚠️ | 6 | Đã có O1–O9 có ngưỡng, nhưng chưa chốt với GVHD, thiếu mốc thời gian, O1 và O4 phụ thuộc thành phần bộ dữ liệu. | ❌ → ⚠️ |
| 4 Constraint | ⚠️ | 5 | Chỉ nằm trong bản tư vấn 03/11, chưa vào TONG_QUAN / báo cáo; thiếu ràng buộc mới phát hiện (máy phát triển, MariaDB 16 MB, IP chung). | Không đổi |
| 5 Method | ✅ | 9 | Mạnh và nhất quán (17 ADR). Chỉ dàn ý báo cáo đang mô tả bộ luật cũ (F01–F11, R01–R10). | Mạnh hơn |
| 6 Evaluation | ⚠️ | 7 | Có baseline, dev/test, KTC, đo tải đối chứng; nhưng kết quả rải ở 5 bộ dữ liệu, chưa có một bảng "kết quả cuối" và O9 chưa đo. | ⚠️ → ⚠️ (tốt hơn rõ) |
| 7 Impact | ⚠️ | 4 | Chưa có đoạn Impact; đã có số để viết (giảm 51% mã bị gom so với không kiểm soát ở bộ luật trước ADR-014, 0/40 khách quen bị chặn nhầm). | Không đổi |
| **Tổng** | | **42/70 (6,0/10)** | | |

**3 điểm yếu nặng nhất**
1. **Chưa có bảng "Mục tiêu → kết quả chính thức → đạt / chưa đạt"** trên một lần đo cố định. Số đang rải ở test_v2 … test_v5, mỗi bộ dữ liệu khác thành phần, nên hội đồng hỏi "hệ thống đạt bao nhiêu?" sẽ khó trả lời gọn.
2. **Context không có số liệu có nguồn**: câu hỏi đầu tiên của hội đồng ("vấn đề này lớn cỡ nào?") chưa có căn cứ.
3. **O1 (recall ≥ 80%) và O4 (FPR tổng ≤ 5%) chưa đạt mà chưa có giải trình định lượng**; Impact chưa viết nên chuỗi Pain point → Impact bị hở ở cuối.

---

## Phần 2. Bảng 7 khái niệm của đề tài

| Bước | Khái niệm | Định nghĩa | Trả lời câu hỏi | Áp dụng cho đề tài | Khác biệt nổi bật |
|---|---|---|---|---|---|
| 1 | Context | Bức tranh môi trường, đối tượng, hiện trạng | Chuyện gì đang xảy ra, ai liên quan? | • Sàn TMĐT dùng mã người mới và COD để hạ rào cản mua lần đầu<br>• Hai chính sách này bị lợi dụng: gom mã bằng nhiều tài khoản, đặt COD rồi không nhận<br>• Bên liên quan: khách hợp lệ, người bán / sàn, đội vận hành rủi ro<br>• **[XM]** tỷ lệ đơn COD, quy mô TMĐT VN (Sách trắng TMĐT – Bộ Công Thương, báo cáo VECOM) | • Bàn về **lạm dụng chính sách** hợp pháp về hình thức, không phải gian lận thẻ<br>• Nhìn cả phía khách bị chặn nhầm |
| 2 | Pain point | Bất cập cụ thể, có hậu quả | Khó ở đâu, hậu quả gì? | • P1 farm tài khoản gom mã người mới → ngân sách khuyến mãi không tạo khách thật<br>• P2 bùng hàng COD → mất phí vận chuyển hai chiều, hàng kẹt<br>• P3 bị khóa thì tạo tài khoản mới → lệnh khóa vô hiệu<br>• P4 xử lý thủ công, không truy vết → mỗi người một kiểu, không giải thích được<br>• P5 chặn nhầm khách thật → mất khách, khiếu nại<br>• Trong mô phỏng không kiểm soát (B0, test_v3 seed 8): 153 lượt mã người mới vào tay kẻ lạm dụng | • Chặn nhầm (P5) được coi là nỗi đau ngang hàng<br>• Né lệnh khóa (P3) ít đồ án xét tới |
| 3 | Objective | Trạng thái mong muốn, đo được | Cải thiện gì, đến đâu, đo bằng gì? | • O1 recall kiểu đã biết ≥ 80% · O2 FPR khách thường ≤ 2%<br>• O3 FPR hard negative ≤ 20% · O4 FPR tổng ≤ 5% (giữ từ đề cương)<br>• O5 p95 chấm điểm ≤ 50 ms ở 1 / 10 / 50 người<br>• O6 100% quyết định có lý do + audit · O7 ≥ 90% kẻ né khóa bị khóa<br>• O8 100% hạn chế khiếu nại được · O9 thời gian xử lý case [CẦN ĐO] | • Có mục tiêu phía khách thật (O2, O3, O8), không chỉ "bắt được bao nhiêu"<br>• Giữ chỉ tiêu đề cương dù chưa đạt (không dời cột gôn) |
| 4 | Constraint | Giới hạn thực tế | Thiếu gì, không thể làm gì? | • Không có dữ liệu gian lận thật, không nhãn → không lấy ML có giám sát làm lõi<br>• Một người, khoảng 2 tháng → modular monolith, một CSDL (ADR-003)<br>• Quyết định phải đồng bộ tại checkout → không dùng LLM trong luồng chính<br>• Dữ liệu cá nhân → che email, băm IP, xem liên hệ có lý do + audit<br>• Máy phát triển Windows, MariaDB XAMPP mặc định → số đo hiệu năng chỉ đúng cho máy này<br>• IP / thiết bị không định danh được người → không khóa theo IP | • Mỗi ràng buộc dẫn thẳng tới một lựa chọn kiến trúc, có ADR |
| 5 | Method | Cách thức, cơ chế, quy trình | Giải bằng cách nào? | • Risk Engine ở 3 điểm kiểm soát (áp mã, chọn thanh toán, đặt hàng)<br>• 18 luật dạng dữ liệu có phiên bản (3 kiểu), đặc trưng F01–F18 bằng SQL chỉ đọc<br>• Điểm theo chính sách + điểm tin cậy tài khoản, ma trận quyết định, REVIEW/BLOCK cần luật mạnh<br>• Khóa theo bậc, truy vết né khóa qua thiết bị / SĐT / địa chỉ, phát hiện cụm nối chuỗi<br>• Case, khiếu nại bốn mắt, audit; chạy thử luật trên dữ liệu cũ trước khi lưu | • Luật sửa trên Console không cần deploy, chạy thử trước được<br>• Mỗi quyết định giải thích bằng luật đã khớp và giá trị thật |
| 6 | Evaluation | Đo lường, kiểm chứng | Hiệu quả bao nhiêu, so với yêu cầu? | • Bộ mô phỏng gọi API thật, tách dev / test, mỗi seed test chạy một lần, KTC Wilson 95%<br>• Có hard negative và biến thể chưa biết; so với 3 baseline (không kiểm soát, luật thủ công, ngẫu nhiên)<br>• Số chính thức (test_v5 seed 12): precision 75,0%, recall kiểu đã biết 56,7%, FPR khách thường 0%, FPR hard negative 16,5%, F1 51,7% (luật thủ công 43,5%)<br>• O7: 14/14 bị khóa ở 2 seed độc lập; O5: đạt ở 1 và 10 người, chưa đạt ở 50 người | • Báo cáo cả chỗ thua (biến thể chưa biết 3,8%, O1, O4, O5 ở 50 người)<br>• Đo đối chứng có / không từng thay đổi |
| 7 | Impact | Lợi ích, khả năng mở rộng | Ai được lợi, giá trị lâu dài? | • Sàn: so với không kiểm soát, mã người mới bị gom giảm 153 → 75 lượt (−51%, test_v3 seed 8, bộ luật trước ADR-014; chưa đo B0 trên test_v5)<br>• Khách thật: 0/40 khách quen bị chặn nhầm (luật thủ công: 31/40, test_v5 seed 12); bị hạn chế thì có khiếu nại<br>• Đội rủi ro: 100% quyết định có lý do, audit; case gom theo cụm<br>• Mở rộng: luật là dữ liệu nên thêm chính sách mới (hoàn tiền) không đổi kiến trúc; tách Risk Engine thành dịch vụ (Đề xuất) | • Lợi ích được đo trên cùng tập với baseline, không chỉ ước tính |

---

## Phần 3. Ma trận truy vết

| Pain point | Objective | Constraint liên quan | Method | Metric (số chính thức) | Impact | Tình trạng |
|---|---|---|---|---|---|---|
| P1 Farm gom mã | O1, O3 | Không nhãn thật → luật + mô phỏng | R01–R05, R11, R12, R18 (cụm nối chuỗi), điểm tin cậy, `min_trust` của mã | Recall kiểu đã biết 56,7% (tài khoản); farm bị phát hiện theo nhóm 8/8, 5/5, 5/5 | Mã người mới bị gom −51% so với B0 (test_v3 seed 8) | ⚠️ O1 chưa đạt; Impact chưa viết thành văn |
| P2 Bùng hàng COD | O1 | Không có dữ liệu giao hàng thật | R07 (tỷ lệ làm mượt), R08, R10, R17, ẩn COD theo bậc | Bùng hàng 15/15, treo đơn 6/6 bị gắn cờ | Đơn COD rủi ro không được xác nhận | ⚠️ Thiếu chỉ số tiền / phí vận chuyển tránh được (chỉ có ước tính trong Console) |
| P3 Né lệnh khóa | O7 | IP không định danh người → khóa khi ≥ 2 điểm hoặc có hành vi bot / spam | F17, R16, khóa thanh toán (ADR-010, 011, 013, 015) | 14/14 bị khóa (seed 10 và seed 12); người nhà 0/8 | Lệnh khóa có hiệu lực thật | ✅ |
| P4 Xử lý thủ công | O6, O9 | Một người làm, không có đội analyst thật | Rule hit + giá trị đặc trưng, case gom cụm, audit, đồ thị liên kết, chạy thử luật | O6: 8/8 kiểm tra đạt 100%; O9 **[CẦN ĐO: buổi đo E4, bấm giờ 3–5 người, mỗi case 2 người]** | Xử lý có căn cứ, nhất quán | ❌ O9 chưa đo |
| P5 Chặn nhầm | O2, O3, O4, O8 | Ràng buộc thiết bị / IP chung trong gia đình, ký túc xá | REVIEW/BLOCK cần luật mạnh, hạn chế theo bậc, khiếu nại tự miễn trừ / gỡ khóa | FPR khách thường 0%; hard negative 16,5%; FPR tổng 8,3%; O8 có test | Khách thật không mất quyền vô lý | ⚠️ O4 chưa đạt, phụ thuộc tỷ lệ hard negative trong bộ dữ liệu |
| Mọi P | O5 | Máy phát triển, MariaDB XAMPP mặc định | Đặc trưng SQL có index, cache luật (ADR-017), nhiều worker | p95 ≤ 11,3 / 31,5 / 87–117 ms ở 1 / 10 / 50 người | Không làm chậm mua hàng ở tải vừa | ⚠️ Chưa đạt ở 50 người |

---

## Phần 4. Danh sách chỉnh sửa (theo mức ưu tiên)

| Ưu tiên | Vị trí | Bản hiện tại | Bản đề xuất | Lý do |
|---|---|---|---|---|
| 1 | TONG_QUAN mục 3, cột "Số đã có" | O1, O3, O4 ghi số test_v2 seed 5 (bộ luật v3.1) | Ghi số chính thức test_v5 seed 12; giữ số cũ ở KIEM_THU làm lịch sử | Mục tiêu phải so với bộ luật cuối |
| 1 | KIEM_THU, mục mới đầu chương | Kết quả rải ở 3–3p | Bảng "Mục tiêu → ngưỡng → kết quả chính thức → đạt / chưa đạt → nguồn" | Trả lời gọn câu "đạt bao nhiêu" |
| 1 | TONG_QUAN mục 2, Mở đầu báo cáo | "[XM] số liệu… chưa tra thì không ghi số" | 2–3 số liệu có trích dẫn (tỷ lệ COD, quy mô TMĐT VN, nếu có: tỷ lệ hoàn hàng / bùng hàng) | Context phải có căn cứ **[XM]**, không được bịa |
| 2 | Định nghĩa O1 | "Recall kiểu đã biết, tập test" | Giữ O1 như cũ (chưa đạt); **bổ sung** chỉ số phụ "tỷ lệ nhóm lạm dụng bị phát hiện", ghi rõ "đặt ngày 19/11, sau lần đo" | Recall tài khoản thấp vì farm lộ dần; không được thay O1 bằng chỉ số dễ đạt hơn |
| 2 | Giải trình O4 | "chưa đạt" | Thêm 1–2 câu: FPR tổng phụ thuộc tỷ lệ hard negative trong dân số (test_v5: 194/384 = 51% khách hợp lệ là ca khó, cao hơn thực tế **[giả định]**); FPR khách thường 0% | Chưa đạt nhưng giải thích được, không đổi chỉ tiêu |
| 2 | TONG_QUAN | Không có mục Constraint | Mục "Ràng buộc" (bảng Phần 2, bước 4) + cột "dẫn tới ADR nào" | Constraint phải giải thích vì sao chọn giải pháp |
| 2 | Kết luận báo cáo | [THIẾU] đoạn Impact | Đoạn Impact theo P1–P5 dùng số Phần 2 bước 7 | Đóng vòng Pain point → Impact |
| 2 | Mục tiêu | Chưa có mốc thời gian | Thêm "đánh giá trên bộ dữ liệu test_v5, trước 30/11/2026" (chữ T của SMART) | SMART |
| 3 | BAO_CAO_DAN_Y | F01–F11, R01–R10, 157 test, "chưa đo tải", "4 mục tiêu" | F01–F18, R01–R18, 218 test, có đo tải, 9 mục tiêu O1–O9 | Dàn ý đang mô tả bộ luật cũ |
| 3 | TONG_QUAN đầu file | "# PROJECT OVERVIEW", cập nhật 03/11, 190 test, 11 ADR | "# TỔNG QUAN DỰ ÁN", 19/11, 218 test, 17 ADR | Tài liệu cũ dễ bị đọc nhầm khi chấm |
| 3 | Đo O9 | [CẦN ĐO] | Buổi đo E4: 3–5 người, mỗi người 5 case, mỗi case 2 người; đặt ngưỡng trước buổi đo | Mục tiêu duy nhất còn chưa có số |
| 3 | O5 | Chưa đạt ở 50 người | Đo lại sau khi tăng `innodb_buffer_pool_size` (cần Luca đồng ý đổi cấu hình XAMPP) **hoặc** ghi là giới hạn | Có hướng cải thiện rõ, đã chẩn đoán |

---

## Phần 5. Ánh xạ vào báo cáo ĐATN
Khoa chưa gửi mẫu riêng **[THIẾU]**, nên ánh xạ theo [BAO_CAO_DAN_Y](../BAO_CAO_DAN_Y.md) (Mở đầu, Ch1 Tổng quan và cơ sở lý thuyết, Ch2 Phân tích – thiết kế, Ch3 Xây dựng, Ch4 Thực nghiệm – đánh giá, Kết luận). Nếu Khoa dùng khung "Ch1 Tổng quan, Ch2 Cơ sở lý thuyết, Ch3 Phân tích – thiết kế, Ch4 Cài đặt – thử nghiệm – đánh giá" thì tách Ch1 hiện tại làm hai.

| Bước | Vị trí trong báo cáo | Nguồn trong repo |
|---|---|---|
| 1 Context | Mở đầu: Lý do chọn đề tài; Ch1.1 Lạm dụng chính sách trong TMĐT | TONG_QUAN mục 2 + nguồn **[XM]** |
| 2 Pain point | Mở đầu: Lý do chọn đề tài (bảng P1–P5); Ch2.1 Bài toán nghiệp vụ | TONG_QUAN mục 2 |
| 3 Objective | Mở đầu: Mục tiêu (bảng O1–O9) | TONG_QUAN mục 3 |
| 4 Constraint | Mở đầu: Đối tượng, phạm vi, giới hạn; Ch2.3 (lý do kiến trúc) | Phần 2 bước 4 + QUYET_DINH (ADR-003, 004, 011) |
| 5 Method | Ch1.2–1.6 (lý thuyết: rule-based, đánh giá, quyền riêng tư); Ch2.3–2.8 (thiết kế); Ch3 (xây dựng) | KIEN_TRUC, BO_LUAT_RUI_RO, ERD, BAN_DO_MA_NGUON |
| 6 Evaluation | Ch4.1 thiết kế thực nghiệm; 4.2 kết quả chính thức + baseline; 4.3 độ trễ; 4.4 phân tích lỗi; 4.5 bảng mục tiêu đạt / chưa đạt | KIEM_THU, thuc_nghiem/ |
| 7 Impact | Kết luận: kết quả đạt được, giá trị; Hướng phát triển | Phần 2 bước 7 |

---

## Phần 6. 5 câu hội đồng dễ hỏi nhất

1. **"Không có dữ liệu thật thì làm sao biết hệ thống hiệu quả?"**
   Gợi ý: nói rõ đây là giới hạn (Constraint). Trình bày cách giảm thiểu: mô phỏng gọi API thật, nhãn tách khỏi Risk Engine, tách dev / test, mỗi seed test chạy một lần, có hard negative và biến thể chưa biết, so với 3 baseline trên cùng tập. Kết luận chỉ ở mức "trong các giả định mô phỏng".
2. **"Recall chỉ 56,7%, vậy hệ thống có tốt hơn kiểm tra thủ công không?"**
   Gợi ý: so trên cùng tập, luật thủ công F1 43,5% và chặn nhầm 31/40 khách quen; Risk Engine F1 51,7%, 0/40 khách quen. Theo nhóm, mọi farm đã biết đều bị phát hiện; recall theo tài khoản thấp vì farm lộ dần. Thừa nhận O1 chưa đạt.
3. **"Vì sao không dùng học máy?"**
   Gợi ý: không có nhãn thật (Constraint); quyết định phải giải thích được và chạy đồng bộ ở checkout; rule-based có phiên bản, chạy thử được. ML là hướng phát triển khi có nhãn từ kết quả case (hồi quy logistic, giải thích được).
4. **"Chặn nhầm khách thật thì sao? FPR 8,3% vượt 5% của đề cương."**
   Gợi ý: tách FPR khách thường (0%) và ca khó (16,5%); FPR tổng phụ thuộc tỷ lệ ca khó trong bộ dữ liệu. Hành động theo bậc (gỡ mã, ẩn COD trước khi giữ / chặn), khiếu nại tự miễn trừ, REVIEW/BLOCK cần luật mạnh. Chưa đạt, nói thẳng.
5. **"Kẻ gian biết luật thì lách được không?"**
   Gợi ý: có, đó là giới hạn của rule-based (biến thể chưa biết chỉ bắt 3,8%). Biện pháp: thông điệp không lộ luật, luật đổi được và chạy thử trên dữ liệu cũ trước khi bật, phát hiện theo cụm (R18), analyst xử lý case. Ví dụ cụ thể: kẻ né khóa xem vài sản phẩm trước khi áp mã thì thoát điều kiện "bot" của ADR-015 nhưng vẫn bị khóa ở bước đặt hàng nếu chung ≥ 2 điểm.

---

## Phần 7. Prompt tạo ảnh infographic
> Mẫu "PROMPT 3" không có trong tài liệu được gửi. GVHD từng nhắc phong cách poster kiểu MediHealth trong buổi họp 04/11; prompt dưới đây theo tinh thần đó và do Claude soạn **(Đề xuất)**. Mỗi ô ≤ 25 từ, tối đa 5 gạch đầu dòng.

```
Tạo infographic dọc khổ A3 phong cách poster học thuật hiện đại: nền xanh navy, khối thẻ bo góc trắng, điểm nhấn cyan và cam, chữ tiếng Việt dễ đọc, 7 thẻ đánh số nối bằng mũi tên. Tiêu đề: "Kiểm soát rủi ro và ngăn ngừa lạm dụng chính sách trên sàn TMĐT".
1 Ngữ cảnh:
- Sàn dùng mã người mới và COD để hút khách
- Hai chính sách bị lợi dụng
- Liên quan: khách, người bán, đội rủi ro
2 Vấn đề:
- Farm tài khoản gom mã
- Bùng hàng COD
- Bị khóa thì lập tài khoản mới
- Xử lý thủ công, khó truy vết
- Chặn nhầm khách thật
3 Mục tiêu:
- Bắt ≥ 80% lạm dụng đã biết
- Chặn nhầm khách thường ≤ 2%
- 100% quyết định có lý do
- ≥ 90% kẻ né khóa bị khóa
4 Ràng buộc:
- Không có dữ liệu thật
- Một người, hai tháng
- Quyết định tức thời tại thanh toán
- Bảo vệ dữ liệu cá nhân
5 Giải pháp:
- 18 luật có phiên bản, sửa không cần triển khai lại
- Điểm tin cậy tài khoản
- Khóa theo bậc, truy vết tài khoản liên kết
- Case, khiếu nại, nhật ký kiểm toán
6 Đánh giá:
- Mô phỏng tách tập phát triển và kiểm thử
- Chặn nhầm khách thường 0%
- Kẻ né khóa bị khóa 14/14
- F1 cao hơn luật thủ công
7 Giá trị:
- Giảm 51% mã bị gom so với không kiểm soát
- Khách quen không bị chặn nhầm
- Mọi quyết định truy vết được
- Mở rộng sang chính sách mới
Mỗi thẻ có biểu tượng phẳng đơn giản, không logo thương hiệu thật, không ảnh người thật, không thêm số liệu ngoài danh sách trên.
```
