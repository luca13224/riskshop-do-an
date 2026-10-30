---
name: frontend-screen
description: Chuẩn dựng một màn hình React + TypeScript + Tailwind + shadcn/ui cho Shop hoặc Risk Console của đồ án. Dùng khi tạo hoặc sửa trang, component, form, bảng dữ liệu, gọi API ở thư mục frontend/.
---

# Màn hình frontend

## Vị trí file
- Trang Shop: `frontend/src/shop/pages/`. Trang Console: `frontend/src/console/pages/`.
- Component dùng chung: `frontend/src/components/`; component shadcn: `frontend/src/components/ui/`.
- Gọi API và kiểu dữ liệu: `frontend/src/lib/api/`. Mỗi nhóm endpoint một file, export hàm gọi API **và** type TypeScript tương ứng với schema backend.

## Quy ước
- **TypeScript rõ kiểu:** props, dữ liệu API, union cho trạng thái (`"ALLOW" | "REVIEW" | …`). Tránh `any`; nếu buộc dùng thì ghi comment lý do.
- **Gọi API bằng TanStack Query:** `useQuery` để đọc, `useMutation` để ghi. Không tự viết `useEffect` + `fetch` cho dữ liệu server.
- **Form:** React Hook Form + Zod; thông báo lỗi tiếng Việt, hiện ngay dưới ô nhập.
- **Bảng ở Console:** TanStack Table, có lọc, sắp xếp, phân trang.
- **Đủ 4 trạng thái** cho mỗi khối dữ liệu: đang tải (skeleton), rỗng, lỗi, có dữ liệu.
- **Phân quyền:** ẩn nút theo vai trò cho gọn giao diện, nhưng luôn nhớ backend mới là nơi chặn thật.
- **Không lộ luật cho khách:** màn hình Shop chỉ hiện `customer_message` từ backend, không hiện `reason_codes`.
- Tuân thủ skill `ui-design-bar`: tokens, chữ tiếng Việt, khả năng truy cập (accessibility).

## Tự kiểm tra trước khi đưa Luca xem
Chạy `npm run build` (bắt lỗi TypeScript) và `npm run lint` (bắt lỗi kiểu như gọi `setState` trong `useEffect`, dùng `? :` như câu lệnh), mở trang bằng trình duyệt tích hợp, chụp màn hình ở 375 px và 1440 px, đọc console trình duyệt, bấm thử mọi nút. Báo lại những gì đã kiểm tra.

## Khi dạy Luca
Luca chưa học TypeScript. Lần đầu gặp một khái niệm (type, interface, generic, hook), giải thích ngắn bằng ví dụ ngay trong màn hình đang làm. Đề nghị Luca tự viết phần dễ (khai báo type, một component nhỏ), Claude review.
