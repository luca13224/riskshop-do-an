# Đề xuất hướng giao diện (tư vấn, CHƯA phải quyết định)

> Ngày: 2026-10-30. Nguồn tham khảo do Luca cung cấp:
> (1) một prompt dựng landing page "Vertex Shops" (pixel contract);
> (2) video YouTube "How to Build $10K Websites in Minutes (Claude AI)". Phân tích dựa trên transcript do Luca cung cấp (mục 2).

## 1. Phân tích prompt "Vertex Shops"

### Kiến trúc
- Một khung thiết kế cố định 1172×657 px. Mọi phần tử đều định vị tuyệt đối, rồi cả khung được phóng to/thu nhỏ bằng một `transform: scale(k)`.
- Bộ "type fitter" đo độ rộng nét chữ bằng canvas, sau đó co giãn chữ (`scaleX`) cho khớp từng pixel với bản mẫu.
- Ba kiến trúc riêng cho desktop, tablet và điện thoại. Riêng điện thoại thì chuyển sang bố cục dạng cột (flow layout) thật.

**Đánh giá:** cách này hợp với landing page một màn hình, không cuộn. Nó **không hợp** với một sàn TMĐT có nhiều trang, phải cuộn, có form và nội dung động:
- Phóng to bằng `scale` làm vỡ tính năng zoom của trình duyệt.
- `scaleX` làm méo chữ.
- Định vị tuyệt đối không chịu được nội dung dài ngắn khác nhau.
- Type fitter là overengineering đối với đồ án.

### Những gì đáng học
| Thành phần | Bản chất kỹ thuật | Giá trị cho dự án |
|---|---|---|
| Design tokens | Nền gần đen `#020204`, đường viền mảnh (hairline) `rgba(255,255,255,.1)`, bo góc thống nhất | Cao. Làm Console trông "đắt" mà không tốn công |
| Nút "light bank" | Gradient nhiều điểm dừng ở chân nút, bị chính khung bo góc của nút cắt (`overflow:hidden`), kèm `::after` có mask | Cao. Làm thành một variant `glow` của Button, chỉ dùng cho 1–2 CTA chính |
| Thanh nav dạng viên thuốc kính | `backdrop-filter: blur() saturate()` | Trung bình |
| Hiệu ứng vào trang có biên đạo | Web Animations API, chạy một lần. Dùng thuộc tính riêng `translate`/`scale` để không xung đột với `transform`. Có hẹn giờ dự phòng 4 giây. Tôn trọng `prefers-reduced-motion` | Cao. Đây là bài học kỹ thuật tốt |
| Vòng carousel 3D | CSS `perspective` + `translate3d`/`rotateY`, ẩn (cull) các thẻ quay ra sau, chạy bằng `requestAnimationFrame` | Trung bình. Hợp với hero trang chủ |
| Bố cục nhiều lớp | Mockup trình duyệt đè lên carousel, tạo chiều sâu | Trung bình |

### Không dùng
- Ảnh trên CloudFront của người khác (rủi ro bản quyền, link có thể chết bất cứ lúc nào).
- Câu chữ tiếng Anh sai nghĩa ("Ships gratis", "Spend via ACH"…).
- Chép nguyên thiết kế từng pixel. Chỉ lấy nguyên lý.

## 2. Phân tích video (theo transcript)

### Hiệu ứng thật sự được làm thế nào
- Hiệu ứng "cà phê rót xuống" **không phải code CSS hay canvas**. Đó là một **video do AI tạo ra**: Higgsfield tạo khung hình đầu, rồi mô hình video (Seedance) dựng thành clip. Clip được tua theo vị trí cuộn trang (scroll-scrubbed video). Cuộn xuống thì video chạy tới, cuộn lên thì chạy lùi.
- Mấy trang khác trong video cũng dùng cùng một công thức: giọt nước hoa biến thành chai, bay qua trường ánh sáng tím, khâu chỉ xanh vào quần jean. Tất cả là "một video chủ đề + cuộn để tua".
- Quy trình của skill:
  1. Hỏi về thương hiệu, "vibe", nguồn cảm hứng, tài sản sẵn có.
  2. Chọn ý tưởng cho video cuộn.
  3. Tạo ảnh và video.
  4. Dựng trang.
  5. Người dùng xem lại một lượt, ghi các chỗ cần sửa.
  6. Sửa.
  7. Triển khai (deploy) qua Hostinger.

