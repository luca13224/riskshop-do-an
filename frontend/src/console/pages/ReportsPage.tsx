import { Info } from "lucide-react"
import { useState } from "react"

import { Skeleton } from "@/components/ui/skeleton"
import { DecisionBadge } from "@/console/components/DecisionBadge"
import { CONTEXT_LABELS, type Decision, type RiskContext } from "@/lib/api/risk"
import { useKpi, type Kpi } from "@/lib/api/reports"
import { formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"

const RANGES = [1, 7, 30]

// Màu trạng thái dành riêng cho quyết định; luôn đi kèm icon + chữ (DecisionBadge), không dùng màu một mình
const BAR_TONE: Record<Decision, string> = {
  ALLOW: "bg-emerald-500",
  ALLOW_WITH_RESTRICTION: "bg-amber-500",
  REVIEW: "bg-violet-500",
  BLOCK: "bg-rose-500",
}

export function ReportsPage() {
  const [days, setDays] = useState(7)
  const kpi = useKpi(days)

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Báo cáo</h1>
          <p className="text-sm text-muted-foreground">
            Hiệu quả của hệ thống kiểm soát rủi ro trong khoảng thời gian đã
            chọn.
          </p>
        </div>
        <div className="flex gap-2" role="group" aria-label="Khoảng thời gian">
          {RANGES.map((d) => (
            <button
              key={d}
              type="button"
              aria-pressed={days === d}
              onClick={() => setDays(d)}
              className={cn(
                "rounded-full border px-3 py-1.5 text-sm hover:bg-muted",
                days === d &&
                  "border-foreground bg-foreground text-background hover:bg-foreground/90"
              )}
            >
              {d === 1 ? "24 giờ" : `${d} ngày`}
            </button>
          ))}
        </div>
      </div>

      {kpi.isPending ? (
        <Skeleton className="h-96 w-full rounded-xl" />
      ) : kpi.isError ? (
        <p className="text-destructive">{kpi.error.message}</p>
      ) : (
        <KpiContent k={kpi.data} />
      )}
    </div>
  )
}

function Stat({
  label,
  value,
  hint,
}: {
  label: string
  value: string
  hint?: string
}) {
  return (
    <div className="rounded-xl border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}

const ms = (v: number | null) =>
  v === null ? "—" : `${v.toLocaleString("vi-VN")} ms`

function KpiContent({ k }: { k: Kpi }) {
  const total = k.decisions.total || 1
  const flagged = k.decisions.total - k.decisions.by_decision.ALLOW

  return (
    <>
      <section className="grid gap-3">
        <h2 className="font-semibold">Tác động nghiệp vụ (ước tính)</h2>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Stat
            label="Giá trị voucher ngăn được"
            value={formatVND(k.impact.voucher_saved_vnd)}
            hint={`${k.impact.voucher_blocked_accounts} tài khoản bị gỡ voucher`}
          />
          <Stat
            label="Chi phí COD tránh được"
            value={formatVND(k.impact.cod_cost_avoided_vnd)}
            hint={`${k.impact.cod_restricted_customers} khách bị chuyển trả trước · ${k.impact.orders_rejected_after_review} đơn bị từ chối`}
          />
          <Stat
            label="Đơn bị giữ chờ xác minh"
            value={String(k.impact.orders_held)}
          />
          <Stat
            label="Khách hợp lệ bị giữ nhầm"
            value={String(k.impact.legit_customers_held_by_mistake)}
            hint="Case nhân viên kết luận không vi phạm"
          />
        </div>
      </section>

      <section className="grid gap-3 lg:grid-cols-2">
        <div className="grid content-start gap-3 rounded-xl border p-4">
          <h2 className="font-semibold">
            Quyết định của Risk Engine{" "}
            <span className="font-normal text-muted-foreground">
              ({k.decisions.total.toLocaleString("vi-VN")} lượt, {flagged} bị
              hạn chế/giữ/chặn)
            </span>
          </h2>
          <ul className="grid gap-3">
            {(Object.keys(k.decisions.by_decision) as Decision[]).map((d) => {
              const n = k.decisions.by_decision[d]
              const pct = Math.round((n / total) * 100)
              return (
                <li
                  key={d}
                  className="grid gap-1"
                  title={`${n} quyết định (${pct}%)`}
                >
                  <div className="flex items-center justify-between text-sm">
                    <DecisionBadge decision={d} />
                    <span className="text-muted-foreground tabular-nums">
                      {n} · {pct}%
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className={cn("h-full rounded-full", BAR_TONE[d])}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </li>
              )
            })}
          </ul>
          <p className="text-xs text-muted-foreground">
            Theo điểm kiểm soát:{" "}
            {Object.entries(k.decisions.by_context)
              .map(([c, n]) => `${CONTEXT_LABELS[c as RiskContext] ?? c} ${n}`)
              .join(" · ")}
          </p>
        </div>

        <div className="grid content-start gap-3">
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Độ trễ p50" value={ms(k.latency_ms.p50)} />
            <Stat label="Độ trễ p95" value={ms(k.latency_ms.p95)} />
            <Stat label="Độ trễ p99" value={ms(k.latency_ms.p99)} />
          </div>
          <p className="text-xs text-muted-foreground">
            Thời gian chấm điểm rủi ro đo ở server cho {k.latency_ms.samples}{" "}
            lượt; {k.decisions.engine_errors} lượt Risk Engine lỗi (đã dùng
            phương án dự phòng). Môi trường: máy phát triển, chưa phải đo tải.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <Stat
              label="Case đang chờ / đang xử lý"
              value={`${k.cases.by_status.OPEN} / ${k.cases.by_status.IN_REVIEW}`}
            />
            <Stat
              label="Thời gian xử lý case trung bình"
              value={
                k.cases.avg_resolve_minutes === null
                  ? "—"
                  : `${k.cases.avg_resolve_minutes} phút`
              }
              hint={`${k.cases.by_status.CONFIRMED_ABUSE} lạm dụng · ${k.cases.by_status.CLEARED} không vi phạm`}
            />
          </div>
        </div>
      </section>

      <section className="grid gap-3">
        <h2 className="font-semibold">Hiệu quả từng luật</h2>
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Luật</th>
                <th className="px-3 py-2 text-right font-medium">
                  Số lần khớp
                </th>
                <th className="px-3 py-2 text-right font-medium">
                  Case xác nhận lạm dụng
                </th>
                <th className="px-3 py-2 text-right font-medium">
                  Case không vi phạm
                </th>
                <th className="px-3 py-2 text-right font-medium">
                  Tỷ lệ chính xác
                </th>
              </tr>
            </thead>
            <tbody>
              {k.rules.map((r) => (
                <tr key={r.code} className="border-t">
                  <td className="px-3 py-2">
                    {r.name}
                    <span className="block font-mono text-xs text-muted-foreground">
                      {r.code}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.hits}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.cases_confirmed}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.cases_cleared}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {r.precision === null ? (
                      <span className="text-muted-foreground">
                        chưa đủ dữ liệu
                      </span>
                    ) : (
                      `${Math.round(r.precision * 100)}%`
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="flex items-start gap-2 rounded-xl border p-4 text-sm text-muted-foreground">
        <Info className="mt-0.5 size-4 shrink-0" />
        <ul className="grid list-disc gap-1 pl-4">
          {k.assumptions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      </section>
    </>
  )
}
