import { ArrowRight } from "lucide-react"
import { useState, type ReactNode } from "react"
import { Link } from "react-router"

import { ColumnChart } from "@/console/components/ColumnChart"
import { DecisionMix } from "@/console/components/DecisionMix"
import { Heatmap } from "@/console/components/Heatmap"
import type { Dashboard } from "@/lib/api/dashboard"
import { CONTEXT_LABELS, type Decision } from "@/lib/api/risk"
import { formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"

// ---------------------------------------------------------------------------------------------
// Phân tích chi tiết rủi ro (dời từ trang Tổng quan sang trang Báo cáo, 2026-11-05): phân bố điểm, khung giờ
// bị can thiệp, đơn hàng và can thiệp theo ngày, nguyên nhân. Mọi số liệu lấy từ API dashboard.
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

export function RiskAnalytics({ data }: { data: Dashboard }) {
  return (
    <div className="grid gap-6">
      <div className="grid gap-6 xl:grid-cols-12">
        <Panel
          className="xl:col-span-7"
          title="Phân bố điểm rủi ro"
          subtitle="Số lượt chấm điểm theo khoảng điểm"
        >
          <ColumnChart
            data={data.score_histogram}
            series={STACK}
            xLabel={(k) => (k === "90" ? "90–100" : `${k}–${Number(k) + 9}`)}
            xTitle="Khoảng điểm"
            height={230}
          />
        </Panel>
        <Panel
          className="xl:col-span-5"
          title="Khung giờ bị can thiệp"
          subtitle="Thứ × giờ, ô càng sáng càng nhiều lượt"
        >
          <Heatmap data={data.heatmap} />
        </Panel>
      </div>
      <div className="grid gap-6 lg:grid-cols-2 2xl:grid-cols-3">
        <OrdersPanel data={data} />
        <Panel title="Can thiệp theo ngày" subtitle="Tỷ lệ cả kỳ và từng ngày">
          <div className="grid gap-5">
            <DecisionMix counts={sumDecisions(data)} />
            <ColumnChart
              data={data.series}
              series={INTERVENTIONS}
              height={180}
              emptyText="Chưa có can thiệp nào trong khoảng này"
            />
          </div>
        </Panel>
        <CausesPanel data={data} className="lg:col-span-2 2xl:col-span-1" />
      </div>
    </div>
  )
}
