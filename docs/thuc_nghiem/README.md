# Kết quả thực nghiệm

> Mỗi file là kết quả của **một lần chạy**, giữ nguyên để truy vết (đặc biệt: mỗi seed của tập test chỉ chạy một lần). Cách đọc và kết luận nằm ở [KIEM_THU.md](../KIEM_THU.md); file `.md` là báo cáo dễ đọc, file `.json` là số liệu đầy đủ của cùng lần chạy.

## Thư mục
| Thư mục | Nội dung | Mục trong KIEM_THU |
|---|---|---|
| `mo_phong/v1/` | Bộ dữ liệu dev / test v1, bộ luật v1 | 3 |
| `mo_phong/v2/` | Thêm farm phân tán, nhóm ở trọ 4G; bộ luật v2, v3 (điểm tin cậy), v3.1 | 3c, 3d, 3e |
| `mo_phong/v3/` | Thêm né lệnh khóa (O7); ADR-013; so với baseline | 3h, 3i, 3j |
| `mo_phong/v4/` | Thêm khách mới đặt nhiều đơn COD; ADR-014 (bùng hàng COD), ADR-015 (né khóa kiểu bot) | 3k, 3l |
| `mo_phong/v5/` | Thêm farm nối chuỗi, đại gia đình, ký túc xá; ADR-016 (R18) | 3m |
| `do_tai/` | Load test và chẩn đoán độ trễ (O5) | 3f, 3n, 3o, 3p |
| `audit/` | Kiểm tra tính giải thích được, audit (O6) | 3g |

## Cách đọc tên file
`<tập>_<phiên bản>_seed<số>_scale<hệ số>[_hậu tố]`, ví dụ `test_v4_seed10_scale1`.
- `dev`: tập để tinh chỉnh luật, chạy bao nhiêu lần cũng được. `test`: chỉ chạy sau khi đã khóa luật, mỗi seed một lần.
- Hậu tố: `_before` / `_adr0xx` / `_r18`: trước / sau một thay đổi; `_without-<LUẬT>`: tắt luật đó; `_no-trust`: tắt điểm tin cậy; `_no-control`: không kiểm soát (baseline B0); `_baseline`: kèm bảng so baseline.
- `load_test_<ngày>_<chế độ>`: `prepaid` (trả trước), `welcome` (khách mới dùng mã), `spread` (mỗi người một sản phẩm), `_w4` (4 worker).

Simulator tự ghi vào `mo_phong/v<phiên bản>/` (`backend/simulator/__main__.py`).
