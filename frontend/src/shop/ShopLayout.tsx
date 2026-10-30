import { LogOut, Package, ShoppingBag, User } from "lucide-react"
import { useEffect, useState } from "react"
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router"

import { Button } from "@/components/ui/button"
import { isStaff, useLogout, useMe } from "@/lib/api/auth"
import { useCart } from "@/lib/api/cart"
import { useCategories } from "@/lib/api/catalog"
import { cn } from "@/lib/utils"

function CartButton() {
  const { data: cart } = useCart()
  const count = cart?.item_count ?? 0
  return (
    <Link
      to="/cart"
      aria-label={`Giỏ hàng, ${count} sản phẩm`}
      className="relative flex size-10 items-center justify-center rounded-full hover:bg-secondary"
    >
      <ShoppingBag className="size-5" />
      {count > 0 && (
        <span className="absolute -top-0.5 -right-0.5 flex min-w-5 items-center justify-center rounded-full bg-buy px-1 text-[11px] leading-5 font-semibold text-buy-foreground">
          {count > 99 ? "99+" : count}
        </span>
      )}
    </Link>
  )
}

function Logo() {
  return (
    <Link
      to="/"
      className="flex items-center gap-2"
      aria-label="RiskShop, về trang chủ"
    >
      <span className="flex size-8 items-center justify-center rounded-xl bg-foreground text-background">
        <span className="size-2.5 rounded-full bg-buy" aria-hidden />
      </span>
      <span className="text-lg font-bold tracking-tight">RiskShop</span>
    </Link>
  )
}

// Header có đang nằm trên phần nền tối của banner trang chủ không (để đổi sang giao diện tối).
function useHeaderOverDark(): boolean {
  const { pathname } = useLocation()
  const [overDark, setOverDark] = useState(false)
  useEffect(() => {
    if (pathname !== "/") return
    let raf = 0
    function update() {
      raf = 0
      const dark = document.querySelector("[data-hero-dark]")
      const header = document.querySelector("header")
      if (!dark || !header) return setOverDark(false)
      // Tối khi phần nền tối còn nằm dưới header VÀ "đèn rạp" chưa bật quá 1/3 (xem useLightsOn ở CinemaHero)
      const hero = document.getElementById("hero")
      const lights = hero
        ? Number(getComputedStyle(hero).getPropertyValue("--lights") || 0)
        : 0
      setOverDark(
        dark.getBoundingClientRect().bottom >
          header.getBoundingClientRect().bottom && lights < 0.3
      )
    }
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update)
    }
    raf = requestAnimationFrame(update)
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => {
      window.removeEventListener("scroll", onScroll)
      cancelAnimationFrame(raf)
      setOverDark(false)
    }
  }, [pathname])
  return pathname === "/" && overDark
}

