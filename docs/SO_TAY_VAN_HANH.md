# Sổ tay vận hành RiskShop

> Dành cho Luca tự vận hành hệ thống khi không có Claude (tháng 12/2026 – ngày bảo vệ). Mọi lệnh đã chạy thử trên máy phát triển ngày 19/11/2026.
> Thao tác chính chỉ là **bấm đúp file `.bat` trong thư mục `scripts\`**. Muốn hiểu bên trong mỗi file làm gì: mở file `.ps1` cùng tên, mỗi bước đều có chú thích.

## 1. Hệ thống gồm 4 phần

| Phần | Làm gì | Địa chỉ | Tắt đi thì sao |
|---|---|---|---|
| MariaDB (XAMPP) | Lưu toàn bộ dữ liệu | cổng 3306 | Mọi thứ khác báo lỗi kết nối |
| Backend (FastAPI) | API, Risk Engine chấm điểm | http://localhost:8000 (tài liệu API: `/docs`) | Web báo "Không kết nối được máy chủ" |
| Worker | Việc chạy nền: mở case, chạy kịch bản Attack Lab | (không có cổng) | Quyết định vẫn chấm, nhưng **case không tự mở**, Attack Lab đứng yên |
| Frontend (React) | Giao diện Shop và Risk Console | http://localhost:5173 · http://localhost:5173/console | Không mở được trang web |

## 2. Việc hằng ngày: bật, kiểm tra, tắt

| Muốn | Bấm đúp | Ghi chú |
|---|---|---|
| Bật hệ thống | `scripts\start.bat` | Mở 3 cửa sổ: "RiskShop backend", "RiskShop worker", "RiskShop frontend". **Đừng đóng** các cửa sổ này khi đang dùng. Xong tự mở Console trên trình duyệt. Phần nào đang chạy rồi thì bỏ qua. |
| Kiểm tra mọi thứ | `scripts\check.bat` | Chỉ đọc, không sửa gì. Dòng `[LỖI]` kèm cách sửa. Hết lỗi thì in "Mọi thứ sẵn sàng". |
| Tắt hệ thống | `scripts\stop.bat` | Tắt backend, worker, frontend. MariaDB để chạy; muốn tắt hẳn thì mở `D:\xampp\xampp-control.exe` → Stop ở dòng MySQL. |

Sửa code backend xong thì chạy `stop.bat` rồi `start.bat` để nạp code mới (script bật backend không ở chế độ tự nạp lại, cho ổn định khi demo).

## 3. Chuẩn bị dữ liệu demo

**Vì sao cần:** lịch sử demo được tạo **tính lùi 14 ngày từ ngày chạy lệnh**, còn Tổng quan / Báo cáo luôn xem theo "24 giờ / 7 ngày / 30 ngày tính tới bây giờ". Khoảng một tuần sau, dữ liệu trôi ra khỏi khung và biểu đồ trống dần. `check.bat` sẽ báo khi điều này xảy ra.

**Làm:** bấm đúp `scripts\prepare_demo.bat`, gõ `CO` rồi Enter. Mất khoảng 2 phút (19/11: 1,7 phút).
- **XÓA toàn bộ dữ liệu trong CSDL demo**, tạo lại sản phẩm, mã giảm giá, 18 luật, 6 tài khoản demo, rồi sinh 14 ngày lịch sử (khoảng 300 khách, 1.300 đơn).
- Không đụng tới mã nguồn, tài liệu, kết quả thực nghiệm.

**Khi nào chạy:**
- Tối hôm trước hoặc sáng ngày bảo vệ.
- Trước mỗi buổi tập demo (vì các cảnh 5c, 5e khóa tài khoản Khang, cần đưa về trạng thái ban đầu).
- Khi `check.bat` báo "biểu đồ sẽ trống" hoặc "tài khoản đang bị khóa".

Chạy buổi sáng thì khung "24 giờ" chỉ có số của tối hôm trước (khoảng 40 lượt). Muốn khung 24 giờ đông hơn: chạy thêm vài cảnh demo (Attack Lab, cảnh 1) trước giờ bảo vệ.

## 4. Tài khoản và quyền
Mật khẩu chung **`11111111`** (chỉ là dữ liệu demo trên máy local).

| Tài khoản | Vai trò | Được làm | Không được làm |
|---|---|---|---|
| `admin1@test.com` | Admin | Mọi màn hình Console, **Attack Lab**, khóa / gỡ khóa | — |
| `admin2@test.com` | Risk Manager | Duyệt khiếu nại, sửa luật (tạo phiên bản mới), khóa / gỡ khóa, xem email / SĐT đầy đủ (phải ghi lý do), Audit Log | Attack Lab |
| `admin3@test.com` | Analyst | Xem Tổng quan, Live Monitor, Báo cáo, Tài khoản bị khóa; nhận và kết luận case; chạy thử luật | Sửa luật, duyệt khiếu nại, gỡ khóa, Audit Log, Attack Lab |
| `user1@test.com` | Khách mới (Minh) | Mua hàng bình thường, có sẵn mã NGUOIMOI | — |
| `user2@test.com` | Khách bùng COD (Khang) | Bị ẩn COD; dùng cho cảnh 5c, 5e | — |
| `user3@test.com` | Khách uy tín (Lan) | Đơn COD giá trị cao vẫn được | — |

Điểm cần nhớ khi hội đồng hỏi về phân quyền: menu ẩn theo vai trò chỉ để gọn; **chặn thật nằm ở backend** (`require_roles`), gõ thẳng đường dẫn hay gọi API trực tiếp vẫn bị từ chối (mã 403).

## 5. Vận hành Risk Console theo vai trò

**Analyst, mỗi ngày**
1. **Tổng quan**: xem 4 thẻ số (đơn hàng, bị can thiệp, việc chờ xử lý, ưu đãi giữ lại) và dải quy trình.
2. **Case** → lọc "Chờ nhận" → mở case → đọc **Bằng chứng** (luật đã khớp, giá trị thật, điểm tin cậy bị trừ vì sao) và **Mạng liên kết tài khoản**.
3. Bấm **Nhận xử lý case này** → ghi lý do (ít nhất 10 ký tự) → **Xác nhận lạm dụng** hoặc **Không vi phạm**. Mọi thao tác vào Audit Log.

**Risk Manager**
1. **Khiếu nại**: đọc lý do của khách, xem luật đã khớp → **Chấp nhận** (tự miễn trừ / gỡ khóa) hoặc **Từ chối**, viết câu trả lời cho khách.
2. **Luật rủi ro**: mở luật → sửa con số → **Chạy thử trên dữ liệu cũ** (xem bao nhiêu tài khoản bị ảnh hưởng, có khách quen không) → ghi lý do → lưu thành phiên bản mới.
3. Trong case: **Khóa vô thời hạn** / **Gỡ khóa** (bắt buộc ghi lý do); **Xem email và SĐT** (bắt buộc lý do, có audit).
4. **Tài khoản bị khóa**: xem mọi lệnh khóa (đang hiệu lực / hết hạn / đã gỡ), lọc theo loại; bấm **Gỡ khóa** ngay trên dòng → ghi lý do → **Xác nhận gỡ khóa**. Trang Tổng quan, dòng "Tài khoản đang bị khóa" bấm vào cũng tới đây.
5. **Audit Log**: kiểm tra ai đã làm gì.

**Admin**: như Risk Manager, cộng **Attack Lab** (chạy kịch bản tấn công mẫu để minh họa).

## 6. Các cảnh demo cần thao tác đặc biệt
Kịch bản đầy đủ: [KICH_BAN_DEMO.md](KICH_BAN_DEMO.md). Mở cửa sổ PowerShell, `cd D:\do_an\backend` trước khi gõ các lệnh dưới.

| Cảnh | Làm gì |
|---|---|
| 2. Farm voucher | Console (admin1) → Attack Lab → chạy kịch bản "Farm voucher" (worker phải đang chạy) |
| 5c. Cố đặt COD lặp → khóa 24 giờ | `.venv\Scripts\python scripts\demo_attack.py spam-cod user2@test.com --times 4` → mở case của Khang |
| 5d. Khiếu nại | Đăng nhập user2 → Khiếu nại → gửi; đăng nhập admin2 → Khiếu nại → Chấp nhận |
| 5e. Né lệnh khóa | admin2 mở case của Khang → Khóa vô thời hạn → `.venv\Scripts\python scripts\demo_attack.py evade` → tài khoản mới bị khóa ngay lần áp mã đầu tiên |
| 6. Sửa luật | admin2 → Luật rủi ro → R02 → sửa bậc thấp thành "≥ 2 tài khoản: +40" → Chạy thử → lưu |
| Sau khi tập | Chạy lại `scripts\prepare_demo.bat` để đưa mọi thứ về ban đầu |

## 7. Xử lý sự cố

| Hiện tượng | Nguyên nhân hay gặp | Cách sửa |
|---|---|---|
| Bấm `.bat` thấy chữ lỗi đỏ "running scripts is disabled" | Windows chặn chạy file `.ps1` trực tiếp | Luôn bấm file **`.bat`** (đã tự cho phép riêng lần chạy đó, không đổi cài đặt máy) |
| `start.bat`: "MariaDB không lên sau 60 giây" | Cổng 3306 bị chương trình khác chiếm, hoặc MariaDB tắt không sạch lần trước | Mở `D:\xampp\xampp-control.exe` → Start MySQL → bấm "Logs" xem lỗi. Máy có MySQL khác cài sẵn thì tắt nó đi |
| `start.bat`: "backend chưa trả lời" | Lỗi trong code / thiếu thư viện / `.env` sai | Xem cửa sổ "RiskShop backend": dòng cuối nói lỗi gì |
| Web báo "Không kết nối được máy chủ" | Backend tắt | `scripts\start.bat` |
| Trang web trắng / không mở được | Frontend tắt | `scripts\start.bat`; xem cửa sổ "RiskShop frontend" |
| Biểu đồ Tổng quan / Báo cáo trống, toàn số 0 | Dữ liệu demo đã cũ | `scripts\prepare_demo.bat` |
| Đăng nhập báo sai mật khẩu | Gõ sai, hoặc chưa chạy demo reset | Mật khẩu `11111111`; vẫn sai thì `prepare_demo.bat` |
| "Tài khoản đang bị khóa" khi đăng nhập user2 | Còn khóa từ lần tập cảnh 5c / 5e | Console → **Tài khoản bị khóa** → Gỡ khóa (admin2, ghi lý do), hoặc `prepare_demo.bat` |
| Case không tự mở, Attack Lab đứng ở "đang chạy" | Worker tắt | `scripts\check.bat` → `scripts\start.bat` |
| "port already in use" / cổng 8000, 5173 bận | Lần trước chưa tắt hết | `scripts\stop.bat` rồi `scripts\start.bat` |
| `npm` không nhận lệnh | Node.js chưa cài / chưa có trong PATH | Cài Node.js 24 (LTS), mở lại cửa sổ |
| Ổ C báo đầy | Cache, file tạm của các ứng dụng | Cache pip / npm đã chuyển sang `D:\_cache`; dọn bằng Disk Cleanup, xóa cache CapCut |

## 8. Kiểm tra sâu (không bắt buộc cho buổi bảo vệ)
Mở PowerShell, `cd D:\do_an\backend`:

| Lệnh | Kiểm tra gì | Kết quả gần nhất |
|---|---|---|
| `.venv\Scripts\python -m pytest -q` | 222 test tự động (chạy trên CSDL test riêng, không đụng dữ liệu demo), ~4 phút | 222 qua (19/11) |
| `.venv\Scripts\python -m ruff check .` | Import / biến thừa | Sạch |
| `.venv\Scripts\python scripts\check_links.py` | Link hỏng trong tài liệu | 0 link hỏng |
| `cd ..\frontend` rồi `npx tsc -b` | Lỗi kiểu TypeScript | Sạch |

## 9. Không nên làm trong giai đoạn trước bảo vệ
- **Không cập nhật thư viện** (`npm update`, `pip install -U`): dễ làm hỏng phần đang chạy tốt.
- **Không chạy thêm tập `test_v*`** của bộ mô phỏng: mỗi seed test chỉ chạy một lần (quy tắc chống "học thuộc", xem KIEM_THU mục 2). Muốn thử thì dùng tập `dev`.
- Sửa luật trên Console để tập cảnh 6 thì sau đó chạy `prepare_demo.bat` để về bộ luật chuẩn.
- Không commit `backend\.env`, `docs\bao-cao\` (đã bị git bỏ qua).

## 10. Checklist ngày bảo vệ
**Tối hôm trước**
- [ ] `scripts\start.bat` → `scripts\prepare_demo.bat` → `scripts\check.bat` ra "Mọi thứ sẵn sàng"
- [ ] Đi một lượt toàn bộ kịch bản demo, rồi `prepare_demo.bat` lại
- [ ] Sạc pin, tắt cập nhật Windows tự động trong ngày (Settings → Windows Update → tạm dừng 1 tuần), tắt thông báo
- [ ] Mở sẵn tab: Shop, Console (đăng nhập admin2), KICH_BAN_DEMO.md

**Sáng ngày bảo vệ (trước giờ vào 30 phút)**
- [ ] `scripts\check.bat` → không có `[LỖI]`
- [ ] Chạy Attack Lab "Farm voucher" một lần để khung "24 giờ" có số
- [ ] Phóng to trình duyệt 110–125% cho hội đồng dễ nhìn
