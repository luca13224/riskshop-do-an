---
name: explain-code
description: Giải thích code, lỗi, khái niệm kỹ thuật hoặc một file cho Luca (sinh viên Gen Z, mới vào nghề) theo cách dễ hiểu. Dùng khi Luca hỏi "cái này là gì", "sao lại thế", "giải thích giúp", dán một đoạn lỗi, hoặc khi vừa viết xong code mà Luca cần hiểu để tự làm tiếp và bảo vệ trước hội đồng.
---

# Giải thích cho newbie

## Thứ tự giải thích
1. **Tóm lại là…**: một câu nói thứ này làm gì, bằng lời thường.
2. **Ví dụ đời thường** (nếu giúp hiểu nhanh hơn). Ví dụ: API giống quầy order, frontend là khách gọi món, backend là bếp, database là kho; transaction giống chuyển khoản, hoặc trừ tiền và cộng tiền cùng xong, hoặc không cái nào xảy ra.
3. **Đi qua code từ trên xuống**, mỗi khối vài dòng: dòng này làm gì, vì sao cần.
4. **Luồng chạy thực tế**: khi người dùng bấm nút X thì code nào chạy trước, chạy sau.
5. **Chỗ hay sai** và cách tự kiểm tra (chạy lệnh nào, test nào, nhìn log ở đâu).
6. **Câu hội đồng có thể hỏi** về đoạn này, kèm gợi ý trả lời 1–2 câu.

## Quy tắc giọng văn
- Giọng anh chị khóa trên: thân thiện, câu ngắn, "mình" và "bạn". Không lên lớp, không khen sáo rỗng.
- Thuật ngữ tiếng Anh giữ nguyên, nhưng lần đầu xuất hiện phải giải thích trong ngoặc bằng lời thường.
- Mỗi đoạn một ý. Không đổ một bảng dài khi một câu nói được.
- Khi giải thích lỗi: lỗi này **nghĩa là gì** trước, **sửa thế nào** sau. Chỉ cho Luca dòng nào trong thông báo lỗi là quan trọng nhất.

## Kiểm tra hiểu bài (nhẹ nhàng, không thành bài kiểm tra)
- Kết thúc bằng **một** câu hỏi nhỏ, hoặc một gợi ý "thử sửa X xem chuyện gì xảy ra", để Luca tự làm.
- Nếu Luca nói không cần hỏi lại thì bỏ bước này.
