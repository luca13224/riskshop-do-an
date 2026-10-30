import { ShoppingCart } from "lucide-react"
import { Link, Outlet, useNavigate } from "react-router"

import { Button } from "@/components/ui/button"
import { isStaff, useLogout, useMe } from "@/lib/api/auth"
import { useCart } from "@/lib/api/cart"

function CartButton() {
  const { data: cart } = useCart()
  const count = cart?.item_count ?? 0
  return (
    <Button variant="ghost" size="sm" asChild>
      <Link
        to="/cart"
        aria-label={`Giỏ hàng, ${count} sản phẩm`}
        className="relative"
      >
        <ShoppingCart />
        {count > 0 && (
          <span className="absolute -top-1 -right-1 flex min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[11px] leading-5 font-semibold text-primary-foreground">
            {count > 99 ? "99+" : count}
          </span>
        )}
      </Link>
    </Button>
  )
}

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
                <span className="hidden text-muted-foreground sm:inline">
                  {user.full_name}
                </span>
                {user.role === "customer" && (
                  <>
                    <Button variant="ghost" size="sm" asChild>
                      <Link to="/orders">Đơn hàng</Link>
                    </Button>
                    <CartButton />
                  </>
                )}
                {isStaff(user) && (
                  <Button variant="outline" size="sm" asChild>
                    <Link to="/console">Risk Console</Link>
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={logout.isPending}
                  onClick={() =>
                    logout.mutate(undefined, { onSuccess: () => navigate("/") })
                  }
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
