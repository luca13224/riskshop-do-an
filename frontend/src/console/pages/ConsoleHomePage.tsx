import {
  AlarmClock,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  CircleCheck,
  FolderOpen,
  Hourglass,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react"
import { useState, type ReactNode } from "react"
import { Link } from "react-router"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ColumnChart } from "@/console/components/ColumnChart"
import { DecisionBadge } from "@/console/components/DecisionBadge"
import { DecisionMix } from "@/console/components/DecisionMix"
import { Sparkline } from "@/console/components/Sparkline"
import { useMe } from "@/lib/api/auth"
import { useDashboard, type Dashboard } from "@/lib/api/dashboard"
import { useHealth } from "@/lib/api/health"
import { CONTEXT_LABELS, type Decision } from "@/lib/api/risk"
import { formatDateTime, formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"

// Dashboard tổng quan của Risk Console. Trả lời 3 câu hỏi của người quản lý trên một màn hình:
//   1) Có gì cần xử lý ngay?  2) Shop đang thế nào?  3) Hệ thống rủi ro đang can thiệp gì?
// Số liệu chi tiết kèm giả định quy đổi tiền nằm ở trang Báo cáo.
export function ConsoleHomePage() {
  const [days, setDays] = useState(7)
  const dash = useDashboard(days)
  const { data: me } = useMe()

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Tổng quan</h1>
          <p className="flex flex-wrap items-center gap-x-2 text-sm text-muted-foreground">
            {me && <span>Xin chào {me.full_name}.</span>}
            {/* Chấm xanh nhấp nháy khi đang tải số liệu mới (tự làm mới mỗi 30 giây) */}
            <span className="inline-flex items-center gap-1.5" role="status">
              <span className="relative flex size-2" aria-hidden>
                {dash.isFetching && (
                  <span className="absolute inline-flex size-full animate-ping rounded-full bg-[#0ca30c] opacity-75 motion-reduce:animate-none" />
                )}
                <span className="relative inline-flex size-2 rounded-full bg-[#0ca30c]" />
              </span>
              {dash.isFetching
                ? "Đang cập nhật…"
                : dash.data
                  ? `Cập nhật lúc ${formatDateTime(dash.data.generated_at)}, tự làm mới mỗi 30 giây`
                  : "Đang tải số liệu…"}
            </span>
          </p>
        </div>
        <div
          className="inline-flex rounded-lg border p-0.5 text-sm"
          role="group"
          aria-label="Khoảng thời gian"
        >
          {[7, 30].map((d) => (
            <button
              key={d}
              type="button"
              aria-pressed={days === d}
              onClick={() => setDays(d)}
              className={cn(
                "rounded-md px-3 py-1.5 transition",
                days === d ? "bg-foreground text-background" : "hover:bg-muted"
              )}
            >
              {d} ngày
            </button>
          ))}
        </div>
      </div>

      {dash.isPending ? (
        <DashboardSkeleton />
      ) : dash.isError ? (
        <Card>
          <CardContent className="py-10 text-center text-sm">
            <p className="font-medium">Không tải được số liệu.</p>
            <p className="mt-1 text-muted-foreground">{dash.error.message}</p>
          </CardContent>
        </Card>
      ) : (
        <div
          className={cn(
            "grid gap-6",
            dash.isPlaceholderData && "opacity-60 transition-opacity"
          )}
        >
          <Attention data={dash.data} />
          <ShopKpis data={dash.data} />
          <div className="grid gap-6 xl:grid-cols-2">
            <OrdersChart data={dash.data} />
            <Card>
              <CardHeader>
                <CardTitle>Hệ thống rủi ro can thiệp theo ngày</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-6">
                <DecisionMix counts={sumDecisions(dash.data)} />
                <p className="-mb-3 text-xs text-muted-foreground">
                  Theo ngày (không vẽ lượt "Cho phép" để thấy rõ các lượt can
                  thiệp)
                </p>
                <ColumnChart
                  data={dash.data.series}
                  series={[
                    {
                      key: "ALLOW_WITH_RESTRICTION",
                      label: "Hạn chế",
                      color: "var(--st-warning)",
                    },
                    {
                      key: "REVIEW",
                      label: "Chờ duyệt",
                      color: "var(--st-serious)",
                    },
                    {
                      key: "BLOCK",
                      label: "Chặn",
                      color: "var(--st-critical)",
                    },
                  ]}
                  emptyText="Chưa có can thiệp nào trong khoảng này"
                />
              </CardContent>
            </Card>
          </div>
          <div className="grid gap-6 xl:grid-cols-2">
            <TopRules data={dash.data} />
            <RecentInterventions data={dash.data} />
          </div>
          <SystemLine data={dash.data} />
        </div>
      )}
    </div>
  )
}

