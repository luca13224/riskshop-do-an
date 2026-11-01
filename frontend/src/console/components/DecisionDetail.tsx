import {
  ACTION_LABELS,
  RESTRICTION_LABELS,
  TRUST_TIER_LABELS,
  type RiskDecision,
  type Trust,
  type TrustTier,
} from "@/lib/api/risk"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const STRENGTH_LABELS = {
  strong: "Mạnh",
  medium: "Vừa",
  weak: "Yếu",
  positive: "Tích cực",
}

// Màu theo bậc dùng bảng trạng thái .viz (index.css); luôn kèm nhãn chữ, không chỉ dựa vào màu
const TIER_COLOR: Record<TrustTier, string> = {
  normal: "var(--st-good)",
  watch: "var(--st-warning)",
  restricted: "var(--st-serious)",
  review: "var(--st-critical)",
  critical: "var(--st-critical)",
}

// Lớp 1: điểm tin cậy tài khoản lúc quyết định + "sổ trừ điểm" (luật nào trừ bao nhiêu)
function TrustPanel({ trust }: { trust: Trust }) {
  const pct = Math.max(0, Math.min(100, trust.score))
  return (
    <div className="viz grid gap-2 rounded-lg border p-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-xs text-muted-foreground">Điểm tin cậy tài khoản</span>
        <span className="flex items-baseline gap-2">
          <span className="text-lg font-semibold tabular-nums">{trust.score}</span>
          <span className="text-xs text-muted-foreground">/ 100</span>
          <span
            className="rounded-full px-2 py-0.5 text-xs font-medium"
            style={{ color: TIER_COLOR[trust.tier], background: `color-mix(in oklab, ${TIER_COLOR[trust.tier]} 15%, transparent)` }}
          >
            {TRUST_TIER_LABELS[trust.tier]}
          </span>
        </span>
      </div>
      <div
        className="h-1.5 overflow-hidden rounded-full bg-muted"
        role="meter"
        aria-label="Điểm tin cậy"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={trust.score}
      >
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: TIER_COLOR[trust.tier] }} />
      </div>
      {trust.deductions.length > 0 && (
        <ul className="grid gap-1 text-xs">
          {trust.deductions.map((x) => (
            <li key={x.rule_code} className="flex gap-3">
              <span
                className={cn(
                  "w-10 shrink-0 text-right font-semibold tabular-nums",
                  x.points < 0 && "text-emerald-600 dark:text-emerald-400"
                )}
              >
                {x.points > 0 ? `−${x.points}` : `+${-x.points}`}
              </span>
              <span className="text-muted-foreground">{x.rule_name}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// Phần "vì sao" của một quyết định: điểm theo chính sách, hành động, từng luật khớp kèm giá trị thực tế
export function DecisionDetail({ decision: d }: { decision: RiskDecision }) {
  const actions = Object.entries(d.actions).filter(([, on]) => on)
  return (
    <div className="grid gap-3">
      {d.restriction && (
        <p className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm">
          <b>{RESTRICTION_LABELS[d.restriction.kind]}</b>{" "}
          {d.restriction.until ? `đến ${formatDateTime(d.restriction.until)} ` : ""}·{" "}
          {d.restriction.reason}
        </p>
      )}
      {d.trust && <TrustPanel trust={d.trust} />}
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
