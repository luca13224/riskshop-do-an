# Bộ hướng dẫn ảnh (IMAGE BRIEF)

> Dùng cho ADR-005. Mục tiêu: 24 ảnh sản phẩm và 6 ảnh danh mục **đồng bộ như cùng một buổi chụp**.
> Ảnh có thể tạo bằng AI (ChatGPT, Gemini, Higgsfield...) hoặc lấy từ nền tảng có giấy phép rõ ràng (Unsplash, Pexels).
> Mọi ảnh phải được ghi vào **Sổ nguồn ảnh** ở cuối file. Báo cáo sẽ ghi rõ ảnh nào do AI tạo.

## 1. Ảnh sản phẩm (24 ảnh)
| Tiêu chí | Yêu cầu |
|---|---|
| Tỷ lệ | 1:1. Ảnh gốc từ 1200×1200 px trở lên |
| Nền | Xám nhạt liền mạch `#F2F2F2`, không có vật trang trí |
| Bố cục | Sản phẩm ở giữa, chiếm khoảng 70% khung hình, góc nghiêng 3/4 |
| Ánh sáng | Đèn studio mềm từ trên bên trái, bóng đổ nhẹ dưới chân sản phẩm |
| Cấm | Chữ, logo, thương hiệu thật, tay người, hình mờ (watermark) |
| Xuất file | WebP 800×800, dưới 120 KB, đặt tên theo SKU: `frontend/public/products/AU-001.webp` |

**Phần prompt chung** (dán trước mô tả từng sản phẩm, viết tiếng Anh vì các công cụ AI hiểu tốt hơn):
```
Professional e-commerce product photo, single product centered, 3/4 view, seamless light grey background #F2F2F2,
soft diffused studio lighting from top left, subtle soft shadow under the product, ultra sharp, photorealistic,
no text, no logo, no brand marks, no hands, square 1:1 composition, product fills about 70% of the frame.
Product:
```

| SKU | Tên | Mô tả sản phẩm cho prompt |
|---|---|---|
| AU-001 | Tai nghe không dây Aria | white true wireless earbuds with open charging case |
| AU-002 | Loa bluetooth Pebble Mini | small round portable bluetooth speaker, fabric mesh, sage green |
| AU-003 | Tai nghe chụp tai Studio X | over-ear noise cancelling headphones, matte black with leather cushions |
| AU-004 | Loa soundbar Cinema 300W | slim black soundbar with a separate wireless subwoofer |
| LT-001 | Laptop mỏng nhẹ Aero 14 | thin silver aluminium 14-inch laptop, half open, blank dark screen |
| LT-002 | Máy tính bảng Slate 11 | 11-inch tablet with thin bezels and a stylus beside it, space grey |
| LT-003 | Hub USB-C 7 trong 1 Dock | compact aluminium USB-C hub with several ports, short cable |
| CP-004 | Giá đỡ laptop nhôm Lift | foldable aluminium laptop stand, silver |
| CP-003 | Màn hình 27 inch ViewPro | 27-inch thin bezel monitor on adjustable stand, abstract blue wallpaper |
| MN-001 | Màn hình 24 inch ViewLite | 24-inch white monitor with slim stand, soft gradient wallpaper |
| MN-002 | Màn hình cong 34 inch UltraWide | 34-inch curved ultrawide monitor, black, landscape wallpaper |
| MN-003 | Đèn treo màn hình Halo | monitor light bar clamped on top of a monitor edge, glowing softly |
| CP-001 | Bàn phím cơ Kite 75% | compact 75% mechanical keyboard, white and grey keycaps |
| CP-002 | Chuột không dây Glide | ergonomic wireless mouse, matte graphite |
| GR-001 | Lót chuột cỡ lớn Desk XL | large rolled-out desk mat, dark grey, stitched edges |
| GR-002 | Webcam 2K Clear | small round webcam on a clip mount, black |
| PH-001 | Cáp sạc USB-C bện dù 2m | coiled braided USB-C cable, dark grey |
| PH-002 | Củ sạc nhanh GaN 65W | compact white GaN wall charger with three ports |
| PH-003 | Sạc dự phòng Volt 20.000mAh | slim power bank with small digital percentage display, black |
| PH-004 | Điện thoại Nova X | modern smartphone, back view with triple camera, deep blue |
| SP-003 | Đồng hồ thông minh Pulse | smartwatch with black sport band, watch face showing heart rate |
| SM-001 | Camera an ninh Wi-Fi Eye 2K | small white pan-tilt home security camera |
| SM-002 | Ổ cắm thông minh Plug | white smart plug with small LED indicator |
| SM-003 | Vòng đeo sức khỏe Band 4 | slim fitness band with black strap, small screen |

