import {
  Ban,
  CircleCheck,
  Eye,
  ShieldAlert,
  type LucideIcon,
} from "lucide-react"

import { DECISION_LABELS, type Decision } from "@/lib/api/risk"

// Thanh 100%: tỷ lệ 4 loại quyết định trong kỳ (kể cả "Cho phép", phần biểu đồ cột không vẽ).
// Màu theo bảng màu trạng thái, mỗi mục chú thích có icon + chữ + số, không chỉ dựa vào màu.
const ORDER: { key: Decision; color: string; icon: LucideIcon }[] = [
  { key: "ALLOW", color: "var(--st-good)", icon: CircleCheck },
  {
    key: "ALLOW_WITH_RESTRICTION",
    color: "var(--st-warning)",
    icon: ShieldAlert,
  },
  { key: "REVIEW", color: "var(--st-serious)", icon: Eye },
  { key: "BLOCK", color: "var(--st-critical)", icon: Ban },
]

export function DecisionMix({ counts }: { counts: Record<Decision, number> }) {
  const total = ORDER.reduce((s, o) => s + counts[o.key], 0)
  if (total === 0)
    return (
      <p className="text-sm text-muted-foreground">
        Chưa có lượt chấm điểm nào.
      </p>
    )
  const pct = (n: number) =>
    `${((n / total) * 100).toLocaleString("vi-VN", { maximumFractionDigits: 1 })}%`

  return (
    <div className="viz grid gap-3">
      {/* gap-0.5 = khe 2px giữa các đoạn; đoạn > 0 thì rộng tối thiểu 4px để vẫn thấy được */}
      <div
        className="flex h-2.5 gap-0.5 overflow-hidden rounded-full"
        aria-hidden
      >
        {ORDER.filter((o) => counts[o.key] > 0).map((o) => (
          <span
            key={o.key}
            className="h-full min-w-1"
            style={{
              flexGrow: counts[o.key],
              flexBasis: 0,
              background: o.color,
            }}
          />
        ))}
      </div>
      <ul className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-sm">
        {ORDER.map(({ key, color, icon: Icon }) => (
          <li key={key} className="flex items-center gap-1.5">
            <Icon className="size-3.5 shrink-0" style={{ color }} aria-hidden />
            <span className="text-muted-foreground">
              {DECISION_LABELS[key]}
            </span>
            <b className="ml-auto tabular-nums">
              {counts[key].toLocaleString("vi-VN")}
            </b>
            <span className="text-xs text-muted-foreground tabular-nums">
              ({pct(counts[key])})
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
