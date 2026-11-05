import { useState } from "react"
import { Link, Navigate } from "react-router"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useMe } from "@/lib/api/auth"
import { PAYMENT_LABELS, useMyOrders } from "@/lib/api/order"
import { formatDateTime, formatVND } from "@/lib/format"
import { OrderStatusBadge } from "@/shop/components/OrderStatusBadge"

// Hiện dần từng 10 đơn: khách mua nhiều không phải cuộn một danh sách dài
const PAGE = 10

export function OrdersPage() {
  const { data: user, isPending } = useMe()
  const orders = useMyOrders()
  const [shown, setShown] = useState(PAGE)

  if (isPending) return null
  if (!user) return <Navigate to="/login?next=/orders" replace />

  return (
    <div className="py-8 pb-16">
      <h1 className="text-2xl font-semibold tracking-tight">
        Đơn hàng của tôi
      </h1>
      {orders.isPending ? (
        <Skeleton className="mt-6 h-32 w-full rounded-xl" />
      ) : orders.isError ? (
        <p className="mt-6 text-destructive">{orders.error.message}</p>
      ) : orders.data.length === 0 ? (
        <div className="mt-6 rounded-xl border p-10 text-center">
          <p className="font-medium">Bạn chưa có đơn hàng nào.</p>
          <Button className="mt-4" asChild>
            <Link to="/">Mua sắm ngay</Link>
          </Button>
        </div>
      ) : (
        <>
        <ul className="mt-6 grid gap-3">
          {orders.data.slice(0, shown).map((o) => (
            <li key={o.order_code}>
              <Link
                to={`/orders/${o.order_code}`}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border p-4 transition hover:bg-muted/50"
              >
                <div>
                  <p className="font-mono font-medium">{o.order_code}</p>
                  <p className="text-sm text-muted-foreground">
                    {formatDateTime(o.created_at)} · {o.item_count} sản phẩm ·{" "}
                    {PAYMENT_LABELS[o.payment_method]}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <OrderStatusBadge status={o.status} />
                  <span className="font-semibold tabular-nums">
                    {formatVND(o.total)}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
        <div className="mt-4 flex flex-col items-center gap-2 text-sm text-muted-foreground">
          <span className="tabular-nums">
            Đang xem {Math.min(shown, orders.data.length)}/{orders.data.length} đơn
          </span>
          {shown < orders.data.length && (
            <Button variant="outline" onClick={() => setShown((n) => n + PAGE)}>
              Xem thêm {Math.min(PAGE, orders.data.length - shown)} đơn
            </Button>
          )}
        </div>
        </>
      )}
    </div>
  )
}