## 2. Ảnh danh mục cho "rạp chiếu phim" (6 ảnh)
| Tiêu chí | Yêu cầu |
|---|---|
| Tỷ lệ | 2:3 (dọc), ảnh gốc từ 1000×1500 px trở lên |
| Tông | Tối, điện ảnh, có viền sáng cyan nhẹ (rim light) để đồng bộ với banner |
| Nội dung | Ảnh không gian sống có sản phẩm của danh mục, không có chữ (chữ sẽ được phủ bằng HTML) |
| Xuất file | WebP 600×900, dưới 150 KB: `frontend/public/categories/audio.webp`... |

Phần prompt chung:
```
Cinematic dark moody lifestyle photo, vertical 2:3, subtle cyan rim light, shallow depth of field, premium tech
advertising style, no text, no logo, no brand marks. Scene:
```
| Mã | Danh mục | Cảnh |
|---|---|---|
| audio | Âm thanh | over-ear headphones resting on a vinyl record player at night |
| laptop | Laptop & máy tính bảng | open laptop on a wooden desk by a rainy window, late evening |
| monitor | Màn hình | ultrawide monitor glowing on a minimal desk setup in a dark room |
| gear | Bàn phím & chuột | mechanical keyboard and mouse close-up with soft desk lamp light |
| phone | Điện thoại & phụ kiện | smartphone charging on a stone surface with a braided cable |
| smart | Thiết bị thông minh | smartwatch on a wrist during an evening run in the city |

## 3. Kiểm tra chất lượng trước khi đưa vào web
- Nền đúng màu xám nhạt và đồng đều giữa các ảnh: đặt 4 ảnh cạnh nhau không thấy lệch tông.
- Không có chữ hay logo lạ. AI hay "vẽ" chữ vô nghĩa lên sản phẩm, gặp thì phải tạo lại.
- Sản phẩm không bị méo (bàn phím đủ phím, tai nghe đủ hai bên).
- Đúng dung lượng file. Claude sẽ chạy script nén và kiểm tra kích thước.

## 4. Sổ nguồn ảnh
Ảnh lấy từ Unsplash, đã loại ảnh Unsplash+ (trả phí). Giấy phép Unsplash License cho dùng miễn phí, kể cả thương mại, không bắt buộc ghi nguồn; vẫn ghi lại để minh bạch. Ảnh được cắt và nén WebP bằng script (kích thước theo mục 1 và 2).

Lưu ý: một số ảnh chụp sản phẩm của thương hiệu thật, ví dụ điện thoại có logo. Sản phẩm trong shop là tên tự đặt, ảnh chỉ để minh họa. Nếu sau này tạo được ảnh đồng bộ nền `#F2F2F2` theo mục 1 thì thay vào.

