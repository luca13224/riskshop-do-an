---
name: risk-rule
description: Thêm, sửa hoặc review một luật rủi ro hay ma trận quyết định của Risk Engine. Dùng khi Luca muốn thêm luật mới, đổi ngưỡng hoặc điểm, thêm đặc trưng, hoặc khi kết quả chấm điểm trông không đúng.
---

# Làm việc với luật rủi ro

Nguồn sự thật: `docs/RULES_V0.md` (sau này là các phiên bản tiếp theo). Code chỉ định nghĩa **loại luật**; luật cụ thể là **dữ liệu có phiên bản** trong CSDL.

## Thêm hoặc sửa một luật, theo thứ tự
1. **Nghiệp vụ trước:** luật bắt hành vi gì, thuộc chính sách nào (voucher/COD), chạy ở context nào (`voucher_apply`, `payment_options`, `place_order`).
2. **Hard negative:** ai là người hợp lệ có thể bị luật này bắt nhầm? Giảm thiểu bằng cách nào? **Không có câu trả lời thì chưa thêm luật.**
3. **Đặc trưng:** dùng đặc trưng có sẵn, hay cần thêm đặc trưng mới? Đặc trưng mới phải chỉ dùng dữ liệu **có trước** thời điểm đánh giá, và cần index phù hợp (skill `db-design`).
4. **Độ mạnh và điểm:** chọn Mạnh, Trung bình hay Yếu. Chỉ luật Mạnh mới được góp vào điều kiện REVIEW/BLOCK. Ghi lý do chọn số điểm.
5. **Tính thử** trên các nhân vật trong bảng mục 5 của `RULES_V0.md`: kết quả demo có còn đúng không? Cập nhật bảng.
6. **Unit test** theo mục 7 của `RULES_V0.md`: dưới ngưỡng, đúng ngưỡng, bậc cao, hard negative, context không áp dụng.
7. **Phiên bản:** sửa luật nghĩa là tạo phiên bản mới, không ghi đè phiên bản cũ. Thay đổi lớn thì ghi ADR (skill `adr`).

## Không được làm
- Tinh chỉnh ngưỡng dựa trên **tập test** (chỉ dùng tập dev).
- Để `reason_codes` hay tên luật lộ ra thông điệp gửi khách.
- Thêm luật chặn chỉ dựa vào IP hoặc chỉ dựa vào `device_id`.

## Khi kết quả chấm điểm trông sai
Lấy `features_snapshot` và danh sách luật khớp của quyết định đó, tính tay lại từng luật, so với ma trận quyết định. Sai ở đặc trưng (dữ liệu hoặc truy vấn), ở luật (điều kiện, tham số) hay ở ma trận?
