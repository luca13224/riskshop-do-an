import { zodResolver } from "@hookform/resolvers/zod"
import { useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { useForm, useWatch } from "react-hook-form"
import { Link, Navigate, useNavigate } from "react-router"
import { z } from "zod"

import { FormField } from "@/components/form-field"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useMe } from "@/lib/api/auth"
import { useCart } from "@/lib/api/cart"
import { ApiError } from "@/lib/api/client"
import {
  PAYMENT_LABELS,
  useCheckout,
  usePaymentOptions,
  type PaymentMethod,
} from "@/lib/api/order"
import { formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"

const schema = z.object({
  recipient_name: z
    .string()
    .trim()
    .min(1, { error: "Vui lòng nhập tên người nhận" }),
  phone: z
    .string()
    .trim()
    .regex(/^0\d{9}$/, {
      error: "Số điện thoại gồm 10 chữ số, bắt đầu bằng 0",
    }),
  line: z.string().trim().min(3, { error: "Vui lòng nhập số nhà, tên đường" }),
  ward: z.string().trim().min(1, { error: "Vui lòng nhập phường/xã" }),
  district: z.string().trim().min(1, { error: "Vui lòng nhập quận/huyện" }),
  province: z.string().trim().min(1, { error: "Vui lòng nhập tỉnh/thành phố" }),
  payment_method: z.enum(["COD", "PREPAID"]),
})
type FormValues = z.infer<typeof schema>

export function CheckoutPage() {
  const { data: user, isPending } = useMe()
  const cart = useCart()
  const checkout = useCheckout()
  const navigate = useNavigate()
  // Mỗi lần vào trang thanh toán có một mã riêng. Bấm "Đặt hàng" nhiều lần hay mạng gửi lại
  // đều dùng cùng mã này, nên backend chỉ tạo đúng MỘT đơn (idempotency).
  const [idempotencyKey] = useState(() => crypto.randomUUID())

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      recipient_name: user?.full_name ?? "",
      phone: user?.phone ?? "",
      payment_method: "COD",
    },
  })
  const { errors, isSubmitting } = form.formState
  const paymentMethod = useWatch({
    control: form.control,
    name: "payment_method",
  })
  const queryClient = useQueryClient()
  // Hỏi Risk Engine trước: nếu không cho COD thì tắt lựa chọn COD ngay trên giao diện
  const options = usePaymentOptions(user?.role === "customer")
  const codAllowed = options.data?.cod_allowed ?? true
  useEffect(() => {
    if (options.data && !options.data.cod_allowed)
      form.setValue("payment_method", "PREPAID")
  }, [options.data, form])

  if (isPending) return null
  if (!user) return <Navigate to="/login?next=/checkout" replace />
  if (user.role !== "customer") return <Navigate to="/" replace />
  if (cart.data && cart.data.items.length === 0 && !checkout.isSuccess)
    return <Navigate to="/cart" replace />

  const onSubmit = form.handleSubmit(async ({ payment_method, ...address }) => {
    try {
      const order = await checkout.mutateAsync({
        idempotencyKey,
        address,
        payment_method,
      })
      navigate(`/orders/${order.order_code}?new=1`, { replace: true })
    } catch (err) {
      // Lỗi hiển thị bên dưới nút đặt hàng. Nếu Risk Engine vừa hạn chế, cập nhật lại giao diện:
      if (err instanceof ApiError && err.code === "COD_NOT_AVAILABLE") {
        await options.refetch()
      }
      if (err instanceof ApiError && err.code === "VOUCHER_NOT_APPLICABLE") {
        await queryClient.invalidateQueries({ queryKey: ["cart"] }) // voucher đã bị gỡ khỏi giỏ
      }
    }
  })

  return (
    <div className="py-8 pb-16">
      <Link
        to="/cart"
        className="text-sm text-muted-foreground hover:text-foreground"
      >
        ← Quay lại giỏ hàng
      </Link>
      <h1 className="mt-2 text-2xl font-semibold tracking-tight">Thanh toán</h1>

      <form
        onSubmit={onSubmit}
        noValidate
        className="mt-6 grid gap-6 lg:grid-cols-[1fr_340px]"
      >
        <div className="grid content-start gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Địa chỉ giao hàng</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <FormField
                id="recipient_name"
                label="Người nhận"
                autoComplete="name"
                error={errors.recipient_name?.message}
                {...form.register("recipient_name")}
              />
              <FormField
                id="phone"
                label="Số điện thoại"
                type="tel"
                autoComplete="tel"
                error={errors.phone?.message}
                {...form.register("phone")}
              />
              <div className="sm:col-span-2">
                <FormField
                  id="line"
                  label="Số nhà, tên đường"
                  autoComplete="address-line1"
                  error={errors.line?.message}
                  {...form.register("line")}
                />
              </div>
              <FormField
                id="ward"
                label="Phường/Xã"
                error={errors.ward?.message}
                {...form.register("ward")}
              />
              <FormField
                id="district"
                label="Quận/Huyện"
                error={errors.district?.message}
                {...form.register("district")}
              />
              <div className="sm:col-span-2">
                <FormField
                  id="province"
                  label="Tỉnh/Thành phố"
                  autoComplete="address-level1"
                  error={errors.province?.message}
                  {...form.register("province")}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Phương thức thanh toán</CardTitle>
            </CardHeader>
            <CardContent
              className="grid gap-3"
              role="radiogroup"
              aria-label="Phương thức thanh toán"
            >
              {(["COD", "PREPAID"] as PaymentMethod[]).map((method) => (
                <label
                  key={method}
                  className={cn(
                    "flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition hover:bg-muted/50",
                    paymentMethod === method && "border-foreground",
                    method === "COD" &&
                      !codAllowed &&
                      "cursor-not-allowed opacity-50"
                  )}
                >
                  <input
                    type="radio"
                    value={method}
                    className="mt-1"
                    disabled={method === "COD" && !codAllowed}
                    {...form.register("payment_method")}
                  />
                  <span>
                    <span className="font-medium">
                      {PAYMENT_LABELS[method]}
                    </span>
                    <span className="block text-sm text-muted-foreground">
                      {method === "COD"
                        ? codAllowed
                          ? "Trả tiền mặt cho nhân viên giao hàng."
                          : (options.data?.message ??
                            "Chưa hỗ trợ cho đơn hàng này.")
                        : "Cổng thanh toán mô phỏng, đơn được coi là đã thanh toán ngay."}
                    </span>
                  </span>
                </label>
              ))}
              {!codAllowed && (
                <p className="text-sm text-muted-foreground">
                  Bạn nghĩ đây là nhầm lẫn?{" "}
                  <Link
                    to="/appeals"
                    className="font-medium text-foreground underline underline-offset-4"
                  >
                    Gửi khiếu nại
                  </Link>
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Đơn hàng</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm">
            {cart.data?.items.map((item) => (
              <div key={item.product_id} className="flex justify-between gap-3">
                <span className="line-clamp-1">
                  {item.name}{" "}
                  <span className="text-muted-foreground">
                    × {item.quantity}
                  </span>
                </span>
                <span className="shrink-0 tabular-nums">
                  {formatVND(item.line_total)}
                </span>
              </div>
            ))}
            <div className="my-1 border-t" />
            <div className="flex justify-between">
              <span>Tạm tính</span>
              <span className="tabular-nums">
                {formatVND(cart.data?.subtotal ?? 0)}
              </span>
            </div>
            {!!cart.data?.discount && (
              <div className="flex justify-between text-emerald-600 dark:text-emerald-400">
                <span>Giảm giá ({cart.data.voucher?.code})</span>
                <span className="tabular-nums">
                  −{formatVND(cart.data.discount)}
                </span>
              </div>
            )}
            <div className="flex justify-between text-base font-semibold">
              <span>Tổng cộng</span>
              <span className="tabular-nums">
                {formatVND(cart.data?.total ?? 0)}
              </span>
            </div>
            {checkout.isError && (
              <p className="text-sm text-destructive" role="alert">
                {checkout.error.message}
              </p>
            )}
            <Button
              type="submit"
              size="lg"
              className="mt-3"
              disabled={isSubmitting || !cart.data}
            >
              {isSubmitting ? "Đang đặt hàng…" : "Đặt hàng"}
            </Button>
          </CardContent>
        </Card>
      </form>
    </div>
  )
}
