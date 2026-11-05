# Thiết kế: phát hiện cụm tài khoản theo chuỗi liên kết + chuẩn hóa địa chỉ (2026-11-06)

> Luca đã duyệt 2026-11-06 → ADR-016. Kết quả đo: TEST_PLAN mục 3m. Khác biệt khi cài đặt: SĐT và địa chỉ gộp thành một nhóm cạnh "điểm nhận hàng" (xem ADR-016).

## 1. Bài toán, nói lại cho đúng
- Mục tiêu ban đầu: kéo recall của biến thể chưa biết lên (test_v4: farm gom hàng về 2–3 điểm nhận chỉ bắt 1/40).
- Rà lại bộ mô phỏng: tài khoản của `farm_multi_drop` có máy riêng, IP riêng, SĐT riêng. Giữa các điểm nhận **không có bất kỳ mối nối nào**. Đồ thị liên kết chỉ thấy 2–3 cụm nhỏ rời nhau, đúng như luật địa chỉ R03/R11 đang thấy. **Gom cụm bằng đồ thị không cải thiện được con số này.**
- Thứ duy nhất chung giữa các điểm nhận trong mô phỏng là tên người nhận ("Khách Farm"), mã sản phẩm, phường. Đây là sản phẩm phụ của bộ sinh dữ liệu. Dùng chúng là **học thuộc mô phỏng**, không làm.
- Bộ chuẩn hóa địa chỉ hiện tại (`order/service.py: normalize_address`) đã gộp đúng các kiểu viết trong mô phỏng ("Số 5 Ngõ 12", "so 05 ngo 12", "5, Ngõ 12"). Làm mạnh hơn cũng không đổi kết quả đo hiện tại.

Bài toán đúng mà đồ thị giải được là **farm nối chuỗi**. Ví dụ A và B chung máy, B và C chung SĐT nhận hàng, C và D chung địa chỉ. Không cặp nào chung đủ nhiều để chạm ngưỡng của từng luật (R02, R03, R12), nhưng cả chuỗi là một cụm 6–10 tài khoản mới cùng gom mã người mới. Đây là cách farm thật hay làm khi xoay vòng máy, SIM và điểm nhận. Mỗi luật hiện tại chỉ nhìn **một loại** điểm chung, nên không thấy.

## 2. Phương án
| | Cách làm | Ưu | Nhược |
|---|---|---|---|
| (A) **Cụm liên thông theo chuỗi** | Đồ thị: nút là tài khoản, cạnh là chung thiết bị / SĐT nhận hàng / địa chỉ (đã chuẩn hóa) trong 30 ngày. **Không tính IP** (ADR-011). Tìm thành phần liên thông chứa tài khoản đang chấm (BFS, tối đa 60 nút). Đặc trưng mới: số tài khoản mới (< 30 ngày) trong cụm đã dùng mã người mới. | Bắt đúng kiểu farm nối chuỗi mà từng luật bỏ sót; giải thích được bằng đồ thị đã có trên Console | Gia đình đông người, ký túc xá dùng chung máy cũng thành chuỗi (hard negative); truy vấn nặng hơn |
| (B) Chỉ mở rộng chuẩn hóa địa chỉ | Thêm "ngõ / ngách / hẻm / kiệt", dạng "12/5", viết tắt "Hn", "Tp.HCM" | Rẻ (1 ngày), đặc thù Việt Nam | Một mình không đổi được con số nào trong mô phỏng hiện tại |
| (C) Dừng ở đây | Dành thời gian viết quyển báo cáo | Không rủi ro | Mất phần nâng cấp cho mức A |

**Khuyến nghị: (A), kèm (B) như phần phụ** (cạnh "chung địa chỉ" dùng địa chỉ chuẩn hóa tốt hơn).