// Khung chung của khu vực Shop. Lớp .shop (index.css) giữ Shop luôn ở tông sáng (ADR-005).
export function ShopLayout() {
  const { data: user } = useMe()
  const logout = useLogout()
  const navigate = useNavigate()
  const overDark = useHeaderOverDark()
  const isHome = useLocation().pathname === "/"

  return (
    <div className="shop flex min-h-svh flex-col overflow-x-clip">
      {/* Trang chủ mở đầu bằng "phòng chiếu" tối, nên thanh thông báo cũng tối theo (nhấn cyan, ADR-005) */}
      <p
        className={cn(
          "px-4 py-2 text-center text-xs font-medium sm:text-sm",
          isHome
            ? "border-b border-white/5 bg-[#05070b] text-white/70"
            : "bg-buy text-buy-foreground"
        )}
      >
        Khách mới nhập mã{" "}
        <b className={isHome ? "text-cyan-300" : undefined}>TANTHU</b> giảm
        50.000đ cho đơn từ 200.000đ
      </p>

      <header
        className={cn(
          "sticky top-0 z-40 border-b bg-background/85 text-foreground backdrop-blur-md transition-colors duration-300",
          overDark && "header-dark"
        )}
      >
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          <Logo />

          <nav
            className="hidden items-center gap-1 text-sm md:flex"
            aria-label="Chính"
          >
            <HeaderLink to="/" end>
              Trang chủ
            </HeaderLink>
            <a
              href="/#san-pham"
              className="rounded-full px-3 py-2 hover:bg-secondary"
            >
              Sản phẩm
            </a>
            {user?.role === "customer" && (
              <HeaderLink to="/orders">Đơn hàng</HeaderLink>
            )}
          </nav>

          <div className="flex items-center gap-1">
            {user ? (
              <>
                <span className="hidden max-w-40 truncate px-2 text-sm text-muted-foreground lg:inline">
                  {user.full_name}
                </span>
                {user.role === "customer" && (
                  <>
                    <Link
                      to="/orders"
                      aria-label="Đơn hàng của tôi"
                      className="flex size-10 items-center justify-center rounded-full hover:bg-secondary md:hidden"
                    >
                      <Package className="size-5" />
                    </Link>
                    <CartButton />
                  </>
                )}
                {isStaff(user) && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="rounded-full"
                    asChild
                  >
                    <Link to="/console">Risk Console</Link>
                  </Button>
                )}
                <button
                  type="button"
                  aria-label="Đăng xuất"
                  title="Đăng xuất"
                  disabled={logout.isPending}
                  onClick={() =>
                    logout.mutate(undefined, { onSuccess: () => navigate("/") })
                  }
                  className="flex size-10 items-center justify-center rounded-full hover:bg-secondary"
                >
                  <LogOut className="size-5" />
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="flex items-center gap-2 rounded-full px-3 py-2 text-sm hover:bg-secondary"
                >
                  <User className="size-5" />
                  <span className="hidden sm:inline">Đăng nhập</span>
                </Link>
                <Button size="sm" className="h-9 rounded-full px-4" asChild>
                  <Link to="/register">Đăng ký</Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 sm:px-6">
        <Outlet />
      </main>

      <ShopFooter />
    </div>
  )
}

function HeaderLink({
  to,
  end,
  children,
}: {
  to: string
  end?: boolean
  children: string
}) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        cn(
          "rounded-full px-3 py-2 hover:bg-secondary",
          isActive && "font-semibold"
        )
      }
    >
      {children}
    </NavLink>
  )
}

function ShopFooter() {
  const categories = useCategories()
  return (
    <footer className="mt-20 bg-[#141414] text-white/70">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-14 sm:grid-cols-2 sm:px-6 lg:grid-cols-4">
        <div>
          <p className="text-lg font-bold text-white">RiskShop</p>
          <p className="mt-3 text-sm leading-relaxed">
            Sàn đồ công nghệ mô phỏng, có hệ thống kiểm soát rủi ro và ngăn ngừa
            lạm dụng chính sách chạy phía sau mọi đơn hàng.
          </p>
        </div>
        <div>
          <p className="font-semibold text-white">Danh mục</p>
          <ul className="mt-3 grid gap-2 text-sm">
            {categories.data?.map((c) => (
              <li key={c.code}>
                <Link
                  to={`/?category=${c.code}#san-pham`}
                  className="hover:text-white"
                >
                  {c.name}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="font-semibold text-white">Mua sắm</p>
          <ul className="mt-3 grid gap-2 text-sm">
            <li>Thanh toán khi nhận hàng (COD) hoặc trả trước</li>
            <li>Mã TANTHU cho khách mới</li>
            <li>Mã GIAM10 giảm 10% (tối đa 100.000đ) cho đơn từ 500.000đ</li>
          </ul>
        </div>
        <div>
          <p className="font-semibold text-white">Về dự án</p>
          <p className="mt-3 text-sm leading-relaxed">
            Đồ án tốt nghiệp, Trường Đại học Thủy Lợi. Sản phẩm, giá và đơn hàng
            đều là dữ liệu mô phỏng.
          </p>
        </div>
      </div>
      <p className="border-t border-white/10 py-5 text-center text-xs">
        © 2026 RiskShop · Dữ liệu mô phỏng, không phải cửa hàng thật
      </p>
    </footer>
  )
}
