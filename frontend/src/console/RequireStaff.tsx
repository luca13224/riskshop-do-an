import { Link, Navigate, Outlet, useLocation } from "react-router"

import { Button } from "@/components/ui/button"
import { isStaff, useMe } from "@/lib/api/auth"

// "Người gác cổng" của Console ở phía giao diện.
// Lưu ý: đây chỉ để trải nghiệm gọn gàng. Lớp chặn thật nằm ở backend (require_roles),
// nên kể cả ai đó sửa code frontend để vào được trang, API vẫn trả 403.
export function RequireStaff() {
  const { data: user, isPending } = useMe()
  const location = useLocation()

  if (isPending) {
    return (
      <p className="p-6 text-sm text-muted-foreground">
        Đang kiểm tra đăng nhập…
      </p>
    )
  }
  if (!user) {
    return (
      <Navigate
        to={`/login?next=${encodeURIComponent(location.pathname)}`}
        replace
      />
    )
  }
  if (!isStaff(user)) {
    return (
      <div className="flex min-h-svh flex-col items-center justify-center gap-4 p-6 text-center">
        <h1 className="text-xl font-semibold">
          Bạn không có quyền vào Risk Console
        </h1>
        <p className="text-sm text-muted-foreground">
          Khu vực này chỉ dành cho nhân viên kiểm soát rủi ro.
        </p>
        <Button variant="outline" asChild>
          <Link to="/">Về trang mua sắm</Link>
        </Button>
      </div>
    )
  }
  return <Outlet />
}
