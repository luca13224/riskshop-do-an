import { ACTION_LABELS, type RiskDecision } from "@/lib/api/risk"
import { cn } from "@/lib/utils"

const STRENGTH_LABELS = {
  strong: "Mạnh",
  medium: "Vừa",
  weak: "Yếu",
  positive: "Tích cực",
}

// Phần "vì sao" của một quyết định: điểm theo chính sách, hành động, từng luật khớp kèm giá trị thực tế
export function DecisionDetail({ decision: d }: { decision: RiskDecision }) {
  const actions = Object.entries(d.actions).filter(([, on]) => on)
  return (
    <div className="grid gap-3">
      {d.error && (
        <p className="text-sm text-destructive">
          Risk Engine lỗi, đã dùng phương án dự phòng: {d.error}
        </p>
      )}
      <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
        <span>
          Điểm theo chính sách:{" "}
          {Object.entries(d.policy_scores)
            .map(([p, s]) => `${p === "cod" ? "COD" : "Voucher"} ${s}`)
            .join(" · ") || "không áp dụng"}
        </span>
        <span>
          Hành động:{" "}
          {actions.length
            ? actions.map(([a]) => ACTION_LABELS[a] ?? a).join(", ")
            : "không"}
        </span>
        <span className="font-mono">ID: {d.public_id}</span>
      </div>
      {d.hits.length === 0 ? (
        <p className="text-sm text-muted-foreground">Không luật nào khớp.</p>
      ) : (
        <ul className="grid gap-1.5">
          {d.hits.map((h) => (
            <li key={h.rule_code} className="flex items-start gap-3 text-sm">
              <span
                className={cn(
                  "w-12 shrink-0 text-right font-semibold tabular-nums",
                  h.points < 0
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "text-foreground"
                )}
              >
                {h.points > 0 ? `+${h.points}` : h.points}
              </span>
              <span className="flex-1">
                {h.reason_text}
                <span className="ml-2 font-mono text-xs text-muted-foreground">
                  {h.rule_code} · {STRENGTH_LABELS[h.strength]}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
