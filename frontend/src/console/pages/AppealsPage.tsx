import { useState } from "react"
import { Link } from "react-router"

import { AppealStatusBadge } from "@/components/appeal-status-badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  POLICY_LABELS,
  useStaffAppeals,
  type AppealStatus,
} from "@/lib/api/appeals"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const FILTERS: { value: AppealStatus | "ALL"; label: string }[] = [
  { value: "OPEN", label: "Chờ xử lý" },
  { value: "ACCEPTED", label: "Đã chấp nhận" },
  { value: "REJECTED", label: "Đã từ chối" },
  { value: "ALL", label: "Tất cả" },
]

// Danh sách khiếu nại của khách (ADR-006). Analyst xem được; Risk Manager/Admin mới kết luận.
export function AppealsPage() {
  const [filter, setFilter] = useState<AppealStatus | "ALL">("OPEN")
  const appeals = useStaffAppeals(filter)

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Khiếu nại</h1>
        <p className="text-sm text-muted-foreground">
          Khách cho rằng mình bị hạn chế nhầm. Chấp nhận thì khách được miễn trừ
          chính sách đó 30 ngày (luật vẫn chạy và vẫn ghi lại), đơn đang giữ
          được duyệt.
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

      {appeals.isPending ? (
        <Skeleton className="h-40 w-full rounded-xl" />
      ) : appeals.isError ? (
        <p className="text-destructive">{appeals.error.message}</p>
      ) : appeals.data.length === 0 ? (
        <p className="rounded-xl border p-8 text-center text-muted-foreground">
          Không có khiếu nại nào.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th className="px-4 py-2.5 font-medium">Mã</th>
                <th className="px-4 py-2.5 font-medium">Khách</th>
                <th className="px-4 py-2.5 font-medium">Bị hạn chế</th>
                <th className="px-4 py-2.5 font-medium">Trạng thái</th>
                <th className="px-4 py-2.5 font-medium">Gửi lúc</th>
              </tr>
            </thead>
            <tbody>
              {appeals.data.map((a) => (
                <tr key={a.appeal_code} className="border-t hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <Link
                      to={`/console/appeals/${a.appeal_code}`}
                      className="font-mono font-medium hover:underline"
                    >
                      {a.appeal_code}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    {a.user_name}
                    <span className="block text-xs text-muted-foreground">
                      {a.user_email}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {a.label}
                    <span className="block text-xs text-muted-foreground">
                      {POLICY_LABELS[a.policy]}
                      {a.order_code && ` · Đơn ${a.order_code}`}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <AppealStatusBadge status={a.status} />
                    {a.handled_by_name && (
                      <span className="mt-1 block text-xs text-muted-foreground">
                        {a.handled_by_name}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap text-muted-foreground">
                    {formatDateTime(a.created_at)}
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
