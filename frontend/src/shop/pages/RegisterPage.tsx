import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Link, useNavigate } from "react-router"
import { z } from "zod"

import { FormField } from "@/components/form-field"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { ApiError } from "@/lib/api/client"
import { useRegister } from "@/lib/api/auth"

// Giữ quy tắc giống backend (app/modules/auth/schemas.py) để báo lỗi sớm cho người dùng
const schema = z.object({
  full_name: z
    .string()
    .trim()
    .min(1, { error: "Vui lòng nhập họ tên" })
    .max(120),
  email: z.email({ error: "Email không hợp lệ" }),
  phone: z
    .string()
    .trim()
    .regex(/^(0\d{9})?$/, {
      error: "Số điện thoại gồm 10 chữ số, bắt đầu bằng 0",
    }),
  password: z.string().min(8, { error: "Mật khẩu tối thiểu 8 ký tự" }).max(128),
})
type FormValues = z.infer<typeof schema>

export function RegisterPage() {
  const navigate = useNavigate()
  const register = useRegister()
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { phone: "" },
  })
  const { errors, isSubmitting } = form.formState

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      await register.mutateAsync({
        ...values,
        phone: values.phone || undefined,
      })
      navigate("/", { replace: true })
    } catch (err) {
      // Lỗi trùng email/số điện thoại: gắn thẳng vào ô tương ứng cho dễ thấy
      if (err instanceof ApiError && err.code === "EMAIL_TAKEN") {
        form.setError("email", { message: err.message })
      } else if (err instanceof ApiError && err.code === "PHONE_TAKEN") {
        form.setError("phone", { message: err.message })
      }
    }
  })

  const otherError =
    register.error instanceof ApiError &&
    ["EMAIL_TAKEN", "PHONE_TAKEN"].includes(register.error.code)
      ? null
      : register.error

  return (
    <div className="flex justify-center py-12">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Tạo tài khoản</CardTitle>
          <CardDescription>
            Thành viên mới được tặng voucher tân thủ.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="grid gap-4" noValidate>
            <FormField
              id="full_name"
              label="Họ tên"
              autoComplete="name"
              error={errors.full_name?.message}
              {...form.register("full_name")}
            />
            <FormField
              id="email"
              label="Email"
              type="email"
              autoComplete="email"
              error={errors.email?.message}
              {...form.register("email")}
            />
            <FormField
              id="phone"
              label="Số điện thoại (không bắt buộc)"
              type="tel"
              autoComplete="tel"
              error={errors.phone?.message}
              {...form.register("phone")}
            />
            <FormField
              id="password"
              label="Mật khẩu"
              type="password"
              autoComplete="new-password"
              error={errors.password?.message}
              {...form.register("password")}
            />
            {otherError && (
              <p className="text-sm text-destructive" role="alert">
                {otherError.message}
              </p>
            )}
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Đang tạo tài khoản…" : "Đăng ký"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Đã có tài khoản?{" "}
              <Link
                to="/login"
                className="font-medium text-foreground underline-offset-4 hover:underline"
              >
                Đăng nhập
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
