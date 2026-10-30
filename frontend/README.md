# Frontend — RiskShop

React + Vite + TypeScript + Tailwind CSS + shadcn/ui (preset Nova, base Radix). Cách chạy cả dự án xem `README.md` ở thư mục gốc.

## Lệnh hay dùng (chạy trong thư mục `frontend/`)
| Lệnh | Làm gì |
|---|---|
| `npm run dev` | Chạy dev server tại http://localhost:5173 (tự cập nhật khi sửa code; `/api` được chuyển sang backend cổng 8000) |
| `npm run build` | Kiểm tra lỗi TypeScript và đóng gói |
| `npm run lint` | Kiểm tra code theo ESLint |
| `npx shadcn@latest add <tên>` | Thêm component shadcn vào `src/components/ui/` |

## Cấu trúc
- `src/lib/api/`: hàm gọi API và kiểu dữ liệu (TypeScript) tương ứng với backend.
- `src/components/ui/`: component shadcn (code nằm trong repo, đọc và sửa được).
- Sắp có: `src/shop/` (trang khách hàng), `src/console/` (Risk Console).

## Ghi chú
- `npm audit` báo 3 lỗ hổng mức **low** trong gói `deepmerge`, do CLI `shadcn` dùng lúc cài đặt; không chạy trên trình duyệt người dùng. Lệnh `npm audit fix --force` sẽ hạ shadcn xuống 1.0.0 nên **không dùng**. Theo dõi lại khi shadcn ra bản mới.
