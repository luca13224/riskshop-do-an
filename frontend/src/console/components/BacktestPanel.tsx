import { ArrowRight, FlaskConical, Info } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { DecisionBadge } from "@/console/components/DecisionBadge"
import { CONTEXT_LABELS, useBacktest, type BacktestSide, type Rule } from "@/lib/api/risk"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const RANGES = [7, 30, 90]
const TONE = { warning: "text-[var(--st-warning)]", good: "text-[var(--st-good)]" }

// "Chạy thử trước khi bật": áp tham số đang sửa lên các quyết định cũ, cho biết ai sẽ bị ảnh hưởng.
// Chỉ đọc, không lưu gì, nên Analyst cũng dùng được.
export function BacktestPanel({
  rule,
  params,
  enabled,
}: {
  rule: Rule
  params: Record<string, unknown>
  enabled: boolean
}) {
  const [days, setDays] = useState(30)
  const run = useBacktest()
  const r = run.data
  const unchanged = JSON.stringify(params) === JSON.stringify(rule.active.params) && enabled === rule.active.enabled

  return (
    <div className="grid gap-3 rounded-lg border border-dashed p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          size="sm"
          variant="outline"
          disabled={run.isPending}
          onClick={() => run.mutate({ code: rule.code, params, enabled, days })}
        >
          <FlaskConical /> {run.isPending ? "Đang chạy thử…" : "Chạy thử trên dữ liệu cũ"}
        </Button>
        <div className="inline-flex rounded-lg border bg-muted/40 p-0.5 text-xs" role="group" aria-label="Số ngày dữ liệu">
          {RANGES.map((d) => (
            <button
              key={d}
              type="button"
              aria-pressed={days === d}
              onClick={() => setDays(d)}
              className={cn(
                "rounded-md px-2.5 py-1 transition-colors",
                days === d ? "bg-primary/20 text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {d} ngày
            </button>
          ))}
        </div>
        {unchanged && <span className="text-xs text-muted-foreground">Chưa đổi số nào: kết quả sẽ không khác.</span>}
      </div>

      {run.isError && (
        <p className="text-destructive" role="alert">
          {run.error.message}
        </p>
      )}

      {r && (
        <div className="grid gap-3" aria-live="polite">
          <p>
            Phát lại <b className="tabular-nums">{r.decisions_scanned.toLocaleString("vi-VN")}</b> lượt chấm điểm trong{" "}
            {r.days} ngày: luật khớp <b className="tabular-nums">{r.hits_old}</b>
            <ArrowRight className="mx-1 inline size-3.5" aria-label="thành" />
            <b className="tabular-nums">{r.hits_new}</b> lượt.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <Side title="Chặt hơn" tone="warning" side={r.stricter} />
            <Side title="Nới hơn" tone="good" side={r.looser} />
          </div>
          <div className="flex items-start gap-2 text-xs text-muted-foreground">
            <Info className="mt-0.5 size-3.5 shrink-0" />
            <ul className="grid list-disc gap-1 pl-4">
              {r.replay_agreement !== null && (
                <li>
                  Phát lại bằng luật hiện tại khớp {Math.round(r.replay_agreement * 100)}% quyết định thật
                  {r.replay_agreement < 1 && "; phần lệch thường do quyết định cũ dùng phiên bản luật trước đó"}.
                </li>
              )}
              {r.truncated && <li>Chỉ xét 20.000 lượt gần nhất.</li>}
              {r.limits.map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

function Side({ title, tone, side }: { title: string; tone: "warning" | "good"; side: BacktestSide }) {
  return (
    <div className="viz grid content-start gap-2 rounded-lg border bg-muted/30 p-3">
      <p className="flex items-baseline justify-between gap-2">
        <span className="font-medium">{title}</span>
        <span className={cn("text-lg font-semibold tabular-nums", side.decisions > 0 && TONE[tone])}>
          {side.decisions} lượt · {side.accounts} tài khoản
        </span>
      </p>
      {side.accounts > 0 && (
        <p className="text-xs text-muted-foreground">
          Trong đó: {side.confirmed_abuse} từng bị kết luận lạm dụng · {side.cleared} từng được kết luận không vi phạm ·{" "}
          {side.loyal} khách quen (≥ 10 đơn giao thành công)
        </p>
      )}
      {side.samples.length > 0 && (
        <ul className="grid gap-1.5 text-xs">
          {side.samples.map((s) => (
            <li key={s.public_id} className="flex flex-wrap items-center gap-x-2 gap-y-1">
              <span className="font-medium">{s.user_email}</span>
              <span className="text-muted-foreground">
                {formatDateTime(s.created_at)} · {CONTEXT_LABELS[s.context]}
              </span>
              <DecisionBadge decision={s.before} />
              <ArrowRight className="size-3" aria-label="thành" />
              <DecisionBadge decision={s.after} />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
