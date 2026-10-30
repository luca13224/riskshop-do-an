import { useState } from "react"
import { Link } from "react-router"

import { Skeleton } from "@/components/ui/skeleton"
import { CaseStatusBadge } from "@/console/components/CaseStatusBadge"
import { ScoreBar } from "@/console/components/DecisionBadge"
import { POLICY_LABELS, useCases, type CaseFilter } from "@/lib/api/cases"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const FILTERS: { value: CaseFilter; label: string }[] = [
  { value: "ACTIVE", label: "Cần xử lý" },
  { value: "CLOSED", label: "Đã đóng" },
  { value: "ALL", label: "Tất cả" },
]

export function CasesPage() {
  const [filter, setFilter] = useState<CaseFilter>("ACTIVE")
  const cases = useCases(filter)

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Case</h1>
        <p className="text-sm text-muted-foreground">
          Hệ thống tự mở case khi quyết định rủi ro cần người xem xét; các tài
          khoản cùng cụm được gom chung một case.
        </p>
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

      {cases.isPending ? (
        <Skeleton className="h-40 w-full rounded-xl" />
      ) : cases.isError ? (
        <p className="text-destructive">{cases.error.message}</p>
      ) : cases.data.length === 0 ? (
        <p className="rounded-xl border p-8 text-center text-muted-foreground">
          Không có case nào.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Case</th>
                <th className="px-3 py-2 font-medium">Chính sách</th>
                <th className="px-3 py-2 font-medium">Đối tượng</th>
                <th className="px-3 py-2 font-medium">Điểm cao nhất</th>
                <th className="px-3 py-2 font-medium">Trạng thái</th>
                <th className="px-3 py-2 font-medium">Người xử lý</th>
              </tr>
            </thead>
            <tbody>
              {cases.data.map((c) => (
                <tr key={c.case_code} className="border-t hover:bg-muted/40">
                  <td className="px-3 py-2">
                    <Link
                      to={`/console/cases/${c.case_code}`}
                      className="font-mono font-medium underline-offset-4 hover:underline"
                    >
                      {c.case_code}
                    </Link>
                    <span className="block text-xs text-muted-foreground">
                      {formatDateTime(c.opened_at)}
                    </span>
                  </td>
                  <td className="px-3 py-2">{POLICY_LABELS[c.policy]}</td>
                  <td className="px-3 py-2">
                    {c.cluster_label}
                    <span className="block text-xs text-muted-foreground">
                      {c.primary_user_email} · {c.decision_count} quyết định
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    <ScoreBar score={c.max_score} />
                  </td>
                  <td className="px-3 py-2">
                    <CaseStatusBadge status={c.status} />
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">
                    {c.assigned_to_name ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
