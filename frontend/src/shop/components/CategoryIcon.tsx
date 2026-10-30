import {
  Headphones,
  Keyboard,
  Laptop,
  Monitor,
  Package,
  Smartphone,
  Watch,
} from "lucide-react"

import type { CategoryCode } from "@/lib/api/catalog"

// Icon theo danh mục. Viết thành component với switch (thay vì trả về "component" từ một hàm)
// để React không phải tạo component mới mỗi lần render.
export function CategoryIcon({
  category,
  className,
  strokeWidth,
}: {
  category: CategoryCode
  className?: string
  strokeWidth?: number
}) {
  const props = { className, strokeWidth, "aria-hidden": true as const }
  switch (category) {
    case "audio":
      return <Headphones {...props} />
    case "laptop":
      return <Laptop {...props} />
    case "monitor":
      return <Monitor {...props} />
    case "gear":
      return <Keyboard {...props} />
    case "phone":
      return <Smartphone {...props} />
    case "smart":
      return <Watch {...props} />
    default:
      return <Package {...props} />
  }
}
