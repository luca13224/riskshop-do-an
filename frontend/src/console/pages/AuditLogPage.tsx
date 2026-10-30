import { useState } from "react"

import { Skeleton } from "@/components/ui/skeleton"
import { useMe } from "@/lib/api/auth"
import { useAuditLogs } from "@/lib/api/reports"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const FILTERS = [
  { value: "", label: "Tất cả" },
  { value: "case", label: "Case" },
  { value: "rule", label: "Luật" },
  { value: "lab_run", label: "Attack Lab" },
  { value: "user", label: "Khách hàng" },
]

const ACTION_LABELS: Record<string, string> = {
  "case.claim": "Nhận xử lý case",
  "case.resolve": "Kết luận case",
  "rule.new_version": "Tạo phiên bản luật",
  "lab.start": "Chạy kịch bản Attack Lab",
  "user.reveal_contact": "Xem thông tin liên hệ khách",
}

function describe(
  before: Record<string, unknown> | null,
  after: Record<string, unknown> | null
) {
  const keys = new Set([
    ...Object.keys(before ?? {}),
    ...Object.keys(after ?? {}),
  ])
  return [...keys]
    .filter((k) => k !== "params") // tham số luật dài, xem ở trang Luật
    .map((k) => {
      const a = before?.[k]
      const b = after?.[k]
      return a === undefined
        ? `${k}: ${String(b)}`
        : `${k}: ${String(a)} → ${String(b)}`
    })
    .join(" · ")
}

export function AuditLogPage() {
  const { data: me } = useMe()
  const [filter, setFilter] = useState("")
  const logs = useAuditLogs(filter)

  if (me && me.role === "analyst") {
    return (
      <p className="text-muted-foreground">
        Audit Log chỉ dành cho Risk Manager và Admin.
      </p>
    )
  }

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Audit Log</h1>
        <p className="text-sm text-muted-foreground">
          Nhật ký mọi thao tác của nhân viên. Chỉ ghi thêm; không có chức năng
          sửa hay xóa.
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
      {logs.isPending ? (
        <Skeleton className="h-40 w-full rounded-xl" />
      ) : logs.isError ? (
        <p className="text-destructive">{logs.error.message}</p>
      ) : logs.data.length === 0 ? (
        <p className="rounded-xl border p-8 text-center text-muted-foreground">
          Chưa có thao tác nào.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Thời gian</th>
                <th className="px-3 py-2 font-medium">Người thực hiện</th>
                <th className="px-3 py-2 font-medium">Thao tác</th>
                <th className="px-3 py-2 font-medium">Đối tượng</th>
                <th className="px-3 py-2 font-medium">Thay đổi / ghi chú</th>
              </tr>
            </thead>
            <tbody>
              {logs.data.map((a) => (
                <tr key={a.id} className="border-t align-top">
                  <td className="px-3 py-2 whitespace-nowrap tabular-nums">
                    {formatDateTime(a.created_at)}
                  </td>
                  <td className="px-3 py-2">
                    {a.actor_name ?? "Hệ thống"}
                    {a.actor_role && (
                      <span className="block text-xs text-muted-foreground">
                        {a.actor_role}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {ACTION_LABELS[a.action] ?? a.action}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs">
                    {a.entity_type}:{a.entity_id}
                  </td>
                  <td className="px-3 py-2">
                    <span className="text-muted-foreground">
                      {describe(a.before_data, a.after_data)}
                    </span>
                    {a.note && <p>{a.note}</p>}
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
