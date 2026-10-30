import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useMe } from "@/lib/api/auth"
import {
  PAYMENT_LABELS,
  useStaffOrders,
  useUpdateShipment,
  type StaffOrder,
} from "@/lib/api/order"
import { formatDateTime, formatVND } from "@/lib/format"
import { OrderStatusBadge } from "@/shop/components/OrderStatusBadge"

// Màn hình tạm để giả lập đơn vị vận chuyển: tạo lịch sử giao thành công / thất bại.
// Đây là nguồn dữ liệu cho luật COD (R07). Chỉ Admin và Risk Manager được cập nhật.
export function ConsoleOrdersPage() {
  const { data: user } = useMe()
  const orders = useStaffOrders()
  const update = useUpdateShipment()
  const canEdit = user?.role === "admin" || user?.role === "risk_manager"

  function actions(o: StaffOrder) {
    if (o.status === "CONFIRMED")
      return [{ status: "SHIPPING" as const, label: "Giao cho vận chuyển" }]
    if (o.status === "SHIPPING")
      return [
        { status: "DELIVERED" as const, label: "Giao thành công" },
        { status: "DELIVERY_FAILED" as const, label: "Giao thất bại" },
      ]
    return []
  }

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Đơn hàng</h1>
        <p className="text-sm text-muted-foreground">
          Giả lập đơn vị vận chuyển. Kết quả giao hàng là dữ liệu cho luật rủi
          ro COD.
          {!canEdit && " Vai trò của bạn chỉ được xem."}
        </p>
      </div>
      {update.isError && (
        <p className="text-sm text-destructive" role="alert">
          {update.error.message}
        </p>
      )}
      {orders.isPending ? (
        <Skeleton className="h-40 w-full rounded-xl" />
      ) : orders.isError ? (
        <p className="text-destructive">{orders.error.message}</p>
      ) : orders.data.length === 0 ? (
        <p className="text-muted-foreground">Chưa có đơn hàng nào.</p>
      ) : (
        <div className="overflow-x-auto rounded-xl border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Mã đơn</th>
                <th className="px-3 py-2 font-medium">Khách hàng</th>
                <th className="px-3 py-2 font-medium">Thanh toán</th>
                <th className="px-3 py-2 text-right font-medium">Tổng</th>
                <th className="px-3 py-2 font-medium">Trạng thái</th>
                <th className="px-3 py-2 font-medium">Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {orders.data.map((o) => (
                <tr key={o.order_code} className="border-t">
                  <td className="px-3 py-2">
                    <span className="font-mono">{o.order_code}</span>
                    <span className="block text-xs text-muted-foreground">
                      {formatDateTime(o.created_at)}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    {o.customer_name}
                    <span className="block text-xs text-muted-foreground">
                      {o.customer_email}
                    </span>
                  </td>
                  <td className="px-3 py-2">
                    {PAYMENT_LABELS[o.payment_method]}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums">
                    {formatVND(o.total)}
                  </td>
                  <td className="px-3 py-2">
                    <OrderStatusBadge status={o.status} />
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-2">
                      {canEdit &&
                        actions(o).map((a) => (
                          <Button
                            key={a.status}
                            size="sm"
                            variant={
                              a.status === "DELIVERY_FAILED"
                                ? "outline"
                                : "secondary"
                            }
                            disabled={update.isPending}
                            onClick={() =>
                              update.mutate({
                                code: o.order_code,
                                status: a.status,
                              })
                            }
                          >
                            {a.label}
                          </Button>
                        ))}
                    </div>
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
