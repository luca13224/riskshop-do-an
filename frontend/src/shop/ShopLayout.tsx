import { Link, Outlet, useNavigate } from "react-router"

import { Button } from "@/components/ui/button"
import { isStaff, useLogout, useMe } from "@/lib/api/auth"

// Khung chung của khu vực Shop: thanh trên cùng + nội dung trang (Outlet)
export function ShopLayout() {
  const { data: user } = useMe()
  const logout = useLogout()
  const navigate = useNavigate()

  return (
    <div className="min-h-svh">
      <header className="border-b">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4">
          <Link to="/" className="text-lg font-semibold tracking-tight">
            RiskShop
          </Link>
          <nav className="flex items-center gap-2 text-sm">
            {user ? (
              <>
                <span className="hidden text-muted-foreground sm:inline">{user.full_name}</span>
                {isStaff(user) && (
                  <Button variant="outline" size="sm" asChild>
                    <Link to="/console">Risk Console</Link>
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={logout.isPending}
                  onClick={() => logout.mutate(undefined, { onSuccess: () => navigate("/") })}
                >
                  Đăng xuất
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" asChild>
                  <Link to="/login">Đăng nhập</Link>
                </Button>
                <Button size="sm" asChild>
                  <Link to="/register">Đăng ký</Link>
                </Button>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4">
        <Outlet />
      </main>
    </div>
  )
}
