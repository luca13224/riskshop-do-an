import {
  AlarmClock,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  CircleCheck,
  FolderOpen,
  Hourglass,
  MessageSquareWarning,
  ShieldAlert,
  ShieldCheck,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react"
import { useState, type ReactNode } from "react"
import { Link } from "react-router"

import { Skeleton } from "@/components/ui/skeleton"
import { AlertsTable } from "@/console/components/AlertsTable"
import { AnimatedNumber } from "@/console/components/AnimatedNumber"
import { ColumnChart } from "@/console/components/ColumnChart"
import { DecisionMix } from "@/console/components/DecisionMix"
import { Heatmap } from "@/console/components/Heatmap"
import { Sparkline } from "@/console/components/Sparkline"
import { useMe } from "@/lib/api/auth"
import { useDashboard, type Dashboard } from "@/lib/api/dashboard"
import { CONTEXT_LABELS, type Decision } from "@/lib/api/risk"
import { formatDateTime, formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"

// ---------------------------------------------------------------------------------------------
// Dashboard tổng quan của Risk Console, bố cục "bento" đọc từ trên xuống theo thứ tự người vận hành cần:
//   1) Hệ thống đang ổn không + việc gì cần làm trước  2) Chỉ số kinh doanh và rủi ro
//   3) Nguyên nhân: phân bố điểm, khung giờ bị tấn công, luật nào khớp  4) Hàng đợi cảnh báo để xử lý
// Mọi số liệu lấy từ backend (gồm cả dữ liệu mô phỏng từ seed và Attack Lab), không có số "trang trí".
// ---------------------------------------------------------------------------------------------
const STACK: { key: Decision; label: string; color: string }[] = [
  { key: "ALLOW", label: "Cho phép", color: "var(--st-good)" },
  {
    key: "ALLOW_WITH_RESTRICTION",
    label: "Hạn chế",
    color: "var(--st-warning)",
  },
  { key: "REVIEW", label: "Chờ duyệt", color: "var(--st-serious)" },
  { key: "BLOCK", label: "Chặn", color: "var(--st-critical)" },
]
const INTERVENTIONS = STACK.slice(1)

export function ConsoleHomePage() {
  const [days, setDays] = useState(7)
  const dash = useDashboard(days)
  const { data: me } = useMe()

  return (
    <div className="mx-auto grid max-w-[1600px] gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Tổng quan rủi ro
          </h1>
          <p className="mt-1 flex flex-wrap items-center gap-x-2 text-sm text-muted-foreground">
            {me && <span>Xin chào {me.full_name}.</span>}
            <span className="inline-flex items-center gap-1.5" role="status">
              <span className="relative flex size-2" aria-hidden>
                {dash.isFetching && (
                  <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary opacity-75 motion-reduce:animate-none" />
                )}
                <span className="relative inline-flex size-2 rounded-full bg-primary" />
              </span>
              {dash.isFetching
                ? "Đang cập nhật…"
                : dash.data
                  ? `Cập nhật ${formatDateTime(dash.data.generated_at)} · tự làm mới mỗi 30 giây`
                  : "Đang tải số liệu…"}
            </span>
          </p>
        </div>
        <Segmented
          label="Khoảng thời gian"
          value={days}
          options={[
            [7, "7 ngày"],
            [30, "30 ngày"],
          ]}
          onChange={setDays}
        />
      </div>

      {dash.isPending ? (
        <DashboardSkeleton />
      ) : dash.isError ? (
        <div className="panel p-10 text-center text-sm">
          <p className="font-medium">Không tải được số liệu.</p>
          <p className="mt-1 text-muted-foreground">{dash.error.message}</p>
        </div>
      ) : (
        <div
          className={cn(
            "grid gap-6",
            dash.isPlaceholderData && "opacity-60 transition-opacity"
          )}
        >
          <div className="grid gap-6 xl:grid-cols-12">
            <Posture data={dash.data} className="xl:col-span-8" />
            <PriorityQueue data={dash.data} className="xl:col-span-4" />
          </div>

          <Kpis data={dash.data} />

          <div className="grid gap-6 xl:grid-cols-12">
            <Panel
              className="xl:col-span-7"
              title="Phân bố điểm rủi ro"
              subtitle="Số lượt chấm điểm theo khoảng điểm, tô màu theo quyết định cuối cùng"
            >
              <ColumnChart
                data={dash.data.score_histogram}
                series={STACK}
                xLabel={(k) =>
                  k === "90" ? "90–100" : `${k}–${Number(k) + 9}`
                }
                xTitle="Khoảng điểm"
                height={230}
              />
            </Panel>
            <Panel
              className="xl:col-span-5"
              title="Khung giờ bị can thiệp"
              subtitle="Thứ × giờ (giờ Việt Nam): ô càng sáng càng nhiều lượt bị hạn chế, giữ hoặc chặn"
            >
              <Heatmap data={dash.data.heatmap} />
            </Panel>
          </div>

          <div className="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3">
            <OrdersPanel data={dash.data} />
            <Panel
              title="Can thiệp theo ngày"
              subtitle="Tỷ lệ cả kỳ và số lượt can thiệp từng ngày"
            >
              <div className="grid gap-5">
                <DecisionMix counts={sumDecisions(dash.data)} />
                <ColumnChart
                  data={dash.data.series}
                  series={INTERVENTIONS}
                  height={180}
                  emptyText="Chưa có can thiệp nào trong khoảng này"
                />
              </div>
            </Panel>
            <CausesPanel
              data={dash.data}
              className="lg:col-span-2 2xl:col-span-1"
            />
          </div>

          <Panel
            title="Hàng đợi cảnh báo"
            subtitle="Bấm một dòng để xem luật nào khớp, giá trị thực tế và hành động đã áp dụng"
            action={
              <Link
                to="/console/monitor"
                className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
              >
                Live Monitor <ArrowRight className="size-3.5" />
              </Link>
            }
          >
            <AlertsTable />
          </Panel>

          <p className="text-xs text-muted-foreground">
            Số liệu lấy trực tiếp từ hệ thống, bao gồm dữ liệu mô phỏng (seed,
            Attack Lab). Ngày giờ theo giờ Việt Nam.
          </p>
        </div>
      )}
    </div>
  )
}

// ---------- Khung thẻ dùng chung ----------
function Panel({
  title,
  subtitle,
  action,
  className,
  children,
}: {
  title: string
  subtitle?: string
  action?: ReactNode
  className?: string
  children: ReactNode
}) {
  return (
    <section className={cn("panel flex min-w-0 flex-col gap-4 p-5", className)}>
      <header className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="font-semibold">{title}</h2>
          {subtitle && (
            <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>
          )}
        </div>
        {action}
      </header>
      {children}
    </section>
  )
}

function Segmented<T extends string | number>({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: T
  options: [T, string][]
  onChange: (v: T) => void
}) {
  return (
    <div
      className="inline-flex rounded-lg border bg-muted/40 p-0.5 text-xs"
      role="group"
      aria-label={label}
    >
      {options.map(([v, text]) => (
        <button
          key={String(v)}
          type="button"
          aria-pressed={value === v}
          onClick={() => onChange(v)}
          className={cn(
            "rounded-md px-3 py-1.5 transition-colors",
            value === v
              ? "bg-primary/20 text-foreground shadow-[inset_0_0_0_1px_rgba(56,189,248,.35)]"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          {text}
        </button>
      ))}
    </div>
  )
}

// ---------- 1a) Tình trạng hệ thống + 24 giờ qua ----------
type Level = "ok" | "watch" | "alert"
const LEVELS: Record<
  Level,
  { label: string; icon: LucideIcon; tone: string; ring: string }
> = {
  ok: {
    label: "Bình thường",
    icon: ShieldCheck,
    tone: "text-[#4ade80]",
    ring: "bg-[#0ca30c]/15 ring-[#0ca30c]/40",
  },
  watch: {
    label: "Cần chú ý",
    icon: ShieldAlert,
    tone: "text-[#fbbf24]",
    ring: "bg-[#fab219]/15 ring-[#fab219]/40",
  },
  alert: {
    label: "Cảnh báo",
    icon: TriangleAlert,
    tone: "text-[#f87171]",
    ring: "bg-[#d03b3b]/15 ring-[#d03b3b]/45",
  },
}

function last24(d: Dashboard) {
  return d.hourly.reduce(
    (s, h) => ({
      total: s.total + h.ALLOW + h.ALLOW_WITH_RESTRICTION + h.REVIEW + h.BLOCK,
      intervened: s.intervened + h.ALLOW_WITH_RESTRICTION + h.REVIEW + h.BLOCK,
      block: s.block + h.BLOCK,
    }),
    { total: 0, intervened: 0, block: 0 }
  )
}

// Tình trạng tổng thể, suy ra từ dữ liệu thật: có lỗi / case quá hạn / lượt chặn -> Cảnh báo;
// tỷ lệ can thiệp 24h cao hoặc còn việc tồn -> Cần chú ý; còn lại -> Bình thường.
function posture(d: Dashboard): {
  level: Level
  headline: string
  reasons: string[]
} {
  const a = d.attention
  const h = last24(d)
  const reasons: string[] = []
  if (a.risk_errors + a.failed_jobs > 0)
    reasons.push(
      `${a.risk_errors + a.failed_jobs} lỗi hệ thống (chấm điểm hoặc việc nền)`
    )
  if (a.stale_cases > 0)
    reasons.push(`${a.stale_cases} case quá 24 giờ chưa ai nhận`)
  if (h.block > 0) reasons.push(`${h.block} lượt bị chặn trong 24 giờ qua`)
  if (reasons.length)
    return { level: "alert", headline: "Có vấn đề cần xử lý ngay", reasons }
  const rate = h.total ? h.intervened / h.total : 0
  if (rate >= 0.3)
    reasons.push(
      `Tỷ lệ can thiệp 24 giờ qua cao (${Math.round(rate * 100)}%), có thể đang có đợt lạm dụng`
    )
  const queue = a.pending_orders + a.open_cases + a.open_appeals
  if (queue > 0)
    reasons.push(`${queue} việc đang chờ: đơn bị giữ, case, khiếu nại`)
  if (reasons.length)
    return {
      level: "watch",
      headline: "Hệ thống ổn định, có việc cần theo dõi",
      reasons,
    }
  return {
    level: "ok",
    headline: "Hệ thống ổn định, không có việc tồn đọng",
    reasons: ["Không có lỗi, không có case hay khiếu nại chờ xử lý"],
  }
}

function Posture({ data, className }: { data: Dashboard; className?: string }) {
  const p = posture(data)
  const L = LEVELS[p.level]
  const h = last24(data)
  return (
    <section
      className={cn(
        "panel relative flex min-w-0 flex-col gap-5 overflow-hidden p-5",
        className
      )}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 -right-24 size-72 rounded-full bg-primary/10 blur-3xl"
      />
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <span
            className={cn(
              "flex size-11 shrink-0 items-center justify-center rounded-xl ring-1",
              L.ring
            )}
          >
            <L.icon className={cn("size-5", L.tone)} />
          </span>
          <div>
            <p
              className={cn(
                "text-xs font-medium tracking-wide uppercase",
                L.tone
              )}
            >
              Tình trạng: {L.label}
            </p>
            <h2 className="mt-0.5 text-lg font-semibold">{p.headline}</h2>
            <ul className="mt-1 grid gap-0.5 text-sm text-muted-foreground">
              {p.reasons.map((r) => (
                <li key={r}>• {r}</li>
              ))}
            </ul>
          </div>
        </div>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-right">
          <dt className="text-xs text-muted-foreground">Chấm điểm 24h</dt>
          <dt className="text-xs text-muted-foreground">Can thiệp 24h</dt>
          <dd className="text-2xl font-semibold">
            <AnimatedNumber value={h.total} />
          </dd>
          <dd className="text-2xl font-semibold text-[#fbbf24]">
            <AnimatedNumber value={h.intervened} />
          </dd>
        </dl>
      </div>
      <div className="grid gap-1">
        <p className="text-xs text-muted-foreground">
          Quyết định theo giờ, 24 giờ qua
        </p>
        <ColumnChart
          data={data.hourly}
          series={STACK}
          height={170}
          xLabel={(k) => `${k.slice(11)}h`}
          xTitle="Giờ"
          emptyText="Chưa có lượt chấm điểm nào trong 24 giờ qua"
        />
      </div>
    </section>
  )
}

// ---------- 1b) Hàng việc ưu tiên ----------
type Severity = "critical" | "serious" | "warning"
function PriorityQueue({
  data,
  className,
}: {
  data: Dashboard
  className?: string
}) {
  const a = data.attention
  const items: {
    icon: LucideIcon
    label: string
    hint: string
    value: number
    to: string
    sev: Severity
  }[] = [
    {
      icon: TriangleAlert,
      label: "Lỗi hệ thống",
      hint: `${a.failed_jobs} việc nền · ${a.risk_errors} lượt chấm điểm`,
      value: a.failed_jobs + a.risk_errors,
      to: "/console/reports",
      sev: "critical",
    },
    {
      icon: AlarmClock,
      label: "Case quá 24 giờ",
      hint: "Chưa ai nhận, nên xử lý trước",
      value: a.stale_cases,
      to: "/console/cases",
      sev: "critical",
    },
    {
      icon: Hourglass,
      label: "Đơn đang giữ",
      hint: "Khách đang chờ xác nhận",
      value: a.pending_orders,
      to: "/console/cases",
      sev: "serious",
    },
    {
      icon: MessageSquareWarning,
      label: "Khiếu nại chờ xử lý",
      hint: "Khách cho rằng bị chặn nhầm",
      value: a.open_appeals,
      to: "/console/appeals",
      sev: "serious",
    },
    {
      icon: FolderOpen,
      label: "Case chờ nhận",
      hint: `${a.in_review_cases} case đang được xử lý`,
      value: a.open_cases,
      to: "/console/cases",
      sev: "warning",
    },
  ]
  const order: Record<Severity, number> = {
    critical: 0,
    serious: 1,
    warning: 2,
  }
  const active = items
    .filter((i) => i.value > 0)
    .sort((x, y) => order[x.sev] - order[y.sev])
  const tone: Record<Severity, string> = {
    critical: "bg-[#d03b3b]",
    serious: "bg-[#ec835a]",
    warning: "bg-[#fab219]",
  }

  return (
    <Panel
      title="Việc cần làm trước"
      subtitle="Sắp xếp theo mức độ khẩn cấp"
      className={className}
    >
      {active.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 py-6 text-center text-sm text-muted-foreground">
          <CircleCheck className="size-8 text-[#4ade80]" />
          Không có gì tồn đọng
        </div>
      ) : (
        <ul className="grid gap-2">
          {active.map((i) => (
            <li key={i.label}>
              <Link
                to={i.to}
                className="group flex items-center gap-3 rounded-xl border bg-muted/30 p-3 transition-colors hover:border-primary/40 hover:bg-muted/60 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
              >
                <span
                  className={cn("h-9 w-1 shrink-0 rounded-full", tone[i.sev])}
                  aria-hidden
                />
                <i.icon className="size-4 shrink-0 text-muted-foreground" />
                <span className="min-w-0 flex-1">
                  <span className="block text-sm">{i.label}</span>
                  <span className="block truncate text-xs text-muted-foreground">
                    {i.hint}
                  </span>
                </span>
                <span className="text-xl font-semibold">
                  <AnimatedNumber value={i.value} />
                </span>
                <ArrowRight className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  )
}

// ---------- 2) Chỉ số kinh doanh + rủi ro (so với kỳ trước) ----------
function Kpis({ data }: { data: Dashboard }) {
  const c = data.current
  const p = data.previous
  const s = data.series
  const pct = (a: number, b: number) => (b > 0 ? a / b : null)
  const perDay = s.map(
    (d) => d.ALLOW + d.ALLOW_WITH_RESTRICTION + d.REVIEW + d.BLOCK
  )
  const percentFmt = (v: number) =>
    `${v.toLocaleString("vi-VN", { maximumFractionDigits: 1 })}%`
  return (
    <section aria-labelledby="chi-so" className="grid gap-3">
      <h2
        id="chi-so"
        className="text-xs font-medium tracking-wide text-muted-foreground uppercase"
      >
        {data.days} ngày qua · so với {data.days} ngày trước đó
      </h2>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi
          label="Giá trị đơn hàng (GMV)"
          value={c.gmv}
          format={(v) => formatVND(Math.round(v))}
          now={c.gmv}
          before={p.gmv}
          trend={s.map((d) => d.gmv)}
          note="Không tính đơn hủy, bị từ chối"
        />
        <Kpi
          label="Đơn hàng"
          value={c.orders}
          now={c.orders}
          before={p.orders}
          trend={s.map((d) => d.orders)}
          note={`${c.voucher_orders} đơn dùng voucher`}
        />
        <Kpi
          label="Khách hàng mới"
          value={c.new_customers}
          now={c.new_customers}
          before={p.new_customers}
        />
        <Kpi
          label="Tỷ lệ đơn COD"
          value={(pct(c.cod_orders, c.orders) ?? 0) * 100}
          format={percentFmt}
          now={pct(c.cod_orders, c.orders)}
          before={pct(p.cod_orders, p.orders)}
          neutral
          note={`${c.cod_orders} đơn thanh toán khi nhận hàng`}
        />
        <Kpi
          label="Lượt chấm điểm rủi ro"
          value={c.decisions}
          now={c.decisions}
          before={p.decisions}
          neutral
          trend={perDay}
        />
        <Kpi
          label="Tỷ lệ can thiệp"
          value={(pct(c.intervened, c.decisions) ?? 0) * 100}
          format={percentFmt}
          now={pct(c.intervened, c.decisions)}
          before={pct(p.intervened, p.decisions)}
          neutral
          trend={s.map((d, i) =>
            perDay[i] ? (perDay[i] - d.ALLOW) / perDay[i] : 0
          )}
          trendColor="var(--st-warning)"
          note={`${c.intervened} lượt hạn chế, giữ hoặc chặn`}
        />
        <Kpi
          label="Độ trễ chấm điểm (p95)"
          value={data.latency_p95_ms ?? 0}
          format={(v) =>
            data.latency_p95_ms === null
              ? "—"
              : `${v.toLocaleString("vi-VN", { maximumFractionDigits: 1 })} ms`
          }
          note="95% lượt chấm điểm nhanh hơn mức này"
        />
        <Kpi
          label="Khiếu nại chờ xử lý"
          value={data.attention.open_appeals}
          note="Khách cho rằng bị hạn chế nhầm"
        />
      </div>
    </section>
  )
}

function Kpi({
  label,
  value,
  format,
  now,
  before,
  neutral,
  note,
  trend,
  trendColor,
}: {
  label: string
  value: number
  format?: (v: number) => string
  now?: number | null
  before?: number | null
  neutral?: boolean // tăng/giảm không mang nghĩa tốt/xấu
  note?: string
  trend?: number[]
  trendColor?: string
}) {
  let delta: ReactNode = null
  if (now !== undefined && before !== undefined && now !== null) {
    if (!before) {
      delta = (
        <span className="text-muted-foreground">
          {now > 0 ? "Mới trong kỳ này" : "Chưa có dữ liệu"}
        </span>
      )
    } else {
      const change = (now - before) / before
      const up = change >= 0
      const Icon = up ? ArrowUpRight : ArrowDownRight
      delta = (
        <span
          className={cn(
            "inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 tabular-nums",
            neutral
              ? "bg-muted text-muted-foreground"
              : up
                ? "bg-[#0ca30c]/15 text-[#4ade80]"
                : "bg-[#d03b3b]/15 text-[#f87171]"
          )}
        >
          <Icon className="size-3.5" aria-hidden />
          {up ? "+" : "−"}
          {Math.abs(change * 100).toLocaleString("vi-VN", {
            maximumFractionDigits: 1,
          })}
          %
        </span>
      )
    }
  }
  return (
    <div className="panel flex flex-col p-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1.5 text-2xl font-semibold tracking-tight">
        <AnimatedNumber value={value} format={format} />
      </p>
      <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
        {delta}
        {note && <span className="text-muted-foreground">{note}</span>}
      </div>
      {trend && trend.some((v) => v > 0) && (
        <div className="mt-auto pt-3 pr-1">
          <Sparkline values={trend} color={trendColor} height={28} />
        </div>
      )}
    </div>
  )
}

// ---------- 3) Đơn hàng theo ngày (đổi Số đơn / Giá trị) ----------
function OrdersPanel({ data }: { data: Dashboard }) {
  const [metric, setMetric] = useState<"orders" | "gmv">("orders")
  return (
    <Panel
      title={
        metric === "orders"
          ? "Đơn hàng theo ngày"
          : "Giá trị đơn hàng theo ngày"
      }
      subtitle="Không tính đơn bị hủy hoặc bị từ chối"
      action={
        <Segmented
          label="Chỉ số"
          value={metric}
          options={[
            ["orders", "Số đơn"],
            ["gmv", "Giá trị"],
          ]}
          onChange={setMetric}
        />
      }
    >
      <ColumnChart
        data={data.series}
        series={[
          {
            key: metric,
            label: metric === "orders" ? "Đơn hàng" : "Giá trị",
            color: "var(--series-1)",
          },
        ]}
        format={metric === "gmv" ? formatVND : undefined}
        height={230}
      />
    </Panel>
  )
}

// ---------- 3) Nguyên nhân: luật khớp nhiều nhất + điểm kiểm soát ----------
function CausesPanel({
  data,
  className,
}: {
  data: Dashboard
  className?: string
}) {
  const maxHits = Math.max(1, ...data.top_rules.map((r) => r.hits))
  return (
    <Panel
      title="Nguyên nhân rủi ro"
      subtitle="Luật khớp nhiều nhất và điểm kiểm soát nào đang can thiệp"
      className={cn("viz", className)}
      action={
        <Link
          to="/console/rules"
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline"
        >
          Luật <ArrowRight className="size-3.5" />
        </Link>
      }
    >
      {data.top_rules.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Chưa có luật nào khớp trong kỳ.
        </p>
      ) : (
        <ul className="grid gap-3">
          {data.top_rules.map((r) => (
            <li key={r.code} title={r.code}>
              <div className="flex items-baseline justify-between gap-3 text-sm">
                <span className="min-w-0 truncate">{r.name ?? r.code}</span>
                <b className="tabular-nums">{r.hits.toLocaleString("vi-VN")}</b>
              </div>
              <div
                className="mt-1 h-1.5 overflow-hidden rounded-full bg-muted"
                aria-hidden
              >
                <div
                  className="h-full rounded-full transition-[width] duration-700"
                  style={{
                    width: `${(r.hits / maxHits) * 100}%`,
                    background: "var(--series-1)",
                  }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
      <div className="grid gap-2 border-t pt-4">
        <p className="text-xs text-muted-foreground">
          Theo điểm kiểm soát (can thiệp / tổng lượt)
        </p>
        {data.by_context.map((c) => (
          <div
            key={c.context}
            className="grid grid-cols-[7.5rem_1fr_auto] items-center gap-3 text-sm"
          >
            <span className="text-muted-foreground">
              {CONTEXT_LABELS[c.context]}
            </span>
            <div
              className="flex h-2 gap-0.5 overflow-hidden rounded-full"
              aria-hidden
            >
              {c.intervened > 0 && (
                <span
                  style={{
                    flexGrow: c.intervened,
                    background: "var(--st-warning)",
                  }}
                />
              )}
              {c.total - c.intervened > 0 && (
                <span
                  style={{
                    flexGrow: c.total - c.intervened,
                    background: "var(--st-good)",
                  }}
                />
              )}
            </div>
            <span className="text-xs tabular-nums">
              {c.intervened}/{c.total}
            </span>
          </div>
        ))}
      </div>
    </Panel>
  )
}

function sumDecisions(data: Dashboard): Record<Decision, number> {
  const total = { ALLOW: 0, ALLOW_WITH_RESTRICTION: 0, REVIEW: 0, BLOCK: 0 }
  for (const d of data.series) {
    total.ALLOW += d.ALLOW
    total.ALLOW_WITH_RESTRICTION += d.ALLOW_WITH_RESTRICTION
    total.REVIEW += d.REVIEW
    total.BLOCK += d.BLOCK
  }
  return total
}

function DashboardSkeleton() {
  return (
    <div className="grid gap-6" aria-busy="true" aria-label="Đang tải">
      <div className="grid gap-6 xl:grid-cols-12">
        <Skeleton className="h-80 rounded-2xl xl:col-span-8" />
        <Skeleton className="h-80 rounded-2xl xl:col-span-4" />
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 8 }, (_, i) => (
          <Skeleton key={i} className="h-32 rounded-2xl" />
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-12">
        <Skeleton className="h-72 rounded-2xl xl:col-span-7" />
        <Skeleton className="h-72 rounded-2xl xl:col-span-5" />
      </div>
    </div>
  )
}
