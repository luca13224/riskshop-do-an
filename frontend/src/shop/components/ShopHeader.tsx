import {
  ArrowRight,
  ChevronDown,
  LogOut,
  Menu,
  Search,
  ShoppingBag,
  User,
  X,
} from "lucide-react"
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react"
import { Link, NavLink, useLocation, useNavigate } from "react-router"

import { Button } from "@/components/ui/button"
import { isStaff, useLogout, useMe } from "@/lib/api/auth"
import { useCart } from "@/lib/api/cart"
import { useCategories } from "@/lib/api/catalog"
import { cn } from "@/lib/utils"

type Panel = "categories" | "search" | "mobile"

// Header của Shop (phần HEAD). Hai hành vi khi cuộn:
// 1) đã cuộn thì thu thấp lại và thành kính mờ; 2) cuộn xuống thì ẩn để nhường chỗ cho nội dung,
// cuộn lên là hiện lại ngay.
export function ShopHeader() {
  const { data: user } = useMe()
  const logout = useLogout()
  const navigate = useNavigate()
  const location = useLocation()

  // Bảng đang mở gắn với location.key: đổi trang là bảng tự đóng, không cần effect riêng
  const [open, setOpen] = useState<{ panel: Panel; at: string } | null>(null)
  const panel = open?.at === location.key ? open.panel : null
  const toggle = (p: Panel) =>
    setOpen(panel === p ? null : { panel: p, at: location.key })
  const close = () => setOpen(null)

  const { hidden, scrolled } = useHeaderScroll(panel !== null)

  // Esc để đóng bảng đang mở
  useEffect(() => {
    if (!panel) return
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(null)
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [panel])

  // Rê chuột vào "Danh mục" là mở; rời khỏi cả nút lẫn bảng một lúc thì đóng
  const leaveTimer = useRef(0)
  const hoverOpen = () => {
    window.clearTimeout(leaveTimer.current)
    if (panel !== "categories") setOpen({ panel: "categories", at: location.key })
  }
  const hoverLeave = () => {
    window.clearTimeout(leaveTimer.current)
    leaveTimer.current = window.setTimeout(
      () => setOpen((o) => (o?.panel === "categories" ? null : o)),
      180
    )
  }

  const isCustomer = user?.role === "customer"

  return (
    <>
      <header
        data-hidden={hidden ? "" : undefined}
        className={cn(
          "shop-header sticky top-0 z-40 border-b text-foreground",
          scrolled || panel
            ? "bg-background/80 shadow-[0_8px_30px_-20px_rgba(0,0,0,.35)] backdrop-blur-xl"
            : "bg-background",
        )}
        onMouseLeave={panel === "categories" ? hoverLeave : undefined}
      >
        <div
          className={cn(
            "mx-auto flex max-w-7xl items-center justify-between gap-3 px-4 transition-[height] duration-300 sm:px-6",
            scrolled ? "h-14" : "h-16"
          )}
        >
          <div className="flex items-center gap-1">
            <IconButton
              label={panel === "mobile" ? "Đóng menu" : "Mở menu"}
              className="md:hidden"
              expanded={panel === "mobile"}
              controls="menu-mobile"
              onClick={() => toggle("mobile")}
            >
              {panel === "mobile" ? <X className="size-5" /> : <Menu className="size-5" />}
            </IconButton>
            <Logo />
          </div>

          <nav className="hidden items-center gap-0.5 text-sm md:flex" aria-label="Chính">
            <button
              type="button"
              aria-expanded={panel === "categories"}
              aria-controls="menu-danh-muc"
              onClick={() => toggle("categories")}
              onMouseEnter={hoverOpen}
              onMouseLeave={hoverLeave}
              className={cn(
                "flex items-center gap-1 rounded-full px-3 py-2 hover:bg-secondary",
                panel === "categories" && "bg-secondary"
              )}
            >
              Danh mục
              <ChevronDown
                className={cn("size-4 transition-transform", panel === "categories" && "rotate-180")}
              />
            </button>
            <HeaderLink to="/danh-muc">Tất cả sản phẩm</HeaderLink>
            <HeaderLink to="/#uu-dai" plain>
              Ưu đãi
            </HeaderLink>
            {isCustomer && (
              <>
                <HeaderLink to="/orders">Đơn hàng</HeaderLink>
                <HeaderLink to="/appeals">Khiếu nại</HeaderLink>
              </>
            )}
          </nav>

          <div className="flex items-center gap-1">
            <IconButton
              label="Tìm sản phẩm"
              expanded={panel === "search"}
              controls="menu-tim-kiem"
              onClick={() => toggle("search")}
            >
              <Search className="size-5" />
            </IconButton>
            {user ? (
              <>
                <span className="hidden max-w-36 truncate px-2 text-sm text-muted-foreground xl:inline">
                  {user.full_name}
                </span>
                {isCustomer && <CartButton />}
                {isStaff(user) && (
                  <Button variant="outline" size="sm" className="hidden rounded-full sm:inline-flex" asChild>
                    <Link to="/console">Risk Console</Link>
                  </Button>
                )}
                <IconButton
                  label="Đăng xuất"
                  className="hidden sm:flex"
                  disabled={logout.isPending}
                  onClick={() => logout.mutate(undefined, { onSuccess: () => navigate("/") })}
                >
                  <LogOut className="size-5" />
                </IconButton>
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
                <Button size="sm" className="hidden h-9 rounded-full px-4 sm:inline-flex" asChild>
                  <Link to="/register">Đăng ký</Link>
                </Button>
              </>
            )}
          </div>
        </div>

        {panel === "categories" && (
          <CategoriesPanel onMouseEnter={hoverOpen} onMouseLeave={hoverLeave} />
        )}
        {panel === "search" && <SearchPanel onDone={close} />}
        {panel === "mobile" && (
          <MobilePanel
            isCustomer={isCustomer}
            loggedIn={!!user}
            onLogout={() => logout.mutate(undefined, { onSuccess: () => navigate("/") })}
          />
        )}
      </header>
      {/* Lớp mờ phía sau bảng đang mở: bấm ra ngoài là đóng */}
      {panel && (
        <div
          aria-hidden
          onClick={close}
          className="fixed inset-0 z-30 bg-black/25 backdrop-blur-[2px] animate-in fade-in"
        />
      )}
    </>
  )
}

// ---------- Bảng danh mục lớn (mega menu) ----------
function CategoriesPanel({
  onMouseEnter,
  onMouseLeave,
}: {
  onMouseEnter: () => void
  onMouseLeave: () => void
}) {
  const categories = useCategories()
  return (
    <div
      id="menu-danh-muc"
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className="panel-in absolute inset-x-0 top-full border-b bg-background shadow-2xl"
    >
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[1fr_300px]">
        <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {categories.data?.map((c, i) => (
            <li key={c.code} className="panel-in" style={{ animationDelay: `${i * 35}ms` }}>
              <Link
                to={`/danh-muc/${c.code}`}
                className="group flex items-center gap-3 rounded-2xl p-2 transition hover:bg-secondary"
              >
                <span className="size-16 shrink-0 overflow-hidden rounded-xl bg-secondary">
                  <img
                    src={`/categories/${c.code}.webp`}
                    alt=""
                    loading="lazy"
                    className="size-full object-cover transition duration-500 group-hover:scale-110"
                  />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm leading-snug font-semibold">{c.name}</span>
                  <span className="text-xs text-muted-foreground">{c.product_count} sản phẩm</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
        <div className="relative isolate hidden overflow-hidden rounded-2xl bg-[#0a1120] p-5 text-white ring-1 ring-white/[.07] lg:block">
          <div
            aria-hidden
            className="absolute inset-0 -z-10 bg-[radial-gradient(70%_80%_at_100%_0%,rgba(255,214,10,.25),transparent_60%),radial-gradient(60%_70%_at_0%_100%,rgba(80,200,255,.2),transparent_60%)]"
          />
          <p className="text-xs tracking-widest text-white/60 uppercase">Khách mới</p>
          <p className="mt-2 text-lg leading-snug font-semibold">
            Nhập <span className="text-cyan-300">NGUOIMOI</span> giảm 50.000đ cho đơn đầu tiên
          </p>
          <Link
            to="/danh-muc"
            className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-buy"
          >
            Xem tất cả sản phẩm <ArrowRight className="size-4" />
          </Link>
        </div>
      </div>
    </div>
  )
}

// ---------- Bảng tìm kiếm ----------
function SearchPanel({ onDone }: { onDone: () => void }) {
  const navigate = useNavigate()
  const categories = useCategories()
  const [text, setText] = useState("")

  function submit(e: FormEvent) {
    e.preventDefault()
    const q = text.trim()
    navigate(q ? `/danh-muc?q=${encodeURIComponent(q)}` : "/danh-muc")
    onDone()
  }

  return (
    <div id="menu-tim-kiem" className="panel-in absolute inset-x-0 top-full border-b bg-background shadow-2xl">
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6">
        <form onSubmit={submit} role="search" className="relative">
          <Search className="pointer-events-none absolute top-1/2 left-5 size-5 -translate-y-1/2 text-muted-foreground" />
          <input
            autoFocus
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Tìm tai nghe, laptop, màn hình…"
            aria-label="Tìm sản phẩm"
            className="h-14 w-full rounded-full bg-secondary pr-28 pl-13 text-base outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <Button type="submit" className="absolute top-1/2 right-2 h-10 -translate-y-1/2 rounded-full px-5">
            Tìm
          </Button>
        </form>
        <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted-foreground">Gợi ý:</span>
          {categories.data?.map((c) => (
            <Link
              key={c.code}
              to={`/danh-muc/${c.code}`}
              className="rounded-full border px-3 py-1.5 transition hover:bg-secondary"
            >
              {c.name}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}

// ---------- Menu trên điện thoại ----------
function MobilePanel({
  isCustomer,
  loggedIn,
  onLogout,
}: {
  isCustomer: boolean
  loggedIn: boolean
  onLogout: () => void
}) {
  const categories = useCategories()
  const links: [string, string][] = [
    ["/danh-muc", "Tất cả sản phẩm"],
    ["/#uu-dai", "Ưu đãi"],
    ...(isCustomer
      ? ([
          ["/orders", "Đơn hàng của tôi"],
          ["/appeals", "Khiếu nại"],
        ] as [string, string][])
      : []),
  ]
  return (
    <nav
      id="menu-mobile"
      aria-label="Menu"
      className="panel-in absolute inset-x-0 top-full max-h-[calc(100svh-4rem)] overflow-y-auto border-b bg-background px-4 pt-2 pb-6 shadow-2xl md:hidden"
      data-lenis-prevent
    >
      <ul className="grid">
        {links.map(([to, label]) => (
          <li key={to}>
            <Link to={to} className="flex items-center justify-between border-b py-3.5 text-base font-medium">
              {label}
              <ArrowRight className="size-4 text-muted-foreground" />
            </Link>
          </li>
        ))}
      </ul>
      <p className="mt-5 text-xs font-medium tracking-widest text-muted-foreground uppercase">Danh mục</p>
      <ul className="mt-2 grid grid-cols-2 gap-2">
        {categories.data?.map((c) => (
          <li key={c.code}>
            <Link
              to={`/danh-muc/${c.code}`}
              className="flex items-center gap-2 rounded-2xl bg-secondary p-2 text-sm font-medium"
            >
              <img src={`/categories/${c.code}.webp`} alt="" className="size-10 rounded-xl object-cover" />
              <span className="leading-tight">{c.name}</span>
            </Link>
          </li>
        ))}
      </ul>
      {loggedIn && (
        <button
          type="button"
          onClick={onLogout}
          className="mt-5 flex items-center gap-2 text-sm text-muted-foreground"
        >
          <LogOut className="size-4" /> Đăng xuất
        </button>
      )}
    </nav>
  )
}

// ---------- Mảnh nhỏ ----------
function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2" aria-label="RiskShop, về trang chủ">
      <span className="flex size-8 items-center justify-center rounded-xl bg-foreground text-background">
        <span className="size-2.5 rounded-full bg-buy" aria-hidden />
      </span>
      <span className="text-lg font-bold tracking-tight">RiskShop</span>
    </Link>
  )
}

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

function IconButton({
  label,
  onClick,
  disabled,
  expanded,
  controls,
  className,
  children,
}: {
  label: string
  onClick: () => void
  disabled?: boolean
  expanded?: boolean
  controls?: string
  className?: string
  children: ReactNode
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      aria-expanded={expanded}
      aria-controls={controls}
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "flex size-10 items-center justify-center rounded-full hover:bg-secondary",
        expanded && "bg-secondary",
        className
      )}
    >
      {children}
    </button>
  )
}

function HeaderLink({ to, plain, children }: { to: string; plain?: boolean; children: string }) {
  if (plain) {
    return (
      <Link to={to} className="rounded-full px-3 py-2 hover:bg-secondary">
        {children}
      </Link>
    )
  }
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn("rounded-full px-3 py-2 hover:bg-secondary", isActive && "font-semibold")
      }
    >
      {children}
    </NavLink>
  )
}

// Theo dõi hướng cuộn: scrolled = đã rời đầu trang; hidden = đang cuộn xuống (đủ xa đầu trang).
// locked = đang mở bảng thì không ẩn header.
function useHeaderScroll(locked: boolean) {
  const [state, setState] = useState({ hidden: false, scrolled: false })
  useEffect(() => {
    let last = window.scrollY
    let raf = 0
    function update() {
      raf = 0
      const y = window.scrollY
      const dy = y - last
      if (Math.abs(dy) < 4) return // bỏ qua rung nhẹ
      last = y
      const next = { hidden: y > 240 && dy > 0, scrolled: y > 12 }
      setState((s) => (s.hidden === next.hidden && s.scrolled === next.scrolled ? s : next))
    }
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update)
    }
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => {
      window.removeEventListener("scroll", onScroll)
      cancelAnimationFrame(raf)
    }
  }, [])
  return { hidden: state.hidden && !locked, scrolled: state.scrolled }
}
