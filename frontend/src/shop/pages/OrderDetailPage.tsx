import { CircleCheck } from "lucide-react"
import { Link, useParams, useSearchParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { PAYMENT_LABELS, STATUS_LABELS, useOrder } from "@/lib/api/order"
import { formatDateTime, formatVND } from "@/lib/format"
import { OrderStatusBadge } from "@/shop/components/OrderStatusBadge"

export function OrderDetailPage() {
  const { code = "" } = useParams()
  const [params] = useSearchParams()
  const order = useOrder(code)

  if (order.isPending)
    return <Skeleton className="my-8 h-64 w-full rounded-xl" />
  if (order.isError) {
    return (
      <div className="py-16 text-center">
        <h1 className="text-xl font-semibold">Không tìm thấy đơn hàng</h1>
        <Button variant="outline" className="mt-6" asChild>
          <Link to="/orders">Về danh sách đơn</Link>
        </Button>
      </div>
    )
  }

  const o = order.data
  return (
    <div className="grid gap-6 py-8 pb-16">
      {params.get("new") && (
        <div
          className="flex items-start gap-3 rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4"
          role="status"
        >
          <CircleCheck className="mt-0.5 size-5 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <div>
            <p className="font-medium">Đặt hàng thành công!</p>
            <p className="text-sm text-muted-foreground">
              Cảm ơn bạn đã mua sắm tại RiskShop.
            </p>
          </div>
        </div>
      )}

      {order.data.status === "PENDING_REVIEW" && (
        <div
          className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-sm"
          role="status"
        >
          <p className="font-medium">Đơn hàng đang chờ xác minh</p>
          <p className="text-muted-foreground">
            Để bảo vệ bạn và người bán, đơn hàng này cần được xác nhận thêm
            trước khi giao. Chúng tôi sẽ liên hệ qua số điện thoại nhận hàng.
          </p>
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link
            to="/orders"
            className="text-sm text-muted-foreground hover:text-foreground"
          >
            ← Đơn hàng của tôi
          </Link>
          <h1 className="mt-1 font-mono text-2xl font-semibold">
            {o.order_code}
          </h1>
          <p className="text-sm text-muted-foreground">
            Đặt lúc {formatDateTime(o.created_at)}
          </p>
        </div>
        <OrderStatusBadge status={o.status} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <Card>
          <CardHeader>
            <CardTitle>Sản phẩm</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm">
            {o.items.map((i) => (
              <div key={i.product_id} className="flex justify-between gap-3">
                <span>
                  {i.product_name}{" "}
                  <span className="text-muted-foreground">
                    × {i.quantity} ({formatVND(i.unit_price)})
                  </span>
                </span>
                <span className="shrink-0 tabular-nums">
                  {formatVND(i.line_total)}
                </span>
              </div>
            ))}
            <div className="border-t pt-3">
              <div className="flex justify-between">
                <span>Tạm tính</span>
                <span className="tabular-nums">{formatVND(o.subtotal)}</span>
              </div>
              {o.discount > 0 && (
                <div className="flex justify-between text-emerald-600 dark:text-emerald-400">
                  <span>Giảm giá ({o.voucher_code})</span>
                  <span className="tabular-nums">−{formatVND(o.discount)}</span>
                </div>
              )}
              <div className="mt-1 flex justify-between text-base font-semibold">
                <span>Tổng cộng</span>
                <span className="tabular-nums">{formatVND(o.total)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid content-start gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Giao tới</CardTitle>
            </CardHeader>
            <CardContent className="text-sm">
              <p className="font-medium">
                {o.address.recipient_name} · {o.address.phone}
              </p>
              <p className="text-muted-foreground">
                {o.address.line}, {o.address.ward}, {o.address.district},{" "}
                {o.address.province}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Thanh toán & giao hàng</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2 text-sm">
              <p>
                {PAYMENT_LABELS[o.payment_method]} ·{" "}
                <span className="text-muted-foreground">
                  {o.payment_status === "PAID"
                    ? "Đã thanh toán"
                    : "Chưa thanh toán"}
                </span>
              </p>
              <ol className="mt-2 grid gap-2 border-l pl-4">
                <li>
                  <span className="font-medium">Đặt hàng</span>{" "}
                  <span className="text-muted-foreground">
                    {formatDateTime(o.created_at)}
                  </span>
                </li>
                {o.events.map((e, idx) => (
                  <li key={idx}>
                    <span className="font-medium">
                      {STATUS_LABELS[e.status]}
                    </span>{" "}
                    <span className="text-muted-foreground">
                      {formatDateTime(e.occurred_at)}
                    </span>
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
