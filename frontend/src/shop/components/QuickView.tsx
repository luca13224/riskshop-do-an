import { ArrowRight, X } from "lucide-react"
import { useEffect, useRef } from "react"
import { Link } from "react-router"

import type { Product } from "@/lib/api/catalog"
import { formatVND } from "@/lib/format"

import { AddToCart } from "./AddToCart"
import { ProductImage } from "./ProductImage"

// Xem nhanh sản phẩm trong hộp thoại, không rời trang danh sách.
// Dùng thẻ <dialog> có sẵn của trình duyệt: showModal() tự lo khóa focus bên trong, phím Esc để đóng,
// và lớp nền mờ (::backdrop). Ít code hơn tự viết modal mà vẫn đúng chuẩn trợ năng.
export function QuickView({
  product,
  onClose,
}: {
  product: Product
  onClose: () => void
}) {
  const ref = useRef<HTMLDialogElement>(null)

  // Không gọi close() khi dọn dẹp: close() bắn sự kiện "close" -> onClose -> tắt popup ngay
  // (StrictMode ở chế độ dev chạy effect hai lần). Gỡ thẻ dialog khỏi trang là nó tự đóng.
  useEffect(() => {
    const dialog = ref.current
    if (dialog && !dialog.open) dialog.showModal()
  }, [])

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      // Bấm ra vùng nền mờ (chính thẻ dialog, không phải nội dung bên trong) thì đóng
      onClick={(e) => e.target === e.currentTarget && onClose()}
      aria-label={`Xem nhanh: ${product.name}`}
      className="m-auto w-[min(56rem,calc(100%-2rem))] rounded-3xl bg-background p-0 text-foreground shadow-2xl backdrop:bg-black/50 backdrop:backdrop-blur-sm"
    >
      <div className="grid gap-6 p-5 sm:grid-cols-2 sm:p-6">
        <div className="overflow-hidden rounded-2xl bg-secondary">
          <ProductImage
            category={product.category}
            imageUrl={product.image_url}
            name={product.name}
            iconClassName="size-24"
          />
        </div>
        <div className="flex flex-col gap-3">
          <div className="flex items-start justify-between gap-3">
            <p className="text-xs font-medium tracking-widest text-muted-foreground uppercase">
              {product.category_name}
            </p>
            <button
              type="button"
              onClick={onClose}
              aria-label="Đóng"
              className="-mt-1 -mr-1 rounded-full p-1.5 hover:bg-secondary"
            >
              <X className="size-5" />
            </button>
          </div>
          <h2 className="text-2xl font-semibold tracking-tight">
            {product.name}
          </h2>
          <p className="text-2xl font-semibold">{formatVND(product.price)}</p>
          <p className="leading-relaxed text-muted-foreground">
            {product.description}
          </p>
          {product.specs.length > 0 && (
            <ul className="grid gap-1 text-sm">
              {product.specs.slice(0, 3).map(([label, value]) => (
                <li key={label}>
                  <span className="text-muted-foreground">{label}:</span>{" "}
                  {value}
                </li>
              ))}
            </ul>
          )}
          <div className="mt-auto grid gap-3 pt-2">
            <AddToCart product={product} />
            <Link
              to={`/products/${product.slug}`}
              className="inline-flex items-center gap-1 text-sm font-medium underline-offset-4 hover:underline"
            >
              Xem chi tiết sản phẩm <ArrowRight className="size-4" />
            </Link>
          </div>
        </div>
      </div>
    </dialog>
  )
}
