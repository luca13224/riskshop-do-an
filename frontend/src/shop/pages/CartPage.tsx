import { Info, TicketPercent, Trash2, X } from "lucide-react"
import { useState, type FormEvent } from "react"
import { Link, Navigate } from "react-router"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { useMe } from "@/lib/api/auth"
import {
  useApplyVoucher,
  useCart,
  useRemoveCartItem,
  useRemoveVoucher,
  useUpdateCartItem,
  type Cart,
} from "@/lib/api/cart"
import { formatVND } from "@/lib/format"
import { ProductImage } from "@/shop/components/ProductImage"
import { QuantityStepper } from "@/shop/components/QuantityStepper"

export function CartPage() {
  const { data: user, isPending: userPending } = useMe()
  const cart = useCart()

  if (userPending) return null
  if (!user) return <Navigate to="/login?next=/cart" replace />
  if (user.role !== "customer") return <Navigate to="/" replace />

  return (
    <div className="py-8 pb-16">
      <h1 className="text-2xl font-semibold tracking-tight">Giỏ hàng</h1>
      {cart.isPending ? (
        <Skeleton className="mt-6 h-40 w-full rounded-xl" />
      ) : cart.isError ? (
        <p className="mt-6 text-destructive">{cart.error.message}</p>
      ) : cart.data.items.length === 0 ? (
        <div className="mt-6 rounded-xl border p-10 text-center">
          <p className="font-medium">Giỏ hàng đang trống.</p>
          <Button className="mt-4" asChild>
            <Link to="/">Tiếp tục mua sắm</Link>
          </Button>
        </div>
      ) : (
        <CartContent cart={cart.data} />
      )}
    </div>
  )
}

function CartContent({ cart }: { cart: Cart }) {
  const update = useUpdateCartItem()
  const remove = useRemoveCartItem()
  const busy = update.isPending || remove.isPending
  const itemError = update.error ?? remove.error

  return (
    <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_340px]">
      <div className="grid content-start gap-3">
        {cart.notice && (
          <p
            className="flex items-start gap-2 rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm"
            role="status"
          >
            <Info className="mt-0.5 size-4 shrink-0" /> {cart.notice}
          </p>
        )}
        {itemError && (
          <p className="text-sm text-destructive" role="alert">
            {itemError.message}
          </p>
        )}
        {cart.items.map((item) => (
          <div
            key={item.product_id}
            className="flex gap-4 rounded-xl border p-3"
          >
            <Link
              to={`/products/${item.slug}`}
              className="w-20 shrink-0 overflow-hidden rounded-lg sm:w-24"
            >
              <ProductImage
                category={item.category}
                imageUrl={item.image_url}
                name={item.name}
                iconClassName="size-8"
              />
            </Link>
            <div className="flex min-w-0 flex-1 flex-col gap-2">
              <div className="flex items-start justify-between gap-2">
                <Link
                  to={`/products/${item.slug}`}
                  className="line-clamp-2 font-medium hover:underline"
                >
                  {item.name}
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Xóa ${item.name} khỏi giỏ`}
                  disabled={busy}
                  onClick={() => remove.mutate(item.product_id)}
                >
                  <Trash2 />
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                {formatVND(item.unit_price)}
              </p>
              <div className="mt-auto flex flex-wrap items-center justify-between gap-2">
                <QuantityStepper
                  value={item.quantity}
                  max={Math.min(item.stock, 99)}
                  disabled={busy}
                  label={`Số lượng ${item.name}`}
                  onChange={(quantity) =>
                    update.mutate({ product_id: item.product_id, quantity })
                  }
                />
                <span className="font-semibold">
                  {formatVND(item.line_total)}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid content-start gap-4">
        <VoucherBox cart={cart} />
        <Card>
          <CardHeader>
            <CardTitle>Tóm tắt đơn hàng</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm">
            <Row
              label={`Tạm tính (${cart.item_count} sản phẩm)`}
              value={formatVND(cart.subtotal)}
            />
            {cart.discount > 0 && (
              <Row
                label={`Giảm giá (${cart.voucher?.code})`}
                value={`−${formatVND(cart.discount)}`}
                className="text-emerald-600 dark:text-emerald-400"
              />
            )}
            <div className="my-1 border-t" />
            <Row
              label="Tổng cộng"
              value={formatVND(cart.total)}
              className="text-base font-semibold"
            />
            <Button size="lg" className="mt-3" asChild>
              <Link to="/checkout">Tiến hành đặt hàng</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function VoucherBox({ cart }: { cart: Cart }) {
  const apply = useApplyVoucher()
  const removeVoucher = useRemoveVoucher()
  const [code, setCode] = useState("")

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!code.trim()) return
    apply.mutate(code, { onSuccess: () => setCode("") })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TicketPercent className="size-5" /> Mã giảm giá
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2">
        {cart.voucher ? (
          <div className="flex items-start justify-between gap-2 rounded-lg border border-dashed p-3">
            <div>
              <p className="font-mono font-semibold">{cart.voucher.code}</p>
              <p className="text-sm text-muted-foreground">
                {cart.voucher.description}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              aria-label="Bỏ mã giảm giá"
              disabled={removeVoucher.isPending}
              onClick={() => removeVoucher.mutate()}
            >
              <X />
            </Button>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="flex gap-2">
            <Input
              value={code}
              onChange={(e) => {
                setCode(e.target.value)
                apply.reset()
              }}
              placeholder="Nhập mã, ví dụ NGUOIMOI"
              aria-label="Mã giảm giá"
              className="uppercase placeholder:normal-case"
            />
            <Button type="submit" variant="outline" disabled={apply.isPending}>
              Áp dụng
            </Button>
          </form>
        )}
        {apply.isError && (
          <>
            <p className="text-sm text-destructive" role="alert">
              {apply.error.message}
            </p>
            <p className="text-sm text-muted-foreground">
              Bạn nghĩ đây là nhầm lẫn?{" "}
              <Link
                to="/appeals"
                className="font-medium text-foreground underline underline-offset-4"
              >
                Gửi khiếu nại
              </Link>
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}

function Row({
  label,
  value,
  className,
}: {
  label: string
  value: string
  className?: string
}) {
  return (
    <div className={`flex justify-between gap-4 ${className ?? ""}`}>
      <span>{label}</span>
      <span className="tabular-nums">{value}</span>
    </div>
  )
}
