import { Check, Eye, ShoppingBag } from "lucide-react"
import { useState } from "react"
import { Link } from "react-router"

import type { Product } from "@/lib/api/catalog"
import { formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"

import { ProductImage } from "./ProductImage"
import { QuickView } from "./QuickView"
import { useQuickAdd } from "./use-quick-add"

// Thẻ sản phẩm kiểu Neotek: ảnh trên nền xám nhạt, rê chuột thì hiện nút tròn,
// nút "Thêm vào giỏ" nằm trong "vết khuyết" ở góc dưới bên phải (lớp .notch trong index.css).
//
// Cả thẻ bấm được để vào trang chi tiết, nhưng KHÔNG bọc cả thẻ trong <a>: bên trong còn có <button>,
// mà HTML không cho lồng nút trong link. Thay vào đó, link ở tên sản phẩm có lớp ::after phủ kín thẻ
// ("stretched link"); các nút nằm trên lớp đó nhờ z-10.
export function ProductCard({ product }: { product: Product }) {
  const [quickView, setQuickView] = useState(false)
  const quick = useQuickAdd(product)

  return (
    <article className="group relative flex flex-col overflow-hidden rounded-3xl bg-secondary">
      <div className="relative">
        <ProductImage
          category={product.category}
          imageUrl={product.image_url}
          name={product.name}
          className="transition duration-500 group-hover:scale-[1.04]"
        />
        {quick.outOfStock && (
          <span className="absolute top-3 left-3 rounded-full bg-foreground px-2.5 py-1 text-xs font-medium text-background">
            Hết hàng
          </span>
        )}
        {/* Nút tròn: ẩn, rê chuột hoặc focus bàn phím mới hiện. Màn hình cảm ứng (không có hover) thì luôn hiện. */}
        <div className="absolute top-3 right-3 z-10 flex flex-col gap-2 opacity-0 transition duration-300 group-focus-within:translate-x-0 group-focus-within:opacity-100 group-hover:translate-x-0 group-hover:opacity-100 [@media(hover:hover)]:translate-x-2 [@media(hover:none)]:opacity-100">
          <button
            type="button"
            onClick={() => setQuickView(true)}
            aria-label={`Xem nhanh ${product.name}`}
            className="flex size-10 items-center justify-center rounded-full bg-buy text-buy-foreground shadow-sm transition hover:scale-110"
          >
            <Eye className="size-4.5" />
          </button>
        </div>
      </div>

      <div className="flex flex-1 flex-col px-4 pt-3 pb-16 sm:px-5">
        <p className="text-[11px] font-medium tracking-widest text-muted-foreground uppercase">
          {product.category_name}
        </p>
        <h3 className="mt-1 line-clamp-2 text-sm font-medium sm:text-base">
          <Link
            to={`/products/${product.slug}`}
            className="outline-none after:absolute after:inset-0 after:content-[''] focus-visible:underline"
          >
            {product.name}
          </Link>
        </h3>
      </div>

      <p className="absolute bottom-4 left-4 text-sm font-semibold sm:left-5 sm:text-base">
        {formatVND(product.price)}
      </p>

      {quick.canBuy && (
        <div className="notch z-10 pt-2 pl-2">
          <button
            type="button"
            onClick={quick.add}
            disabled={quick.outOfStock || quick.pending}
            title={quick.error ?? undefined}
            aria-label={`Thêm ${product.name} vào giỏ`}
            className={cn(
              "flex size-11 items-center justify-center rounded-full bg-buy text-buy-foreground transition hover:scale-105 disabled:opacity-40 sm:size-12",
              quick.error && "bg-destructive text-white"
            )}
          >
            {quick.added ? (
              <Check className="size-5" />
            ) : (
              <ShoppingBag className="size-5" />
            )}
          </button>
          <span className="sr-only" role="status">
            {quick.added ? "Đã thêm vào giỏ" : (quick.error ?? "")}
          </span>
        </div>
      )}

      {quickView && (
        <QuickView product={product} onClose={() => setQuickView(false)} />
      )}
    </article>
  )
}
