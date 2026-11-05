import { Info } from "lucide-react"
import { useState } from "react"

import { Skeleton } from "@/components/ui/skeleton"
import { Panel, RiskAnalytics } from "@/console/components/RiskAnalytics"
import { useDashboard } from "@/lib/api/dashboard"
import { useKpi, type Kpi } from "@/lib/api/reports"
import { formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"

// Trang Báo cáo, bản tinh gọn (2026-11-06): 5 khối, đọc từ trên xuống
//   1) Tác động nghiệp vụ  2) Xu hướng can thiệp + phân bố điểm  3) Hiệu quả từng luật  4) Vận hành + giả định
const RANGES = [1, 7, 30]

export function ReportsPage() {
  const [days, setDays] = useState(7)
  const kpi = useKpi(days)
  const dash = useDashboard(days)

  return (
    <div className="mx-auto grid max-w-[1400px] gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Báo cáo</h1>
          <p className="mt-1 text-sm text-muted-foreground">Hệ thống kiểm soát rủi ro hiệu quả tới đâu trong kỳ đã chọn.</p>
        </div>
        <div className="inline-flex rounded-lg border bg-muted/40 p-0.5 text-xs" role="group" aria-label="Khoảng thời gian">
          {RANGES.map((d) => (
            <button
              key={d}
              type="button"
              aria-pressed={days === d}
              onClick={() => setDays(d)}
              className={cn(
                "rounded-md px-3 py-1.5 transition-colors",
                days === d ? "bg-primary/20 text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {d === 1 ? "24 giờ" : `${d} ngày`}
            </button>
          ))}
        </div>
      </header>

      {kpi.isPending ? (
        <Skeleton className="h-40 w-full rounded-2xl" />
      ) : kpi.isError ? (
        <p className="text-destructive">{kpi.error.message}</p>
      ) : (
        <Impact k={kpi.data} />
      )}

      {dash.data ? <RiskAnalytics data={dash.data} /> : <Skeleton className="h-80 w-full rounded-2xl" />}

      {kpi.data && (
        <>
          <RuleTable k={kpi.data} />
          <Operations k={kpi.data} />
        </>
      )}
    </div>
  )
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="panel p-4 sm:p-5">
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</p>
      <p className="mt-2 text-2xl font-semibold tabular-nums">{value}</p>
      {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}

// ---------- 1) Tác động nghiệp vụ ----------
function Impact({ k }: { k: Kpi }) {
  return (
    <section className="grid gap-3" aria-label="Tác động nghiệp vụ (ước tính)">
      <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
        <Stat
          label="Ưu đãi giữ lại"
          value={formatVND(k.impact.voucher_saved_vnd)}
          hint={`${k.impact.voucher_blocked_accounts} tài khoản bị gỡ mã`}
        />
        <Stat
          label="Chi phí COD tránh được"
          value={formatVND(k.impact.cod_cost_avoided_vnd)}
          hint={`${k.impact.cod_restricted_customers} khách chuyển trả trước · ${k.impact.orders_rejected_after_review} đơn bị từ chối`}
        />
        <Stat label="Đơn giữ chờ xác minh" value={String(k.impact.orders_held)} />
        <Stat
          label="Khách hợp lệ bị giữ nhầm"
          value={String(k.impact.legit_customers_held_by_mistake)}
          hint="Case kết luận không vi phạm"
        />
      </div>
    </section>
  )
}

// ---------- 3) Hiệu quả từng luật (gộp "luật khớp nhiều nhất" cũ vào đây) ----------
function RuleTable({ k }: { k: Kpi }) {
  const rules = [...k.rules].sort((a, b) => b.hits - a.hits)
  const maxHits = Math.max(1, ...rules.map((r) => r.hits))
  return (
    <Panel
      title="Hiệu quả từng luật"
      subtitle="Số lần khớp trong kỳ; tỷ lệ chính xác = case xác nhận lạm dụng / case đã kết luận"
      className="viz"
    >
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-muted-foreground">
            <tr>
              <th className="py-2 pr-3 font-medium">Luật</th>
              <th className="py-2 pr-3 font-medium">Số lần khớp</th>
              <th className="hidden py-2 pr-3 text-right font-medium sm:table-cell">Lạm dụng / Không vi phạm</th>
              <th className="py-2 text-right font-medium">Chính xác</th>
            </tr>
          </thead>
          <tbody>
            {rules.map((r) => (
              <tr key={r.code} className="border-t" title={r.code}>
                <td className="py-2 pr-3">{r.name}</td>
                <td className="w-1/3 py-2 pr-3">
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted" aria-hidden>
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${(r.hits / maxHits) * 100}%`, background: "var(--series-1)" }}
                      />
                    </div>
                    <span className="w-10 text-right tabular-nums">{r.hits}</span>
                  </div>
                </td>
                <td className="hidden py-2 pr-3 text-right tabular-nums sm:table-cell">
                  {r.cases_confirmed} / {r.cases_cleared}
                </td>
                <td className="py-2 text-right tabular-nums">
                  {r.precision === null ? (
                    <span className="text-xs whitespace-nowrap text-muted-foreground" title="Chưa có case nào kết luận">—</span>
                  ) : (
                    `${Math.round(r.precision * 100)}%`
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  )
}

// ---------- 4) Vận hành + giả định ----------
const ms = (v: number | null) => (v === null ? "—" : `${v.toLocaleString("vi-VN")} ms`)

function Operations({ k }: { k: Kpi }) {
  return (
    <Panel title="Vận hành" subtitle="Đo ở server trên máy phát triển, chưa phải đo tải">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Chấm điểm p95" value={ms(k.latency_ms.p95)} hint={`p50 ${ms(k.latency_ms.p50)} · ${k.latency_ms.samples} lượt`} />
        <Stat label="Lỗi Risk Engine" value={String(k.decisions.engine_errors)} hint="đã dùng phương án dự phòng" />
        <Stat
          label="Case chờ / đang xử lý"
          value={`${k.cases.by_status.OPEN} / ${k.cases.by_status.IN_REVIEW}`}
        />
        <Stat
          label="Xử lý case trung bình"
          value={k.cases.avg_resolve_minutes === null ? "—" : `${k.cases.avg_resolve_minutes} phút`}
          hint={`${k.cases.by_status.CONFIRMED_ABUSE} lạm dụng · ${k.cases.by_status.CLEARED} không vi phạm`}
        />
      </div>
      <div className="flex items-start gap-2 text-xs text-muted-foreground">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        <ul className="grid list-disc gap-1 pl-4">
          {k.assumptions.map((a) => (
            <li key={a}>{a}</li>
          ))}
        </ul>
      </div>
    </Panel>
  )
}
