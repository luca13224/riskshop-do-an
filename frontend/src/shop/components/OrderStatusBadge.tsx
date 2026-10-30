import { Badge } from "@/components/ui/badge"
import { STATUS_LABELS, type OrderStatus } from "@/lib/api/order"
import { cn } from "@/lib/utils"

const TONES: Record<OrderStatus, string> = {
  PENDING_REVIEW: "bg-amber-500/15 text-amber-700 dark:text-amber-300",
  CONFIRMED: "bg-sky-500/15 text-sky-700 dark:text-sky-300",
  SHIPPING: "bg-violet-500/15 text-violet-700 dark:text-violet-300",
  DELIVERED: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
  DELIVERY_FAILED: "bg-rose-500/15 text-rose-700 dark:text-rose-300",
  CANCELLED: "bg-muted text-muted-foreground",
  REJECTED: "bg-rose-500/15 text-rose-700 dark:text-rose-300",
}

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  return (
    <Badge variant="secondary" className={cn("font-medium", TONES[status])}>
      {STATUS_LABELS[status]}
    </Badge>
  )
}
