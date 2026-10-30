import {
  Headphones,
  Keyboard,
  Laptop,
  Monitor,
  Package,
  Smartphone,
  Watch,
  type LucideIcon,
} from "lucide-react"

import type { CategoryCode } from "@/lib/api/catalog"
import { cn } from "@/lib/utils"

// Ảnh minh họa tự vẽ theo danh mục: demo chạy offline, không phụ thuộc ảnh bên ngoài hay bản quyền ảnh.
const STYLES: Record<CategoryCode, { icon: LucideIcon; bg: string }> = {
  audio: { icon: Headphones, bg: "from-violet-500/25 to-fuchsia-500/10" },
  laptop: { icon: Laptop, bg: "from-sky-500/25 to-cyan-500/10" },
  monitor: { icon: Monitor, bg: "from-cyan-500/25 to-teal-500/10" },
  gear: { icon: Keyboard, bg: "from-amber-500/25 to-orange-500/10" },
  phone: { icon: Smartphone, bg: "from-rose-500/25 to-pink-500/10" },
  smart: { icon: Watch, bg: "from-emerald-500/25 to-lime-500/10" },
}

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
        className={cn("aspect-square w-full object-cover", className)}
      />
    )
  }
  const style = STYLES[category] ?? { icon: Package, bg: "from-muted to-muted" }
  const Icon = style.icon
  return (
    <div
      role="img"
      aria-label={name}
      className={cn(
        "flex aspect-square w-full items-center justify-center bg-gradient-to-br",
        style.bg,
        className
      )}
    >
      <Icon
        className={cn("size-14 text-foreground/70", iconClassName)}
        strokeWidth={1.25}
        aria-hidden
      />
    </div>
  )
}
