import { ChevronDown, Pause, Play } from "lucide-react"
import { Fragment, useState } from "react"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { DecisionBadge, ScoreBar } from "@/console/components/DecisionBadge"
import {
  ACTION_LABELS,
  CONTEXT_LABELS,
  useRiskDecisions,
  type Decision,
  type RiskDecision,
} from "@/lib/api/risk"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const FILTERS: { value: "ALL" | "FLAGGED"; label: string }[] = [
  { value: "ALL", label: "Tất cả" },
  { value: "FLAGGED", label: "Chỉ quyết định bị hạn chế / giữ / chặn" },
]

const STRENGTH_LABELS = {
  strong: "Mạnh",
  medium: "Vừa",
  weak: "Yếu",
  positive: "Tích cực",
}

export function LiveMonitorPage() {
  const [live, setLive] = useState(true)
  const [filter, setFilter] = useState<"ALL" | "FLAGGED">("ALL")
  const [openId, setOpenId] = useState<number | null>(null)
  const decisions = useRiskDecisions(live)

  const rows = (decisions.data ?? []).filter(
    (d) => filter === "ALL" || d.decision !== "ALLOW"
  )
  const counts = (decisions.data ?? []).reduce<Record<Decision, number>>(
    (acc, d) => ({ ...acc, [d.decision]: acc[d.decision] + 1 }),
    { ALLOW: 0, ALLOW_WITH_RESTRICTION: 0, REVIEW: 0, BLOCK: 0 }
  )

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Live Monitor
          </h1>
          <p className="text-sm text-muted-foreground">
            Mọi quyết định của Risk Engine, mới nhất ở trên. Bấm một dòng để xem
            vì sao.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setLive((v) => !v)}>
          {live ? <Pause /> : <Play />}
          {live ? "Tạm dừng" : "Tiếp tục"}
          {live && (
            <span
              className="size-2 animate-pulse rounded-full bg-emerald-500"
              aria-hidden
            />
          )}
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {(Object.keys(counts) as Decision[]).map((d) => (
          <div key={d} className="rounded-xl border p-3">
            <DecisionBadge decision={d} />
            <p className="mt-2 text-2xl font-semibold tabular-nums">
              {counts[d]}
            </p>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            aria-pressed={filter === f.value}
            onClick={() => setFilter(f.value)}
            className={cn(
              "rounded-full border px-3 py-1.5 text-sm hover:bg-muted",
              filter === f.value &&
                "border-foreground bg-foreground text-background hover:bg-foreground/90"
            )}
          >
            {f.label}
          </button>
        ))}
      </div>

      {decisions.isPending ? (
        <Skeleton className="h-48 w-full rounded-xl" />
      ) : decisions.isError ? (
        <p className="text-destructive">{decisions.error.message}</p>
      ) : rows.length === 0 ? (
        <p className="rounded-xl border p-8 text-center text-muted-foreground">
          Chưa có quyết định nào.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Thời gian</th>
                <th className="px-3 py-2 font-medium">Khách hàng</th>
                <th className="px-3 py-2 font-medium">Điểm kiểm soát</th>
                <th className="px-3 py-2 font-medium">Điểm</th>
                <th className="px-3 py-2 font-medium">Quyết định</th>
                <th className="px-3 py-2 text-right font-medium">Xử lý</th>
                <th className="w-8" />
              </tr>
            </thead>
            <tbody>
              {rows.map((d) => (
                <Fragment key={d.id}>
                  <tr
                    className={cn(
                      "animate-in cursor-pointer border-t transition-colors fade-in hover:bg-muted/40",
                      openId === d.id && "bg-muted/40"
                    )}
                    onClick={() => setOpenId(openId === d.id ? null : d.id)}
                  >
                    <td className="px-3 py-2 whitespace-nowrap tabular-nums">
                      {formatDateTime(d.created_at)}
                    </td>
                    <td className="px-3 py-2">
                      {d.user_name}
                      <span className="block text-xs text-muted-foreground">
                        {d.user_email}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      {CONTEXT_LABELS[d.context]}
                      {d.order_code && (
                        <span className="block font-mono text-xs text-muted-foreground">
                          {d.order_code}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      <ScoreBar score={d.score} />
                    </td>
                    <td className="px-3 py-2">
                      <DecisionBadge decision={d.decision} />
                    </td>
                    <td className="px-3 py-2 text-right text-xs text-muted-foreground tabular-nums">
                      {d.latency_ms.toFixed(1)} ms
                    </td>
                    <td className="px-2">
                      <ChevronDown
                        className={cn(
                          "size-4 text-muted-foreground transition-transform",
                          openId === d.id && "rotate-180"
                        )}
                        aria-hidden
                      />
                    </td>
                  </tr>
                  {openId === d.id && (
                    <tr className="bg-muted/20">
                      <td colSpan={7} className="px-4 py-3">
                        <DecisionDetail decision={d} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function DecisionDetail({ decision: d }: { decision: RiskDecision }) {
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