// ---------- Biểu đồ đơn hàng: đổi qua lại giữa số đơn và giá trị (GMV) ----------
function OrdersChart({ data }: { data: Dashboard }) {
  const [metric, setMetric] = useState<"orders" | "gmv">("orders")
  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
        <CardTitle>
          {metric === "orders"
            ? "Đơn hàng theo ngày"
            : "Giá trị đơn hàng theo ngày"}
        </CardTitle>
        <div
          className="inline-flex rounded-lg border p-0.5 text-xs"
          role="group"
          aria-label="Chỉ số"
        >
          {(
            [
              ["orders", "Số đơn"],
              ["gmv", "Giá trị"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              aria-pressed={metric === key}
              onClick={() => setMetric(key)}
              className={cn(
                "rounded-md px-2.5 py-1 transition",
                metric === key
                  ? "bg-foreground text-background"
                  : "hover:bg-muted"
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
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
        />
      </CardContent>
    </Card>
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

// ---------- 1) Việc cần xử lý ----------
function Attention({ data }: { data: Dashboard }) {
  const a = data.attention
  const items: {
    icon: LucideIcon
    label: string
    value: number
    to: string
    hint: string
    urgent?: boolean
  }[] = [
    {
      icon: FolderOpen,
      label: "Case chờ nhận",
      value: a.open_cases,
      to: "/console/cases",
      hint: `${a.in_review_cases} case đang được xử lý`,
    },
    {
      icon: AlarmClock,
      label: "Case quá 24 giờ chưa ai nhận",
      value: a.stale_cases,
      to: "/console/cases",
      hint: "Nên ưu tiên trước",
      urgent: true,
    },
    {
      icon: Hourglass,
      label: "Đơn đang giữ chờ duyệt",
      value: a.pending_orders,
      to: "/console/cases",
      hint: "Khách đang chờ xác nhận đơn",
      urgent: true,
    },
    {
      icon: TriangleAlert,
      label: "Lỗi hệ thống",
      value: a.failed_jobs + a.risk_errors,
      to: "/console/reports",
      hint: `${a.failed_jobs} việc nền lỗi · ${a.risk_errors} lượt chấm điểm lỗi`,
      urgent: true,
    },
  ]
  return (
    <section aria-labelledby="can-xu-ly">
      <h2
        id="can-xu-ly"
        className="mb-3 text-sm font-medium text-muted-foreground"
      >
        Cần xử lý ngay
      </h2>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {items.map(({ icon: Icon, label, value, to, hint, urgent }) => {
          const hot = value > 0 && urgent
          return (
            <Link
              key={label}
              to={to}
              className={cn(
                "group flex items-start gap-3 rounded-xl border p-4 transition hover:bg-muted/50",
                hot && "border-[#d03b3b]/40 bg-[#d03b3b]/5"
              )}
            >
              <span
                className={cn(
                  "flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted",
                  hot && "bg-[#d03b3b] text-white"
                )}
              >
                {value === 0 ? (
                  <CircleCheck className="size-4.5" />
                ) : (
                  <Icon className="size-4.5" />
                )}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-2xl font-semibold tabular-nums">
                  {value}
                </span>
                <span className="block text-sm">{label}</span>
                <span className="block text-xs text-muted-foreground">
                  {value === 0 ? "Không có gì tồn đọng" : hint}
                </span>
              </span>
              <ArrowRight className="mt-1 size-4 text-muted-foreground opacity-0 transition group-hover:opacity-100" />
            </Link>
          )
        })}
      </div>
    </section>
  )
}

// ---------- 2) Shop và rủi ro: thẻ KPI có so sánh kỳ trước ----------
function ShopKpis({ data }: { data: Dashboard }) {
  const c = data.current
  const p = data.previous
  const pct = (a: number, b: number) => (b > 0 ? a / b : null)
  // Chuỗi theo ngày cho sparkline trong từng thẻ
  const s = data.series
  const decisionsPerDay = s.map(
    (d) => d.ALLOW + d.ALLOW_WITH_RESTRICTION + d.REVIEW + d.BLOCK
  )
  return (
    <section aria-labelledby="chi-so" className="grid gap-3">
      <h2 id="chi-so" className="text-sm font-medium text-muted-foreground">
        {data.days} ngày qua, so với {data.days} ngày trước đó
      </h2>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi
          label="Giá trị đơn hàng (GMV)"
          value={formatVND(c.gmv)}
          now={c.gmv}
          before={p.gmv}
          note="Không tính đơn bị hủy hoặc từ chối"
          trend={s.map((d) => d.gmv)}
        />
        <Kpi
          label="Đơn hàng"
          value={c.orders.toLocaleString("vi-VN")}
          now={c.orders}
          before={p.orders}
          trend={s.map((d) => d.orders)}
        />
        <Kpi
          label="Khách hàng mới"
          value={c.new_customers.toLocaleString("vi-VN")}
          now={c.new_customers}
          before={p.new_customers}
        />
        <Kpi
          label="Tỷ lệ đơn COD"
          value={percent(pct(c.cod_orders, c.orders))}
          now={pct(c.cod_orders, c.orders)}
          before={pct(p.cod_orders, p.orders)}
          neutral
          note={`${c.cod_orders} đơn thanh toán khi nhận hàng`}
        />
        <Kpi
          label="Đơn dùng voucher"
          value={c.voucher_orders.toLocaleString("vi-VN")}
          now={c.voucher_orders}
          before={p.voucher_orders}
          neutral
          note={`${percent(pct(c.voucher_orders, c.orders))} tổng số đơn`}
        />
        <Kpi
          label="Lượt chấm điểm rủi ro"
          value={c.decisions.toLocaleString("vi-VN")}
          now={c.decisions}
          before={p.decisions}
          neutral
          trend={decisionsPerDay}
        />
        <Kpi
          label="Tỷ lệ can thiệp"
          value={percent(pct(c.intervened, c.decisions))}
          now={pct(c.intervened, c.decisions)}
          before={pct(p.intervened, p.decisions)}
          neutral
          note={`${c.intervened} lượt hạn chế, giữ hoặc chặn`}
          trend={s.map((d, i) =>
            decisionsPerDay[i]
              ? (decisionsPerDay[i] - d.ALLOW) / decisionsPerDay[i]
              : 0
          )}
          trendColor="var(--st-warning)"
        />
        <Kpi
          label="Độ trễ chấm điểm (p95)"
          value={
            data.latency_p95_ms === null ? "—" : `${data.latency_p95_ms} ms`
          }
          note="95% lượt chấm điểm nhanh hơn mức này"
        />
      </div>
    </section>
  )
}

function Kpi({
  label,
  value,
  now,
  before,
  neutral,
  note,
  trend,
  trendColor,
}: {
  label: string
  value: string
  now?: number | null
  before?: number | null
  neutral?: boolean // tăng/giảm không mang nghĩa tốt/xấu (ví dụ tỷ lệ COD)
  note?: string
  trend?: number[] // số liệu từng ngày, vẽ thành sparkline
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
            "inline-flex items-center gap-0.5 tabular-nums",
            neutral
              ? "text-muted-foreground"
              : up
                ? "text-[#006300] dark:text-[#0ca30c]"
                : "text-[#d03b3b]"
          )}
        >
          <Icon className="size-3.5" aria-hidden />
          {up ? "Tăng" : "Giảm"}{" "}
          {Math.abs(change * 100).toLocaleString("vi-VN", {
            maximumFractionDigits: 1,
          })}
          %
        </span>
      )
    }
  }
  return (
    <div className="flex flex-col rounded-xl border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight tabular-nums">
        {value}
      </p>
      <div className="mt-1 grid gap-0.5 text-xs">
        {delta}
        {note && <span className="text-muted-foreground">{note}</span>}
      </div>
      {trend && trend.some((v) => v > 0) && (
        <div className="mt-auto pt-3 pr-1">
          <Sparkline values={trend} color={trendColor} />
        </div>
      )}
    </div>
  )
}

// ---------- 3) Luật khớp nhiều nhất ----------
function TopRules({ data }: { data: Dashboard }) {
  const max = Math.max(1, ...data.top_rules.map((r) => r.hits))
  return (
    <Card className="viz">
      <CardHeader>
        <CardTitle>Luật khớp nhiều nhất</CardTitle>
      </CardHeader>
      <CardContent>
        {data.top_rules.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Chưa có luật nào khớp trong khoảng này.
          </p>
        ) : (
          <ul className="grid gap-3">
            {data.top_rules.map((r) => (
              <li key={r.code}>
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <span className="min-w-0 truncate">{r.name ?? r.code}</span>
                  <b className="tabular-nums">
                    {r.hits.toLocaleString("vi-VN")}
                  </b>
                </div>
                <div
                  className="mt-1 h-2 overflow-hidden rounded-full bg-muted"
                  aria-hidden
                >
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${(r.hits / max) * 100}%`,
                      background: "var(--series-1)",
                    }}
                  />
                </div>
                <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                  {r.code}
                </p>
              </li>
            ))}
          </ul>
        )}
        <Link
          to="/console/rules"
          className="mt-4 inline-flex items-center gap-1 text-sm hover:underline"
        >
          Xem tất cả luật <ArrowRight className="size-4" />
        </Link>
      </CardContent>
    </Card>
  )
}

// ---------- Các lượt can thiệp gần nhất ----------
function RecentInterventions({ data }: { data: Dashboard }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Can thiệp gần nhất</CardTitle>
      </CardHeader>
      <CardContent>
        {data.recent_interventions.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Chưa có lượt can thiệp nào.
          </p>
        ) : (
          <ul className="divide-y">
            {data.recent_interventions.map((r) => (
              <li key={r.public_id} className="grid gap-1 py-2.5 text-sm">
                {/* Dòng 1: quyết định, ngữ cảnh, khách (email đã che). Dòng 2: điểm, giờ, case/đơn liên quan */}
                <div className="flex min-w-0 items-center gap-2">
                  <DecisionBadge decision={r.decision} />
                  <span className="shrink-0 text-muted-foreground">
                    {CONTEXT_LABELS[r.context]}
                  </span>
                  <span className="min-w-0 truncate">{r.user_email}</span>
                </div>
                <div className="flex flex-wrap items-center gap-x-2 text-xs text-muted-foreground tabular-nums">
                  <span>{r.score} điểm</span>
                  <span>·</span>
                  <span>{formatDateTime(r.created_at)}</span>
                  {r.case_code ? (
                    <>
                      <span>·</span>
                      <Link
                        to={`/console/cases/${r.case_code}`}
                        className="font-medium text-foreground hover:underline"
                      >
                        Case {r.case_code}
                      </Link>
                    </>
                  ) : r.order_code ? (
                    <>
                      <span>·</span>
                      <span className="font-mono">Đơn {r.order_code}</span>
                    </>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
        <Link
          to="/console/monitor"
          className="mt-4 inline-flex items-center gap-1 text-sm hover:underline"
        >
          Mở Live Monitor <ArrowRight className="size-4" />
        </Link>
      </CardContent>
    </Card>
  )
}

// ---------- Trạng thái hệ thống (dòng nhỏ cuối trang) ----------
function SystemLine({ data }: { data: Dashboard }) {
  const health = useHealth()
  const ok = health.isSuccess
  return (
    <p
      className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground"
      role="status"
    >
      <span
        className={cn(
          "size-2 rounded-full",
          ok ? "bg-[#0ca30c]" : "bg-[#d03b3b]"
        )}
        aria-hidden
      />
      {ok
        ? "API và cơ sở dữ liệu hoạt động bình thường"
        : "Không kết nối được API hoặc cơ sở dữ liệu"}
      <span>·</span>
      {data.attention.risk_errors === 0
        ? "Không có lỗi chấm điểm trong kỳ"
        : `${data.attention.risk_errors} lượt chấm điểm lỗi trong kỳ`}
    </p>
  )
}

function DashboardSkeleton() {
  return (
    <div className="grid gap-6" aria-busy="true" aria-label="Đang tải">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }, (_, i) => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 7 }, (_, i) => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <Skeleton className="h-72 rounded-xl" />
        <Skeleton className="h-72 rounded-xl" />
      </div>
    </div>
  )
}

function percent(v: number | null) {
  return v === null
    ? "—"
    : `${(v * 100).toLocaleString("vi-VN", { maximumFractionDigits: 1 })}%`
}
