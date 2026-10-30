import { CircleCheck, CircleX, Clock } from "lucide-react"

import { APPEAL_STATUS_LABELS, type AppealStatus } from "@/lib/api/appeals"
import { cn } from "@/lib/utils"

// Trạng thái khiếu nại: icon + chữ + màu (không chỉ dựa vào màu). Dùng chung cho Shop và Console.
export function AppealStatusBadge({ status }: { status: AppealStatus }) {
  const Icon =
    status === "ACCEPTED"
      ? CircleCheck
      : status === "REJECTED"
        ? CircleX
        : Clock
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium",
        status === "ACCEPTED" &&
          "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
        status === "REJECTED" &&
          "bg-rose-500/15 text-rose-700 dark:text-rose-300",
        status === "OPEN" &&
          "bg-amber-500/15 text-amber-800 dark:text-amber-300"
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {APPEAL_STATUS_LABELS[status]}
    </span>
  )
}