### Đánh giá phản biện
- Video là nội dung quảng bá: có link affiliate (Higgsfield, Hostinger), và con số "$10K" là lời quảng cáo, chưa kiểm chứng.
- Cách này hợp với **trang thương hiệu một sản phẩm** (quán cà phê, nước hoa). Không hợp với sàn nhiều sản phẩm có dữ liệu động.
- Chi phí và rủi ro:
  - Cần credit trả phí để tạo video.
  - File video nặng, ảnh hưởng tốc độ tải trên điện thoại.
  - Nội dung tạo bằng AI phải ghi rõ trong báo cáo.
  - Hội đồng có thể hỏi "phần này em tự làm hay AI làm?", trái tinh thần "không lạm dụng AI" của đồ án.
- Skill này chính là bộ "10k-websites-skill" Luca từng gửi trước đây.

### Bài học giữ lại
Ngôn ngữ hình ảnh phải chính là bản chất của sản phẩm:
- Màu sắc lấy từ sản phẩm.
- Chuyển động là ẩn dụ của sản phẩm.
- Trang kể chuyện theo nhịp cuộn (scrollytelling): mỗi đoạn cuộn là một chương.
- Thêm một bài học quy trình: hỏi rõ "vibe" trước, dựng xong thì xem lại một lượt rồi mới sửa.

### Cách mình áp dụng
- Giữ ý tưởng **cuộn để kể chuyện**, nhưng thay video AI bằng **canvas 2D do mình tự code**, tiến trình chạy theo vị trí cuộn.
- Lợi ích:
  - Không tốn credit.
  - Nhẹ.
  - Giải thích được từng dòng code trước hội đồng.
  - Có thể gắn dữ liệu thật.
- Kịch bản cuộn cho trang mở màn demo:
  1. Dòng request chảy vào.
  2. Màng lọc Risk Engine hiện ra.
  3. Một farm voucher ập tới, các hạt đỏ bị tách ra.
  4. Các hạt đỏ gom thành một case.
  5. Số liệu thực nghiệm (precision, recall) hiện lên.
  6. Nút "Vào Risk Console".
- Kỹ thuật: tính tiến trình cuộn bằng JS (`scroll` + `requestAnimationFrame`). Có thể cân nhắc CSS `animation-timeline: scroll()`, nhưng cần kiểm tra hỗ trợ trình duyệt trước khi dùng. Tôn trọng reduced motion: khi đó hiển thị ảnh tĩnh từng chương.

## 3. Áp dụng cho đồ án
"Sản phẩm" thật của đồ án là **hệ thống kiểm soát rủi ro**, không phải món hàng được bán. Vì vậy ẩn dụ đề xuất là:

> **Dòng chảy và màng lọc.** Các hạt sáng (mỗi hạt là một request: áp voucher, đặt đơn) chảy qua một màng lọc phát sáng (Risk Engine).
> Hạt hợp lệ đi tiếp với màu cyan. Hạt bị hạn chế chuyển màu hổ phách. Hạt bị giữ hoặc bị chặn chuyển đỏ và tách khỏi dòng.

Điểm mạnh: ở Live Monitor, hiệu ứng này vẽ từ **dữ liệu thật** (`risk_decisions`), không phải hoạt hình trang trí. Khi chạy Attack Lab, hội đồng sẽ thấy một "cơn mưa" hạt đỏ tách ra ngay trước mắt.

### Hai gương mặt
- **Shop (khách hàng):** giữ phong cách sáng, sạch, đáng tin như một sàn TMĐT. Giá và chữ phải dễ đọc. Chỉ mượn nút glow cho CTA chính và hiệu ứng vào trang.
- **Risk Console (nhân viên):** tối, đường viền mảnh, glow cyan tiết chế, theo kiểu Vertex.
- **Màn mở đầu demo (`/about` hoặc trang chủ Console):** hero kiểu Vertex kết hợp hiệu ứng dòng chảy và màng lọc.

## 4. Phân loại
| Mức | Việc | Ước lượng |
|---|---|---|
| MVP | Bộ token (màu, viền, bo góc); Button variant `glow`; header kính; hiệu ứng vào trang có biên đạo cho shop và Console; tôn trọng reduced motion | ~1 buổi |
| Recommended | Màn mở đầu demo kể chuyện theo cuộn (scrollytelling), dòng chảy vẽ bằng canvas 2D; Live Monitor vẽ hạt từ quyết định thật (dùng lại polling đã có), giới hạn số hạt, dừng khi tab ẩn | 1–2 buổi |
| Advanced/Optional | Carousel 3D sản phẩm trên trang chủ shop; kể chuyện theo thao tác cuộn (scroll-driven) | 1 buổi |
| Không làm | Khung cố định phóng to cho cả app; type fitter; chép pixel hoặc ảnh của người khác; video hero tạo bằng AI trả phí | — |

