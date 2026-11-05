import { Link, Outlet } from "react-router"

import { Button } from "@/components/ui/button"
import { hasRole, useMe, type Role } from "@/lib/api/auth"

// Chặn ở giao diện khi nhân viên gõ thẳng đường dẫn của trang không thuộc quyền mình
// (vd. Analyst mở /console/audit). Lớp chặn thật vẫn là require_roles ở backend.
export function RequireRole({ roles }: { roles: Role[] }) {
  const { data: user } = useMe()
  if (hasRole(user, roles)) return <Outlet />
  return (
    <div className="panel mx-auto max-w-lg p-10 text-center">
      <h1 className="text-lg font-semibold">Trang này không thuộc quyền của bạn</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Vai trò hiện tại không được mở trang này. Cần quyền thì nhờ Admin cấp.
      </p>
      <Button variant="outline" className="mt-5" asChild>
        <Link to="/console">Về Tổng quan</Link>
      </Button>
    </div>
  )
}
