import type { ReactNode } from "react"

import { ColumnChart } from "@/console/components/ColumnChart"
import { DecisionMix } from "@/console/components/DecisionMix"
import type { Dashboard } from "@/lib/api/dashboard"
import { CONTEXT_LABELS, type Decision } from "@/lib/api/risk"
import { cn } from "@/lib/utils"

// ---------------------------------------------------------------------------------------------
// Biểu đồ của trang Báo cáo, bản tinh gọn (2026-11-06): chỉ giữ 2 biểu đồ, mỗi cái trả lời một câu hỏi.
//   - Xu hướng can thiệp: hệ thống can thiệp bao nhiêu, kiểu gì, ở điểm kiểm soát nào
//   - Phân bố điểm rủi ro: ngưỡng đang đặt có hợp lý không (điểm dồn ở đâu)
// Đã bỏ: bản đồ nhiệt khung giờ, đơn hàng theo ngày (có ở Tổng quan), danh sách luật khớp nhiều nhất
// (gộp vào bảng "Hiệu quả từng luật").
// ---------------------------------------------------------------------------------------------
const STACK: { key: Decision; label: string; color: string }[] = [
  { key: "ALLOW", label: "Cho phép", color: "var(--st-good)" },
  { key: "ALLOW_WITH_RESTRICTION", label: "Hạn chế", color: "var(--st-warning)" },
  { key: "REVIEW", label: "Chờ duyệt", color: "var(--st-serious)" },
  { key: "BLOCK", label: "Chặn", color: "var(--st-critical)" },
]
const INTERVENTIONS = STACK.slice(1)

export function Panel({
  title,
  subtitle,
  className,
  children,
}: {
  title: string
  subtitle?: string
  className?: string
  children: ReactNode
}) {
  return (
    <section className={cn("panel flex min-w-0 flex-col gap-4 p-5", className)}>
      <header className="min-w-0">
        <h2 className="font-semibold">{title}</h2>
        {subtitle && <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>}
      </header>
      {children}
    </section>
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
    <div className="viz grid gap-6 xl:grid-cols-2">
      <Panel title="Xu hướng can thiệp" subtitle="Tỷ lệ cả kỳ, số lượt từng ngày và theo điểm kiểm soát">
        <DecisionMix counts={sumDecisions(data)} />
        <ColumnChart
          data={data.series}
          series={INTERVENTIONS}
          height={180}
          emptyText="Chưa có can thiệp nào trong khoảng này"
        />
        <p className="text-xs text-muted-foreground">
          Can thiệp / tổng lượt:{" "}
          {data.by_context.map((c) => `${CONTEXT_LABELS[c.context]} ${c.intervened}/${c.total}`).join(" · ")}
        </p>
      </Panel>
      <Panel title="Phân bố điểm rủi ro" subtitle="Số lượt chấm điểm theo khoảng điểm, tô màu theo quyết định">
        <ColumnChart
          data={data.score_histogram}
          series={STACK}
          xLabel={(k) => (k === "90" ? "90–100" : `${k}–${Number(k) + 9}`)}
          xTitle="Khoảng điểm"
          height={260}
        />
      </Panel>
    </div>
  )
}