Công nghệ: CSS, Canvas 2D và `requestAnimationFrame`. Không cần thêm thư viện.
Cách kiểm chứng:
- Tự kiểm tra theo skill `ui-design-bar`.
- Thử ở độ rộng 375 px và 1440 px.
- Bật reduced motion để kiểm tra.
- Không có lỗi trong console.
- Hiệu ứng đạt 60 fps khi Attack Lab đang chạy.

## 5. Cần Luca chốt
1. Shop giữ tông sáng (khuyến nghị), hay đồng bộ tông tối với Console?
2. Có chấp nhận ẩn dụ "dòng chảy và màng lọc", kể theo nhịp cuộn và vẽ bằng canvas tự code (không dùng video AI), làm dấu ấn thị giác của đồ án không?
3. Nguồn ảnh sản phẩm: dùng ảnh tự chụp, ảnh có giấy phép miễn phí, hay giữ ảnh hiện tại?

## 6. Tham khảo thêm: mẫu "Neotek" (123Website, id 31771)
Nguồn: https://mau.123website.com.vn/neotek/ (đã xem trực tiếp ngày 2026-10-30).

- **Công nghệ:** WordPress, WooCommerce, Elementor, theme thương mại của 123Website. Đây là theme bán sẵn, không phải sản phẩm tự xây. Theo ADR-003 mình không dùng lại theme, chỉ học bố cục.
- **Ngôn ngữ thiết kế:**
  - Nền sáng.
  - Thẻ trắng hoặc xám nhạt, bo góc lớn.
  - Ảnh sản phẩm đã tách nền, đặt trên cùng một nền xám nhạt nên lưới sản phẩm rất đồng đều.
  - Chỉ dùng **một màu nhấn duy nhất là vàng** (nút CTA, nhãn giảm giá, icon dịch vụ). Chữ màu đen.
  - Banner lớn bo góc, dùng ảnh lifestyle.
- **Chi tiết đắt giá:** nút "Phát video" và nhãn ngày của bài viết nằm trong một "vết khuyết" cắt vào góc banner hoặc ảnh (kỹ thuật bo góc ngược, inverted radius).
- **Nhịp các khối trên trang chủ:**
  1. Hero slider.
  2. Nổi bật tuần này (carousel).
  3. Banner câu chuyện.
  4. Bán chạy.
  5. Dải cam kết dịch vụ (giao hàng, đổi trả, thanh toán, hỗ trợ).
  6. Đánh giá gắn với sản phẩm.
  7. Tin tức.
  8. Footer tối.
- **Hạn chế:**
  - Đẹp nhưng chung chung, không có dấu ấn riêng.
  - Nội dung đánh giá và tin tức là dữ liệu mẫu.

### So với shop hiện tại
- Shop hiện tại dùng nền tối. Ảnh sản phẩm chỉ là ô gradient kèm icon nên trông như bản phác thảo (wireframe).
- Danh mục đang trộn thời trang, gia dụng, thể thao, âm thanh, máy tính.
- **Khoảng cách lớn nhất không nằm ở hiệu ứng**, mà ở: ảnh sản phẩm thật và đồng bộ, một hệ thống thẻ nhất quán, một màu nhấn, và nhịp các khối trên trang chủ.

### Đề xuất cập nhật
- **MVP:**
  - Chuyển shop sang tông sáng, theo cấu trúc kiểu Neotek.
  - Danh mục chỉ còn đồ công nghệ. Giá vẫn phải giữ được các kịch bản demo (ví dụ đơn COD từ 3 triệu trở lên).
  - Ảnh sản phẩm có giấy phép rõ ràng, nền đồng bộ. Không lấy ảnh của theme Neotek.
  - Trang chủ gồm: hero, nổi bật, banner, bán chạy, dải cam kết.
- **Recommended:**
  - Dấu ấn "tín hiệu điện" chỉ đặt ở hero.
  - Vết khuyết bo góc ngược trên banner.
- **Cần chốt thêm:** màu nhấn là vàng (năng lượng, tương phản cao trên nền sáng) hay cyan điện (đồng bộ với Console)?
