import {
  ArrowDown,
  ArrowUp,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Search,
} from "lucide-react"
import { Fragment, useMemo, useState } from "react"

import { Skeleton } from "@/components/ui/skeleton"
import { DecisionBadge, ScoreBar } from "@/console/components/DecisionBadge"
import { DecisionDetail } from "@/console/components/DecisionDetail"
import {
  CONTEXT_LABELS,
  DECISION_LABELS,
  useRiskDecisions,
  type Decision,
} from "@/lib/api/risk"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

type Filter = "INTERVENED" | Decision | "ALL"
const FILTERS: { value: Filter; label: string }[] = [
  { value: "INTERVENED", label: "Cần chú ý" },
  { value: "BLOCK", label: DECISION_LABELS.BLOCK },
  { value: "REVIEW", label: DECISION_LABELS.REVIEW },
  {
    value: "ALLOW_WITH_RESTRICTION",
    label: DECISION_LABELS.ALLOW_WITH_RESTRICTION,
  },
  { value: "ALL", label: "Tất cả" },
]
const PAGE = 8

// Hàng đợi cảnh báo: 100 quyết định gần nhất, lọc / tìm / sắp xếp / phân trang ngay trên trình duyệt.
// Bấm một dòng để mở chi tiết (luật nào khớp, giá trị thực tế, hành động) mà không rời dashboard.
export function AlertsTable() {
  const decisions = useRiskDecisions(false)
  const [filter, setFilter] = useState<Filter>("INTERVENED")
  const [q, setQ] = useState("")
  const [sort, setSort] = useState<{ key: "time" | "score"; desc: boolean }>({
    key: "time",
    desc: true,
  })
  const [page, setPage] = useState(0)
  const [open, setOpen] = useState<string | null>(null)

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase()
    const list = (decisions.data ?? []).filter((d) => {
      if (
        filter === "INTERVENED"
          ? d.decision === "ALLOW"
          : filter !== "ALL" && d.decision !== filter
      )
        return false
      if (!needle) return true
      return [
        d.user_email,
        d.user_name,
        d.order_code ?? "",
        d.public_id,
        ...d.hits.map((h) => h.rule_code),
      ]
        .join(" ")
        .toLowerCase()
        .includes(needle)
    })
    const dir = sort.desc ? -1 : 1
    return list.sort(
      (a, b) => dir * (sort.key === "score" ? a.score - b.score : a.id - b.id)
    )
  }, [decisions.data, filter, q, sort])

  const pages = Math.max(1, Math.ceil(rows.length / PAGE))
  const current = Math.min(page, pages - 1)
  const visible = rows.slice(current * PAGE, current * PAGE + PAGE)

  function toggleSort(key: "time" | "score") {
    setSort((s) =>
      s.key === key ? { key, desc: !s.desc } : { key, desc: true }
    )
    setPage(0)
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div
          className="flex flex-wrap gap-1.5"
          role="group"
          aria-label="Lọc theo quyết định"
        >
          {FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              aria-pressed={filter === f.value}
              onClick={() => {
                setFilter(f.value)
                setPage(0)
              }}
              className={cn(
                "rounded-full border px-3 py-1 text-xs transition hover:border-primary/40 hover:text-foreground",
                filter === f.value
                  ? "border-primary/50 bg-primary/15 text-foreground"
                  : "text-muted-foreground"
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
        <label className="relative w-full sm:w-64">
          <span className="sr-only">Tìm cảnh báo</span>
          <Search className="pointer-events-none absolute top-1/2 left-3 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => {
              setQ(e.target.value)
              setPage(0)
            }}
            placeholder="Tìm khách, mã đơn, mã luật…"
            className="h-8 w-full rounded-lg border bg-transparent pr-3 pl-8 text-xs outline-none placeholder:text-muted-foreground focus-visible:border-primary/60 focus-visible:ring-2 focus-visible:ring-primary/30"
          />
        </label>
      </div>

      {decisions.isPending ? (
        <div className="grid gap-2">
          {Array.from({ length: 5 }, (_, i) => (
            <Skeleton key={i} className="h-10 rounded-lg" />
          ))}
        </div>
      ) : decisions.isError ? (
        <p className="text-sm text-destructive">{decisions.error.message}</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-left text-sm">
            <thead className="bg-muted/60 text-xs text-muted-foreground">
              <tr>
                <th className="w-8 px-3 py-2" />
                <SortHeader
                  label="Thời gian"
                  active={sort.key === "time"}
                  desc={sort.desc}
                  onClick={() => toggleSort("time")}
                />
                <th className="px-3 py-2 font-medium">Quyết định</th>
                <SortHeader
                  label="Điểm"
                  active={sort.key === "score"}
                  desc={sort.desc}
                  onClick={() => toggleSort("score")}
                />
                <th className="px-3 py-2 font-medium">Khách</th>
                <th className="px-3 py-2 font-medium">Điểm kiểm soát</th>
                <th className="px-3 py-2 font-medium">Lý do chính</th>
              </tr>
            </thead>
            <tbody>
              {visible.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-3 py-8 text-center text-muted-foreground"
                  >
                    Không có cảnh báo nào khớp bộ lọc.
                  </td>
                </tr>
              )}
              {visible.map((d) => {
                const expanded = open === d.public_id
                const top = [...d.hits].sort((a, b) => b.points - a.points)[0]
                return (
                  <Fragment key={d.public_id}>
                    <tr
                      className={cn(
                        "cursor-pointer border-t transition-colors hover:bg-primary/5",
                        expanded && "bg-primary/5"
                      )}
                      onClick={() => setOpen(expanded ? null : d.public_id)}
                    >
                      <td className="px-3 py-2.5">
                        <button
                          type="button"
                          aria-expanded={expanded}
                          aria-label={
                            expanded ? "Thu gọn chi tiết" : "Xem chi tiết"
                          }
                          onClick={(e) => {
                            e.stopPropagation()
                            setOpen(expanded ? null : d.public_id)
                          }}
                          className="flex size-6 items-center justify-center rounded-md hover:bg-muted focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
                        >
                          <ChevronDown
                            className={cn(
                              "size-4 transition-transform",
                              expanded && "rotate-180"
                            )}
                          />
                        </button>
                      </td>
                      <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground tabular-nums">
                        {formatDateTime(d.created_at)}
                      </td>
                      <td className="px-3 py-2.5">
                        <DecisionBadge decision={d.decision} />
                      </td>
                      <td className="px-3 py-2.5">
                        <ScoreBar score={d.score} />
                      </td>
                      <td className="px-3 py-2.5">
                        <span className="block max-w-44 truncate">
                          {d.user_email}
                        </span>
                        {d.order_code && (
                          <span className="font-mono text-[11px] text-muted-foreground">
                            {d.order_code}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2.5 whitespace-nowrap text-muted-foreground">
                        {CONTEXT_LABELS[d.context]}
                      </td>
                      <td className="px-3 py-2.5">
                        <span className="line-clamp-1 max-w-80 text-muted-foreground">
                          {top ? top.reason_text : "—"}
                        </span>
                      </td>
                    </tr>
                    {expanded && (
                      <tr className="border-t bg-muted/30">
                        <td colSpan={7} className="px-4 py-4">
                          <DecisionDetail decision={d} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
        <span>{rows.length} cảnh báo · 100 quyết định gần nhất</span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            aria-label="Trang trước"
            disabled={current === 0}
            onClick={() => setPage(current - 1)}
            className="flex size-7 items-center justify-center rounded-md border hover:bg-muted disabled:opacity-40"
          >
            <ChevronLeft className="size-4" />
          </button>
          <span className="px-2 tabular-nums">
            {current + 1} / {pages}
          </span>
          <button
            type="button"
            aria-label="Trang sau"
            disabled={current >= pages - 1}
            onClick={() => setPage(current + 1)}
            className="flex size-7 items-center justify-center rounded-md border hover:bg-muted disabled:opacity-40"
          >
            <ChevronRight className="size-4" />
          </button>
        </div>
      </div>
    </div>
  )
}

function SortHeader({
  label,
  active,
  desc,
  onClick,
}: {
  label: string
  active: boolean
  desc: boolean
  onClick: () => void
}) {
  const Icon = desc ? ArrowDown : ArrowUp
  return (
    <th
      className="px-3 py-2 font-medium"
      aria-sort={active ? (desc ? "descending" : "ascending") : "none"}
    >
      <button
        type="button"
        onClick={onClick}
        className="inline-flex items-center gap-1 hover:text-foreground"
      >
        {label}
        <Icon className={cn("size-3", !active && "opacity-30")} aria-hidden />
      </button>
    </th>
  )
}
