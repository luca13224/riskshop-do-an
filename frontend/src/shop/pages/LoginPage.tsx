import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { Link, Navigate, useNavigate, useSearchParams } from "react-router"
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
import { isStaff, useLogin, useMe } from "@/lib/api/auth"

// Quy tắc kiểm tra form, chạy ngay trên trình duyệt (backend vẫn kiểm tra lại)
const schema = z.object({
  email: z.email({ error: "Email không hợp lệ" }),
  password: z.string().min(1, { error: "Vui lòng nhập mật khẩu" }),
})
type FormValues = z.infer<typeof schema>

export function LoginPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const login = useLogin()
  const { data: me } = useMe()
  const form = useForm<FormValues>({ resolver: zodResolver(schema) })
  const { errors, isSubmitting } = form.formState

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      const user = await login.mutateAsync(values)
      // Chỉ cho chuyển tới đường dẫn nội bộ (bắt đầu bằng "/"), tránh bị lợi dụng chuyển sang trang lạ
      const next = params.get("next")
      const safeNext =
        next && next.startsWith("/") && !next.startsWith("//") ? next : null
      navigate(safeNext ?? (isStaff(user) ? "/console" : "/"), {
        replace: true,
      })
    } catch {
      // Lỗi đã nằm trong login.error, hiển thị bên dưới
    }
  })

  // Đã đăng nhập sẵn (không phải vừa bấm Đăng nhập ở đây) thì không cần form nữa
  if (me && login.isIdle) return <Navigate to={isStaff(me) ? "/console" : "/"} replace />

  return (
    <div className="flex justify-center py-12">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Đăng nhập</CardTitle>
          <CardDescription>
            Dùng chung cho khách hàng và nhân viên.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={onSubmit} className="grid gap-4" noValidate>
            <FormField
              id="email"
              label="Email"
              type="email"
              autoComplete="email"
              error={errors.email?.message}
              {...form.register("email")}
            />
            <FormField
              id="password"
              label="Mật khẩu"
              type="password"
              autoComplete="current-password"
              error={errors.password?.message}
              {...form.register("password")}
            />
            {login.error && (
              <p className="text-sm text-destructive" role="alert">
                {login.error.message}
              </p>
            )}
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Đang đăng nhập…" : "Đăng nhập"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Chưa có tài khoản?{" "}
              <Link
                to="/register"
                className="font-medium text-foreground underline-offset-4 hover:underline"
              >
                Đăng ký
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
