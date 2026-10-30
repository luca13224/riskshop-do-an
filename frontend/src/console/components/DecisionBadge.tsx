import {
  Ban,
  CircleCheck,
  Eye,
  ShieldAlert,
  type LucideIcon,
} from "lucide-react"

import { DECISION_LABELS, type Decision } from "@/lib/api/risk"
import { cn } from "@/lib/utils"

// Màu + icon + chữ: không chỉ dựa vào màu (người mù màu, khi in báo cáo vẫn đọc được)
const STYLES: Record<Decision, { icon: LucideIcon; tone: string }> = {
  ALLOW: {
    icon: CircleCheck,
    tone: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
  },
  ALLOW_WITH_RESTRICTION: {
    icon: ShieldAlert,
    tone: "bg-amber-500/15 text-amber-700 dark:text-amber-300",
  },
  REVIEW: {
    icon: Eye,
    tone: "bg-violet-500/15 text-violet-700 dark:text-violet-300",
  },
  BLOCK: { icon: Ban, tone: "bg-rose-500/15 text-rose-700 dark:text-rose-300" },
}

export function DecisionBadge({ decision }: { decision: Decision }) {
  const { icon: Icon, tone } = STYLES[decision]
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium",
        tone
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {DECISION_LABELS[decision]}
    </span>
  )
}

export function ScoreBar({ score }: { score: number }) {
  const tone =
    score >= 70
      ? "bg-rose-500"
      : score >= 40
        ? "bg-amber-500"
        : "bg-emerald-500"
  return (
    <div
      className="flex items-center gap-2"
      aria-label={`Điểm rủi ro ${score}`}
    >
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full", tone)}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="w-7 text-right text-sm font-semibold tabular-nums">
        {score}
      </span>
    </div>
  )
}
