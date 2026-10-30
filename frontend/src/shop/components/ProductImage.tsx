import type { CategoryCode } from "@/lib/api/catalog"
import { cn } from "@/lib/utils"

import { CategoryIcon } from "./CategoryIcon"

// Khi chưa có ảnh: vẽ icon theo danh mục trên nền xám nhạt, cùng màu nền với ảnh sản phẩm thật (#f2f2f2).
interface ProductImageProps {
  category: CategoryCode
  imageUrl: string | null
  name: string
  className?: string
  iconClassName?: string
}

export function ProductImage({
  category,
  imageUrl,
  name,
  className,
  iconClassName,
}: ProductImageProps) {
  if (imageUrl) {
    return (
      <img
        src={imageUrl}
        alt={name}
        loading="lazy"
        // Ảnh chụp thật (Unsplash), mỗi ảnh một nền khác nhau: phủ kín ô cho đồng đều
        className={cn("aspect-square w-full object-cover", className)}
      />
    )
  }
  return (
    <div
      role="img"
      aria-label={name}
      className={cn(
        "flex aspect-square w-full items-center justify-center bg-secondary",
        className
      )}
    >
      <CategoryIcon
        category={category}
        className={cn("size-16 text-foreground/25", iconClassName)}
        strokeWidth={1}
      />
    </div>
  )
}