## 3. Thiết kế (A)
- **Đặc trưng F18** `cluster_new_voucher_accounts`:
  - Thành phần liên thông chứa tài khoản hiện tại, chỉ đi qua cạnh thiết bị / SĐT / địa chỉ trong 30 ngày, tối đa 60 nút.
  - Giá trị là số tài khoản tạo < 30 ngày trong cụm đã dùng hoặc đang dùng mã người mới.
  - Lưu kèm **số loại cạnh khác nhau** trong cụm, để giải thích ("6 tài khoản nối nhau qua thiết bị → SĐT → địa chỉ").
- **Luật R18** `CLUSTER_CHAIN` (chính sách voucher, độ mạnh **vừa**: chỉ gỡ mã, không giữ hay chặn đơn, không khóa):
  - Chạy ở bước áp mã và đặt hàng.
  - F18 ≥ ngưỡng **và** cụm có ≥ 2 loại cạnh, vì cụm chỉ một loại cạnh thì R02/R03/R12 đã xử lý.
  - Ngưỡng và điểm chọn trên dev, không chỉnh theo test.
- **Hiệu năng:** BFS bằng truy vấn theo index có sẵn (`account_devices`, `addresses.norm_hash`, `addresses.phone`), giới hạn 60 nút / 2 vòng truy vấn mỗi bước. Đo lại p95 chấm điểm (mục tiêu O5 ≤ 50 ms).
- **Console:** đồ thị liên kết (`LinkGraph.tsx`) tô viền cho các tài khoản cùng cụm.
- **Chuẩn hóa địa chỉ (B):**
  - Thêm "ngách / hẻm / kiệt / ngõ", dạng "12/5" tương đương "số 5 ngõ 12".
  - Thêm "HN / Hà Nội", "TP.HCM / Hồ Chí Minh".
  - Có unit test riêng. Lưu ý: hash địa chỉ cũ không đổi (chỉ áp cho địa chỉ mới), cần ghi rõ.

## 4. Dữ liệu đo (định nghĩa TRƯỚC khi code, không chỉnh theo kết quả)
Bộ dev_v5 / test_v5 = v4 + các persona sau:
- **farm_chain** (lạm dụng, có ở dev để hiệu chỉnh): 6–9 tài khoản mới. Mỗi tài khoản chung đúng **một** thứ với tài khoản kế tiếp, xoay vòng giữa thiết bị, SĐT nhận hàng và địa chỉ. Không có thiết bị, SĐT hay địa chỉ nào dùng cho quá 2 tài khoản. Tất cả dùng mã người mới.
- **farm_chain_sparse** (biến thể **chưa biết**, chỉ ở test): như trên nhưng có 1–2 mắt xích "đứt" (tài khoản không chung gì), cụm bị tách đôi.
- **big_family_chain** (hard negative): gia đình 4–6 người dùng chung 1–2 máy, nhiều người giao về nhà bố mẹ, một vài người dùng mã người mới. Đây là người dễ bị R18 bắt nhầm nhất.
- **dorm** (hard negative): ký túc xá 5–8 sinh viên, một máy tính chung cho vài người, chung địa chỉ, SĐT riêng.

## 5. Kiểm chứng
- Recall farm_chain và farm_chain_sparse; tỷ lệ bắt nhầm big_family_chain, dorm, roommates_4g; F1 so với luật thủ công trong cùng lần chạy.
- Chạy thử R18 bằng tính năng backtest trên CSDL demo (FR-43) trước khi bật.
- p95 chấm điểm sau khi thêm BFS.
- Giới hạn cần nói trước: hiệu quả phụ thuộc giả định "farm nối chuỗi"; farm không chung bất cứ thứ gì (như `farm_multi_drop`) vẫn lọt, là giới hạn cố hữu của phát hiện dựa trên liên kết.

## 6. Ước lượng công sức
- Persona + dữ liệu: 0,5 ngày.
- F18 + R18 + test: 1 ngày.
- Chuẩn hóa địa chỉ: 0,5 ngày.
- Đo dev / test + tài liệu + ADR: 0,5 ngày.
- Console tô cụm: 0,5 ngày, có thể bỏ.
