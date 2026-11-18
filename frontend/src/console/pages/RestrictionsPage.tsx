import { ChevronLeft, ChevronRight, Search, X } from "lucide-react"
import { useState, type FormEvent } from "react"
import { Link, useSearchParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { CONTACT_ROLES, useMe } from "@/lib/api/auth"
import {
  RESTRICTION_STATUS_LABELS,
  useLiftRestriction,
  useRestrictionList,
  type RestrictionKind,
  type RestrictionRow,
  type RestrictionStatus,
} from "@/lib/api/risk"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const STATUSES: (RestrictionStatus | "all")[] = ["active", "expired", "lifted", "all"]
const KINDS: [RestrictionKind | "", string][] = [
  ["", "Mọi loại"],
  ["purchase_cooldown", "Khóa 24 giờ"],
  ["purchase_linked", "Khóa do liên kết"],
  ["purchase_ban", "Khóa vô thời hạn"],
]
const KIND_SHORT: Record<RestrictionKind, string> = {
  purchase_cooldown: "Khóa 24 giờ",
  purchase_linked: "Khóa do liên kết",
  purchase_ban: "Vô thời hạn",
}
const KIND_TONE: Record<RestrictionKind, string> = {
  purchase_cooldown: "bg-amber-500/15 text-amber-300",
  purchase_linked: "bg-orange-500/15 text-orange-300",
  purchase_ban: "bg-rose-500/15 text-rose-300",
}

// Tài khoản bị hạn chế quyền mua hàng: một nơi xem mọi lệnh khóa (tự động theo ADR-010, 011, 015 hoặc do
// nhân viên), vì sao, đến khi nào, ai gỡ. Nhân viên nào cũng xem được; chỉ Risk Manager / Admin gỡ khóa,
// bắt buộc lý do (ghi audit). Bộ lọc nằm trên URL (?status=&kind=&q=&page=).
export function RestrictionsPage() {
  const { data: me } = useMe()
  const canManage = !!me && CONTACT_ROLES.includes(me.role)
  const [params, setParams] = useSearchParams()
  const status = (params.get("status") as RestrictionStatus | "all" | null) ?? "active"
  const kind = (params.get("kind") as RestrictionKind | null) ?? undefined
  const q = params.get("q") ?? ""
  const page = Number(params.get("page") ?? "1") || 1
  const list = useRestrictionList({ status, kind, q, page })
  const [search, setSearch] = useState(q)

  function setFilter(next: { status?: string; kind?: string; q?: string; page?: number }) {
    const p = new URLSearchParams(params)
    for (const key of ["status", "kind", "q"] as const) {
      const v = next[key]
      if (v === undefined) continue
      if (v && !(key === "status" && v === "active")) p.set(key, v)
      else p.delete(key)
    }
    if (next.page && next.page > 1) p.set("page", String(next.page))
    else p.delete("page")
    setParams(p, { replace: true })
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    setFilter({ q: search.trim(), page: 1 })
  }

  const counts = list.data?.status_counts
  const allCount = counts ? counts.active + counts.expired + counts.lifted : undefined
  const totalPages = list.data ? Math.max(1, Math.ceil(list.data.total / list.data.page_size)) : 1

  return (
    <div className="mx-auto grid max-w-[1400px] gap-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Tài khoản bị khóa</h1>
        <p className="mt-1 max-w-3xl text-sm text-muted-foreground">
          Mọi lệnh khóa quyền mua hàng: hệ thống tự khóa khi khách cố đặt lặp sau nhiều lần bị từ chối hoặc né lệnh khóa
          bằng tài khoản mới; nhân viên khóa vô thời hạn sau khi xem xét. Khách bị khóa vẫn đăng nhập, xem đơn và gửi
          khiếu nại được.
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Lọc theo trạng thái">
        {STATUSES.map((s) => {
          const n = s === "all" ? allCount : counts?.[s]
          return (
            <button
              key={s}
              type="button"
              aria-pressed={status === s}
              onClick={() => setFilter({ status: s, page: 1 })}
              className={cn(
                "inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm transition-colors",
                status === s ? "border-primary/50 bg-primary/15 text-foreground" : "text-muted-foreground hover:bg-muted"
              )}
            >
              {s === "all" ? "Tất cả" : RESTRICTION_STATUS_LABELS[s]}
              {n !== undefined && (
                <span
                  className={cn(
                    "rounded-full px-1.5 text-xs tabular-nums",
                    s === "active" && n > 0 ? "bg-rose-500/20 text-rose-300" : "bg-muted"
                  )}
                >
                  {n}
                </span>
              )}
            </button>
          )
        })}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-flex flex-wrap rounded-lg border bg-muted/40 p-0.5 text-xs" role="group" aria-label="Loại khóa">
          {KINDS.map(([k, label]) => (
            <button
              key={label}
              type="button"
              aria-pressed={(kind ?? "") === k}
              onClick={() => setFilter({ kind: k, page: 1 })}
              className={cn(
                "rounded-md px-3 py-1.5 transition-colors",
                (kind ?? "") === k ? "bg-primary/20 text-foreground" : "text-muted-foreground hover:text-foreground"
              )}
            >
              {label}
            </button>
          ))}
        </div>
        <form onSubmit={submit} role="search" className="relative min-w-60 flex-1 sm:max-w-sm">
          <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Email hoặc tên khách…"
            aria-label="Tìm theo email hoặc tên khách"
            className="pr-9 pl-9"
          />
          {q && (
            <button
              type="button"
              aria-label="Xóa tìm kiếm"
              onClick={() => {
                setSearch("")
                setFilter({ q: "", page: 1 })
              }}
              className="absolute top-1/2 right-2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground"
            >
              <X className="size-4" />
            </button>
          )}
        </form>
      </div>

      {list.isPending ? (
        <Skeleton className="h-72 w-full rounded-xl" />
      ) : list.isError ? (
        <p className="text-destructive">{list.error.message}</p>
      ) : list.data.items.length === 0 ? (
        <p className="rounded-xl border p-10 text-center text-muted-foreground">
          {status === "active" ? "Hiện không có tài khoản nào bị khóa." : "Không có lệnh khóa nào khớp bộ lọc."}
        </p>
      ) : (
        <>
          <div className={cn("overflow-x-auto rounded-xl border", list.isPlaceholderData && "opacity-60 transition-opacity")}>
            <table className="w-full text-sm">
              <caption className="sr-only">Danh sách tài khoản bị hạn chế quyền mua hàng</caption>
              <thead className="bg-muted/50 text-left text-muted-foreground">
                <tr>
                  <th scope="col" className="px-3 py-2 font-medium">Khách hàng</th>
                  <th scope="col" className="px-3 py-2 font-medium">Loại khóa</th>
                  <th scope="col" className="hidden px-3 py-2 font-medium md:table-cell">Lý do</th>
                  <th scope="col" className="hidden px-3 py-2 font-medium lg:table-cell">Thời gian</th>
                  <th scope="col" className="hidden px-3 py-2 text-right font-medium sm:table-cell">Điểm tin cậy</th>
                  <th scope="col" className="px-3 py-2 font-medium">Xử lý</th>
                </tr>
              </thead>
              <tbody>
                {list.data.items.map((r) => (
                  <Row key={r.id} r={r} canManage={canManage} />
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
            <span className="tabular-nums">
              {list.data.total} lệnh khóa · trang {page}/{totalPages}
            </span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setFilter({ page: page - 1 })} aria-label="Trang trước">
                <ChevronLeft className="size-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setFilter({ page: page + 1 })}
                aria-label="Trang sau"
              >
                <ChevronRight className="size-4" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function Row({ r, canManage }: { r: RestrictionRow; canManage: boolean }) {
  const [open, setOpen] = useState(false)
  const [reason, setReason] = useState("")
  const lift = useLiftRestriction(r.user_id)
  const period = `${formatDateTime(r.created_at)} → ${r.expires_at ? formatDateTime(r.expires_at) : "vô thời hạn"}`

  return (
    <>
      <tr className="border-t align-top">
        <td className="px-3 py-2">
          <span className="font-medium">{r.user_name}</span>
          <span className="block text-xs text-muted-foreground">{r.user_email}</span>
          {/* Màn hẹp: gom lý do và thời gian vào cột đầu */}
          <span className="mt-1 block text-xs text-muted-foreground md:hidden">{r.reason}</span>
          <span className="block text-xs text-muted-foreground tabular-nums lg:hidden">{period}</span>
        </td>
        <td className="px-3 py-2">
          <span className={cn("inline-block rounded-md px-2 py-0.5 text-xs font-medium whitespace-nowrap", KIND_TONE[r.kind])}>
            {KIND_SHORT[r.kind]}
          </span>
          <span className="mt-1 block text-xs text-muted-foreground">
            {r.source === "staff" ? "Nhân viên khóa" : "Hệ thống tự khóa"}
          </span>
          {r.status !== "active" && (
            <span className="mt-1 block text-xs text-muted-foreground">{RESTRICTION_STATUS_LABELS[r.status]}</span>
          )}
        </td>
        <td className="hidden max-w-sm px-3 py-2 md:table-cell">
          {r.reason}
          {r.status === "lifted" && (
            <span className="mt-1 block text-xs text-muted-foreground">
              Gỡ bởi {r.lifted_by_name ?? "?"} lúc {r.lifted_at ? formatDateTime(r.lifted_at) : "?"}: {r.lift_reason}
            </span>
          )}
        </td>
        <td className="hidden px-3 py-2 whitespace-nowrap tabular-nums lg:table-cell">{period}</td>
        <td className="hidden px-3 py-2 text-right tabular-nums sm:table-cell">{r.trust_score ?? "—"}</td>
        <td className="px-3 py-2">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            {r.case_code && (
              <Link to={`/console/cases/${r.case_code}`} className="text-xs text-primary whitespace-nowrap hover:underline">
                Xem case
              </Link>
            )}
            {canManage && r.status === "active" && (
              <button
                type="button"
                aria-expanded={open}
                onClick={() => setOpen((v) => !v)}
                className="text-xs whitespace-nowrap text-rose-300 hover:underline"
              >
                Gỡ khóa
              </button>
            )}
          </div>
        </td>
      </tr>
      {open && (
        <tr className="bg-muted/30">
          <td colSpan={6} className="px-3 py-3">
            <form
              className="flex flex-wrap items-center gap-2"
              onSubmit={(e) => {
                e.preventDefault()
                lift.mutate(reason, { onSuccess: () => setOpen(false) })
              }}
            >
              <label htmlFor={`lift-${r.id}`} className="text-sm">
                Lý do gỡ khóa (ghi vào audit log):
              </label>
              <Input
                id={`lift-${r.id}`}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                minLength={10}
                maxLength={255}
                placeholder="Ví dụ: đã gọi điện xác minh, khách thật bấm lặp do mạng chậm"
                className="min-w-64 flex-1"
                autoFocus
              />
              <Button type="submit" size="sm" disabled={lift.isPending || reason.trim().length < 10}>
                Xác nhận gỡ khóa
              </Button>
              <Button type="button" size="sm" variant="ghost" onClick={() => setOpen(false)}>
                Hủy
              </Button>
              {lift.isError && (
                <p className="w-full text-destructive" role="alert">
                  {lift.error.message}
                </p>
              )}
            </form>
          </td>
        </tr>
      )}
    </>
  )
}