| File | Nguồn (tác giả, URL ảnh gốc) | Giấy phép | Ngày |
|---|---|---|---|
| `frontend/public/products/AU-001.webp` | TheRegisti, https://unsplash.com/photos/qt9_OfTaaeY | Unsplash License | 2026-10-31 |
| `frontend/public/products/AU-002.webp` | Habib Dadkhah, https://unsplash.com/photos/S0B-pmGjdVA | Unsplash License | 2026-10-31 |
| `frontend/public/products/AU-003.webp` | C D-X, https://unsplash.com/photos/PDX_a_82obo | Unsplash License | 2026-10-31 |
| `frontend/public/products/AU-004.webp` | Jonas Leupe, https://unsplash.com/photos/2RyHepsRFqE | Unsplash License | 2026-10-31 |
| `frontend/public/products/LT-001.webp` | Ales Nesetril, https://unsplash.com/photos/Im7lZjxeLhg | Unsplash License | 2026-10-31 |
| `frontend/public/products/LT-002.webp` | Kelly Sikkema, https://unsplash.com/photos/qjewkQ3JeVU | Unsplash License | 2026-10-31 |
| `frontend/public/products/LT-003.webp` | Lasse Jensen, https://unsplash.com/photos/4nVJUZEJb3s | Unsplash License | 2026-10-31 |
| `frontend/public/products/CP-004.webp` | Workperch, https://unsplash.com/photos/iTUZ7VcJI8M | Unsplash License | 2026-10-31 |
| `frontend/public/products/CP-003.webp` | Daniel Eliashevskyi, https://unsplash.com/photos/aTg26S0_OC0 | Unsplash License | 2026-10-31 |
| `frontend/public/products/MN-001.webp` | Mediamodifier, https://unsplash.com/photos/9ixBVUCo6NU | Unsplash License | 2026-10-31 |
| `frontend/public/products/MN-002.webp` | Daniel Korpai, https://unsplash.com/photos/8GDCzWrcE3M | Unsplash License | 2026-10-31 |
| `frontend/public/products/MN-003.webp` | Kirill Martynov, https://unsplash.com/photos/xZoNX2slteU | Unsplash License | 2026-10-31 |
| `frontend/public/products/CP-001.webp` | Roy Wen, https://unsplash.com/photos/XNLdEeILUqw | Unsplash License | 2026-10-31 |
| `frontend/public/products/CP-002.webp` | Oscar Ivan Esquivel Arteaga, https://unsplash.com/photos/ZtxED1cpB1E | Unsplash License | 2026-10-31 |
| `frontend/public/products/GR-001.webp` | Oakywood, https://unsplash.com/photos/Zah7GC6mNKg | Unsplash License | 2026-10-31 |
| `frontend/public/products/GR-002.webp` | Bedirhan Gül, https://unsplash.com/photos/Gq8qdtRwwJs | Unsplash License | 2026-10-31 |
| `frontend/public/products/PH-001.webp` | Mika Baumeister, https://unsplash.com/photos/RWxeE7wu1T8 | Unsplash License | 2026-10-31 |
| `frontend/public/products/PH-002.webp` | Andrey Matveev, https://unsplash.com/photos/1A_MMH9w-Sc | Unsplash License | 2026-10-31 |
| `frontend/public/products/PH-003.webp` | Andrey Matveev, https://unsplash.com/photos/7JbgHNq4h4k | Unsplash License | 2026-10-31 |
| `frontend/public/products/PH-004.webp` | kuaileqie RE, https://unsplash.com/photos/NvM9V3mLrKs | Unsplash License | 2026-10-31 |
| `frontend/public/products/SP-003.webp` | Simon Daoudi, https://unsplash.com/photos/2wFoa040m8g | Unsplash License | 2026-10-31 |
| `frontend/public/products/SM-001.webp` | Turquo Cabbit, https://unsplash.com/photos/RWo6JqzzhDU | Unsplash License | 2026-10-31 |
| `frontend/public/products/SM-002.webp` | Kelly Sikkema, https://unsplash.com/photos/fZirmwarM0E | Unsplash License | 2026-10-31 |
| `frontend/public/products/SM-003.webp` | Nikita Kostrykin, https://unsplash.com/photos/5--lSW0MiE0 | Unsplash License | 2026-10-31 |
| `frontend/public/categories/audio.webp` | Sebastian Banasiewcz, https://unsplash.com/photos/oXXc-s5nNy8 | Unsplash License | 2026-10-31 |
| `frontend/public/categories/laptop.webp` | Hans, https://unsplash.com/photos/bZD2E08iKCc | Unsplash License | 2026-10-31 |
| `frontend/public/categories/monitor.webp` | Amr Taha™, https://unsplash.com/photos/6VjuO4aw19c | Unsplash License | 2026-10-31 |
| `frontend/public/categories/gear.webp` | Jon Spectacle, https://unsplash.com/photos/-Jrmmm_sbtA | Unsplash License | 2026-10-31 |
| `frontend/public/categories/phone.webp` | Shyam Mishra, https://unsplash.com/photos/jfMT9qmubPU | Unsplash License | 2026-10-31 |
| `frontend/public/categories/smart.webp` | Daniel Korpai, https://unsplash.com/photos/hbTKIbuMmBI | Unsplash License | 2026-10-31 |
