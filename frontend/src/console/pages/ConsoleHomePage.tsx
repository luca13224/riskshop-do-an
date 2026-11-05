import { ArrowRight, CircleCheck, TriangleAlert } from "lucide-react"
import { useState, type ReactNode } from "react"
import { Link } from "react-router"

import { Skeleton } from "@/components/ui/skeleton"
import { AnimatedNumber } from "@/console/components/AnimatedNumber"
import { DecisionBadge } from "@/console/components/DecisionBadge"
import { useDashboard, type Dashboard } from "@/lib/api/dashboard"
import { CONTEXT_LABELS } from "@/lib/api/risk"
import { formatDateTime, formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"

// ---------------------------------------------------------------------------------------------
// Tổng quan Risk Console, bản tối giản (2026-11-05): 4 khối, mỗi khối trả lời đúng một câu hỏi.
//   1) 4 thẻ số: bán bao nhiêu, can thiệp bao nhiêu, còn bao nhiêu việc, giữ lại bao nhiêu ưu đãi
//   2) Dải quy trình: rủi ro đang dồn ở bước nào
//   3) Cảnh báo mới: ai vừa bị can thiệp, vì sao (một câu)
//   4) Trạng thái hệ thống: engine có khỏe không
// Biểu đồ phân tích chi tiết nằm ở trang Báo cáo (RiskAnalytics).
// ---------------------------------------------------------------------------------------------
const RANGES: [number, string][] = [
  [1, "24 giờ"],
  [7, "7 ngày"],
  [30, "30 ngày"],
]

export function ConsoleHomePage() {
  const [days, setDays] = useState(1)
  const dash = useDashboard(days)

  return (
    <div className="viz mx-auto grid max-w-[1400px] gap-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Tổng quan rủi ro</h1>
          <p className="mt-1 text-sm text-muted-foreground" role="status">
            {dash.data
              ? `Cập nhật ${formatDateTime(dash.data.generated_at)} · tự làm mới mỗi 30 giây`
              : "Đang tải số liệu…"}
          </p>
        </div>
        <div className="inline-flex rounded-lg border bg-muted/40 p-0.5 text-xs" role="group" aria-label="Khoảng thời gian">
          {RANGES.map(([v, text]) => (
            <button
              key={v}
              type="button"
              aria-pressed={days === v}
              onClick={() => setDays(v)}
              className={cn(
                "rounded-md px-3 py-1.5 transition-colors",
                days === v ? "bg-primary/20 text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {text}
            </button>
          ))}
        </div>
      </header>

      {dash.isPending ? (
        <OverviewSkeleton />
      ) : dash.isError ? (
        <div className="panel p-10 text-center text-sm">
          <p className="font-medium">Không tải được số liệu.</p>
          <p className="mt-1 text-muted-foreground">{dash.error.message}</p>
        </div>
      ) : (
        <div className={cn("grid gap-6", dash.isPlaceholderData && "opacity-60 transition-opacity")}>
          <StatCards data={dash.data} />
          <Pipeline data={dash.data} />
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
            <RecentAlerts data={dash.data} />
            <SystemStatus data={dash.data} />
          </div>
        </div>
      )}
    </div>
  )
}

// ---------- 1) 4 thẻ số ----------
function StatCards({ data }: { data: Dashboard }) {
  const c = data.current
  const a = data.attention
  const pending = a.open_cases + a.open_appeals + a.pending_orders
  const rate = c.decisions ? Math.round((c.intervened / c.decisions) * 100) : 0
  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
      <Stat label="Đơn hàng" value={c.orders} note={`${formatVND(c.gmv)} doanh thu`} />
      <Stat label="Bị can thiệp" value={c.intervened} suffix={`· ${rate}%`} note="gỡ mã, ẩn COD, giữ hoặc chặn đơn" />
      <Stat
        label="Việc chờ xử lý"
        value={pending}
        tone={pending ? "warning" : "good"}
        note={`${a.open_cases} case · ${a.open_appeals} khiếu nại · ${a.pending_orders} đơn giữ`}
        to="/console/cases"
      />
      <Stat
        label="Ưu đãi giữ lại"
        value={data.saved.voucher_vnd}
        format={formatVND}
        tone="good"
        note={`ước tính, ${data.saved.voucher_blocks} lượt gỡ mã`}
      />
    </div>
  )
}

const TONE = { good: "text-[var(--st-good)]", warning: "text-[var(--st-warning)]" }

function Stat({
  label,
  value,
  note,
  suffix,
  tone,
  format,
  to,
}: {
  label: string
  value: number
  note: string
  suffix?: string
  tone?: keyof typeof TONE
  format?: (v: number) => string
  to?: string
}) {
  const body = (
    <>
      <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">{label}</p>
      <p className={cn("mt-2 text-2xl font-semibold tabular-nums sm:text-3xl", tone && TONE[tone])}>
        <AnimatedNumber value={value} format={format} />
        {suffix && <span className="ml-1.5 text-base font-normal text-muted-foreground">{suffix}</span>}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">{note}</p>
    </>
  )
  return to ? (
    <Link to={to} className="panel block p-4 transition-colors hover:border-primary/40 sm:p-5">
      {body}
    </Link>
  ) : (
    <div className="panel p-4 sm:p-5">{body}</div>
  )
}

// ---------- 2) Dải quy trình xử lý ----------
function Pipeline({ data }: { data: Dashboard }) {
  const p = data.pipeline
  const steps: { label: string; value: number; to?: string; tone?: keyof typeof TONE }[] = [
    { label: "Đã chấm điểm", value: p.scored, to: "/console/monitor" },
    { label: "Bị gắn cờ", value: p.flagged, to: "/console/monitor", tone: p.flagged ? "warning" : undefined },
    { label: "Case mở", value: p.cases_opened, to: "/console/cases" },
    { label: "Đang xử lý", value: p.in_review, to: "/console/cases" },
    { label: "Khiếu nại", value: p.appeals, to: "/console/appeals" },
    { label: "Đã kết luận", value: p.resolved, to: "/console/cases", tone: "good" },
  ]
  return (
    <Section title="Quy trình xử lý rủi ro">
      <ol className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
        {steps.map((s, i) => (
          <li key={s.label}>
            <Link
              to={s.to ?? "#"}
              className="block rounded-xl border bg-muted/30 px-3 py-3 text-center transition-colors hover:border-primary/40"
            >
              <span className="text-xs text-muted-foreground">
                {i + 1}. {s.label}
              </span>
              <span className={cn("mt-1 block text-2xl font-semibold tabular-nums", s.tone && TONE[s.tone])}>
                {s.value.toLocaleString("vi-VN")}
              </span>
            </Link>
          </li>
        ))}
      </ol>
    </Section>
  )
}

// ---------- 3) Cảnh báo mới ----------
function RecentAlerts({ data }: { data: Dashboard }) {
  return (
    <Section
      title="Cảnh báo mới"
      action={
        <Link to="/console/monitor" className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
          Xem tất cả <ArrowRight className="size-3.5" />
        </Link>
      }
    >
      {data.recent_interventions.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted-foreground">Chưa có lượt can thiệp nào.</p>
      ) : (
        <ul className="divide-y">
          {data.recent_interventions.map((r) => (
            <li key={r.public_id} className="flex items-start justify-between gap-4 py-3">
              <div className="min-w-0">
                <p className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
                  <span className="font-medium text-foreground">{r.user_email}</span>
                  <span>{formatDateTime(r.created_at)}</span>
                  <span>· {CONTEXT_LABELS[r.context]}</span>
                  <DecisionBadge decision={r.decision} />
                </p>
                <p className="mt-1 text-sm">{r.reason}</p>
              </div>
              {r.case_code && (
                <Link
                  to={`/console/cases/${r.case_code}`}
                  className="shrink-0 text-xs text-primary hover:underline"
                >
                  Chi tiết
                </Link>
              )}
            </li>
          ))}
        </ul>
      )}
    </Section>
  )
}

// ---------- 4) Trạng thái hệ thống ----------
function SystemStatus({ data }: { data: Dashboard }) {
  const s = data.system
  const p95 = s.latency_p95_ms
  const rows: { label: string; value: string; ok: boolean; to?: string }[] = [
    { label: "Bộ luật đang bật", value: `${s.rules_enabled} luật`, ok: true, to: "/console/rules" },
    { label: "Chấm điểm p95", value: p95 == null ? "chưa có" : `${Math.round(p95)} ms`, ok: p95 == null || p95 <= 50 },
    { label: "Worker", value: s.worker_ok ? "Đang chạy" : `${s.jobs_lagging} việc bị trễ`, ok: s.worker_ok },
    { label: "Lỗi Risk Engine 24 giờ", value: String(s.engine_errors_24h), ok: s.engine_errors_24h === 0 },
    {
      label: "Tài khoản đang bị khóa",
      value: String(s.active_restrictions),
      ok: true,
      to: "/console/cases",
    },
  ]
  return (
    <Section title="Trạng thái hệ thống">
      <ul className="grid gap-2">
        {rows.map((r) => (
          <li key={r.label} className="flex items-center justify-between gap-3 rounded-lg border bg-muted/30 px-3 py-2.5 text-sm">
            <span>{r.label}</span>
            <span
              className={cn(
                "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium tabular-nums",
                r.ok ? "text-[var(--st-good)]" : "text-[var(--st-warning)]"
              )}
            >
              {r.ok ? <CircleCheck className="size-3.5" aria-hidden /> : <TriangleAlert className="size-3.5" aria-hidden />}
              {r.value}
            </span>
          </li>
        ))}
      </ul>
    </Section>
  )
}

function Section({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="panel flex min-w-0 flex-col gap-4 p-5">
      <header className="flex items-center justify-between gap-3">
        <h2 className="font-semibold">{title}</h2>
        {action}
      </header>
      {children}
    </section>
  )
}

function OverviewSkeleton() {
  return (
    <div className="grid gap-6" aria-busy="true" aria-label="Đang tải">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-32 rounded-2xl" />
        ))}
      </div>
      <Skeleton className="h-36 rounded-2xl" />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.7fr)_minmax(0,1fr)]">
        <Skeleton className="h-80 rounded-2xl" />
        <Skeleton className="h-80 rounded-2xl" />
      </div>
    </div>
  )
}
