import { ChevronLeft, ChevronRight, Search, X } from "lucide-react"
import { useState, type FormEvent, type ReactNode } from "react"
import { useSearchParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { useMe } from "@/lib/api/auth"
import {
  PAYMENT_LABELS,
  STATUS_LABELS,
  useStaffOrders,
  useUpdateShipment,
  type OrderStatus,
  type StaffOrder,
} from "@/lib/api/order"
import { formatDateTime, formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"
import { OrderStatusBadge } from "@/shop/components/OrderStatusBadge"

// Thứ tự chip lọc: đơn cần chú ý (chờ duyệt) đứng đầu, sau đó theo vòng đời đơn
const FILTERS: OrderStatus[] = [
  "PENDING_REVIEW",
  "CONFIRMED",
  "SHIPPING",
  "DELIVERED",
  "DELIVERY_FAILED",
  "REJECTED",
]

// Đơn hàng trong Console: lọc theo trạng thái, tìm theo mã đơn / email / tên, phân trang.
// Bộ lọc nằm trên URL (?status=&q=&page=) nên tải lại trang hay gửi link cho đồng nghiệp vẫn giữ đúng.
// Cập nhật giao hàng chỉ dành cho Admin và Risk Manager; kết quả giao hàng là dữ liệu cho luật COD (R07).
export function ConsoleOrdersPage() {
  const { data: user } = useMe()
  const [params, setParams] = useSearchParams()
  const status = (params.get("status") as OrderStatus | null) ?? undefined
  const q = params.get("q") ?? ""
  const page = Number(params.get("page") ?? "1") || 1
  const orders = useStaffOrders({ status, q, page })
  const update = useUpdateShipment()
  const canEdit = user?.role === "admin" || user?.role === "risk_manager"

  function setFilter(next: { status?: OrderStatus | null; q?: string; page?: number }) {
    const p = new URLSearchParams(params)
    if (next.status !== undefined) {
      if (next.status) p.set("status", next.status)
      else p.delete("status")
    }
    if (next.q !== undefined) {
      if (next.q) p.set("q", next.q)
      else p.delete("q")
    }
    if (next.page && next.page > 1) p.set("page", String(next.page))
    else p.delete("page")
    setParams(p, { replace: true })
  }

  const counts = orders.data?.status_counts ?? {}
  const allCount = Object.values(counts).reduce((a, b) => a + (b ?? 0), 0)
  const totalPages = orders.data
    ? Math.max(1, Math.ceil(orders.data.total / orders.data.page_size))
    : 1
  const filtered = !!status || !!q

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Đơn hàng</h1>
        <p className="text-sm text-muted-foreground">
          Theo dõi và cập nhật trạng thái giao hàng. Kết quả giao hàng là dữ liệu
          cho luật rủi ro COD.
          {!canEdit && " Vai trò của bạn chỉ được xem."}
        </p>
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-wrap gap-2" aria-label="Lọc theo trạng thái">
          <FilterChip active={!status} onClick={() => setFilter({ status: null })}>
            Tất cả <Count n={allCount} />
          </FilterChip>
          {FILTERS.map((s) => (
            <FilterChip
              key={s}
              active={status === s}
              onClick={() => setFilter({ status: s })}
            >
              {STATUS_LABELS[s]} <Count n={counts[s] ?? 0} attention={s === "PENDING_REVIEW"} />
            </FilterChip>
          ))}
        </div>
        <SearchBox
          key={q}
          initial={q}
          onSearch={(text) => setFilter({ q: text })}
        />
      </div>

      {update.isError && (
        <p className="text-sm text-destructive" role="alert">
          {update.error.message}
        </p>
      )}

      {orders.isPending ? (
        <Skeleton className="h-64 w-full rounded-xl" />
      ) : orders.isError ? (
        <div className="rounded-xl border p-6 text-center">
          <p className="text-destructive">{orders.error.message}</p>
          <Button variant="outline" size="sm" className="mt-3" onClick={() => orders.refetch()}>
            Thử lại
          </Button>
        </div>
      ) : orders.data.items.length === 0 ? (
        <div className="rounded-xl border p-10 text-center">
          <p className="font-medium">
            {filtered ? "Không có đơn nào khớp bộ lọc." : "Chưa có đơn hàng nào."}
          </p>
          {filtered && (
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => setParams(new URLSearchParams(), { replace: true })}
            >
              Xóa bộ lọc
            </Button>
          )}
        </div>
      ) : (
        <>
          <div
            className={cn(
              "overflow-x-auto rounded-xl border",
              orders.isPlaceholderData && "opacity-60 transition-opacity"
            )}
          >
            <table className="w-full text-sm">
              <caption className="sr-only">Danh sách đơn hàng</caption>
              <thead className="bg-muted/50 text-left text-muted-foreground">
                <tr>
                  <th scope="col" className="px-3 py-2 font-medium">Mã đơn</th>
                  <th scope="col" className="hidden px-3 py-2 font-medium md:table-cell">Khách hàng</th>
                  <th scope="col" className="hidden px-3 py-2 font-medium lg:table-cell">Thanh toán</th>
                  <th scope="col" className="hidden px-3 py-2 text-right font-medium lg:table-cell">Số SP</th>
                  <th scope="col" className="hidden px-3 py-2 text-right font-medium sm:table-cell">Tổng</th>
                  <th scope="col" className="px-3 py-2 font-medium">Trạng thái</th>
                  <th scope="col" className="px-3 py-2 font-medium">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {orders.data.items.map((o) => (
                  <tr key={o.order_code} className="border-t">
                    <td className="px-3 py-2">
                      <span className="font-mono">{o.order_code}</span>
                      <span className="block text-xs text-muted-foreground">
                        {formatDateTime(o.created_at)}
                      </span>
                      {/* Màn hẹp: gom khách, thanh toán, tổng tiền vào cột đầu */}
                      <span className="block text-xs text-muted-foreground md:hidden">{o.customer_email}</span>
                      <span className="block text-xs text-muted-foreground lg:hidden">
                        {PAYMENT_LABELS[o.payment_method]}
                        <span className="sm:hidden"> · {formatVND(o.total)}</span>
                      </span>
                    </td>
                    <td className="hidden px-3 py-2 md:table-cell">
                      {o.customer_name}
                      <span className="block text-xs text-muted-foreground">
                        {o.customer_email}
                      </span>
                    </td>
                    <td className="hidden px-3 py-2 lg:table-cell">{PAYMENT_LABELS[o.payment_method]}</td>
                    <td className="hidden px-3 py-2 text-right tabular-nums lg:table-cell">{o.item_count}</td>
                    <td className="hidden px-3 py-2 text-right whitespace-nowrap tabular-nums sm:table-cell">{formatVND(o.total)}</td>
                    <td className="px-3 py-2">
                      <OrderStatusBadge status={o.status} />
                    </td>
                    <td className="px-3 py-2">
                      <RowActions
                        order={o}
                        canEdit={canEdit}
                        pending={update.isPending}
                        onUpdate={(s) => update.mutate({ code: o.order_code, status: s })}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
            <span className="tabular-nums">
              {orders.data.total} đơn · trang {page}/{totalPages}
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setFilter({ page: page - 1 })}
                aria-label="Trang trước"
              >
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

function RowActions({
  order,
  canEdit,
  pending,
  onUpdate,
}: {
  order: StaffOrder
  canEdit: boolean
  pending: boolean
  onUpdate: (s: "SHIPPING" | "DELIVERED" | "DELIVERY_FAILED") => void
}) {
  if (order.status === "PENDING_REVIEW") {
    // Đơn bị giữ được duyệt/từ chối trong Case (có lý do và audit), không duyệt tắt ở đây
    return <span className="text-xs text-muted-foreground">Duyệt trong Case</span>
  }
  if (!canEdit) return null
  const actions =
    order.status === "CONFIRMED"
      ? [{ status: "SHIPPING" as const, label: "Giao cho vận chuyển" }]
      : order.status === "SHIPPING"
        ? [
            { status: "DELIVERED" as const, label: "Giao thành công" },
            { status: "DELIVERY_FAILED" as const, label: "Giao thất bại" },
          ]
        : []
  return (
    <div className="flex flex-wrap gap-2">
      {actions.map((a) => (
        <Button
          key={a.status}
          size="sm"
          variant={a.status === "DELIVERY_FAILED" ? "outline" : "secondary"}
          disabled={pending}
          onClick={() => onUpdate(a.status)}
        >
          {a.label}
        </Button>
      ))}
    </div>
  )
}

function FilterChip({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition hover:bg-muted",
        active && "border-primary/50 bg-primary/15 text-foreground"
      )}
    >
      {children}
    </button>
  )
}

function Count({ n, attention }: { n: number; attention?: boolean }) {
  return (
    <span
      className={cn(
        "rounded-full bg-muted px-1.5 text-xs tabular-nums text-muted-foreground",
        attention && n > 0 && "bg-amber-500/20 text-amber-300"
      )}
    >
      {n}
    </span>
  )
}

function SearchBox({ initial, onSearch }: { initial: string; onSearch: (q: string) => void }) {
  const [text, setText] = useState(initial)
  function submit(e: FormEvent) {
    e.preventDefault()
    onSearch(text.trim())
  }
  return (
    <form onSubmit={submit} role="search" className="relative w-full lg:w-80">
      <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Mã đơn, email hoặc tên khách…"
        aria-label="Tìm đơn hàng"
        className="pr-9 pl-9"
      />
      {text && (
        <button
          type="button"
          aria-label="Xóa từ khóa"
          onClick={() => {
            setText("")
            onSearch("")
          }}
          className="absolute top-1/2 right-2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:bg-muted"
        >
          <X className="size-4" />
        </button>
      )}
    </form>
  )
}
