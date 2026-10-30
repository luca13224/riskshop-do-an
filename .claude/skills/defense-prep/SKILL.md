---
name: defense-prep
description: Luyện bảo vệ đồ án cho Luca theo kiểu hội đồng phản biện, hỏi xoáy vào một module, một quyết định hay một kết quả thực nghiệm, rồi chấm câu trả lời. Dùng khi Luca nói "luyện bảo vệ", "hỏi tôi như hội đồng", "kiểm tra tôi hiểu chưa", hoặc sau khi hoàn thành một module quan trọng.
---

# Luyện bảo vệ

1. Hỏi Luca muốn luyện phần nào (một module, một ADR, kết quả thực nghiệm, hoặc toàn bộ). Đọc code và tài liệu thật của phần đó trước khi hỏi, không hỏi chung chung.
2. Đóng vai hội đồng gồm giảng viên phản biện, chuyên gia nghiệp vụ và kỹ sư. Hỏi **từng câu một**, từ dễ đến khó:
   - "Cái này làm gì?" (hiểu chức năng)
   - "Vì sao chọn cách này mà không phải cách khác?" (dựa vào DECISIONS.md)
   - "Chuyện gì xảy ra nếu…?" (trường hợp biên, lỗi, tấn công, chặn nhầm)
   - "Em chứng minh bằng gì?" (số liệu thật trong TEST_PLAN.md, không chấp nhận số chưa đo)
   - "Hạn chế là gì?"
3. Sau mỗi câu trả lời: chấm đạt / cần bổ sung / sai, chỉ ra thiếu gì, gợi ý cách trả lời gọn trong 30–60 giây. **Không nói hộ** trước khi Luca thử trả lời.
4. Nếu câu trả lời lộ ra chỗ Luca chưa hiểu code của chính mình, ghi lại thành việc cần học hoặc cần sửa.
5. Kết thúc: tóm tắt các câu yếu nhất. Đề nghị lưu danh sách câu hỏi và gợi ý trả lời vào `docs/reviews/defense-qa.md` (hỏi Luca trước khi ghi).
