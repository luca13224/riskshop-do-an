import {
  Activity,
  BarChart3,
  FlaskConical,
  FolderOpen,
  LayoutDashboard,
  LogOut,
  MessageSquareWarning,
  Package,
  ScrollText,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Store,
  type LucideIcon,
} from "lucide-react"
import { useState, type FormEvent } from "react"
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router"

import { AUDIT_ROLES, LAB_ROLES, ROLE_LABELS, hasRole, useLogout, useMe, type Role } from "@/lib/api/auth"
import { useDashboard } from "@/lib/api/dashboard"
import { useHealth } from "@/lib/api/health"
import { Seo } from "@/lib/seo"
import { cn } from "@/lib/utils"

type BadgeKey = "cases" | "appeals"
interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  end?: boolean
  badge?: BadgeKey
  roles?: Role[] // bỏ trống: mọi nhân viên đều thấy
}

// Menu chia theo công việc của người vận hành: theo dõi -> xử lý -> cấu hình -> kiểm soát
const NAV_GROUPS: { title: string; items: NavItem[] }[] = [
  {
    title: "Giám sát",
    items: [
      { to: "/console", label: "Tổng quan", icon: LayoutDashboard, end: true },
      { to: "/console/monitor", label: "Live Monitor", icon: Activity },
      { to: "/console/reports", label: "Báo cáo", icon: BarChart3 },
    ],
  },
  {
    title: "Xử lý",
    items: [
      { to: "/console/cases", label: "Case", icon: FolderOpen, badge: "cases" },
      {
        to: "/console/appeals",
        label: "Khiếu nại",
        icon: MessageSquareWarning,
        badge: "appeals",
      },
      { to: "/console/orders", label: "Đơn hàng", icon: Package },
    ],
  },
  {
    title: "Cấu hình",
    items: [
      { to: "/console/rules", label: "Luật rủi ro", icon: SlidersHorizontal },
      { to: "/console/lab", label: "Attack Lab", icon: FlaskConical, roles: LAB_ROLES },
    ],
  },
  {
    title: "Kiểm soát",
    items: [{ to: "/console/audit", label: "Audit Log", icon: ScrollText, roles: AUDIT_ROLES }],
  },
]
const ALL_ITEMS = NAV_GROUPS.flatMap((g) => g.items)

// Khung chung của Risk Console. Lớp .console (index.css) giữ toàn bộ Console ở tông dark navy.
export function ConsoleLayout() {
  const { data: user } = useMe()
  const logout = useLogout()
  // Chỉ hiện mục người dùng được phép mở (Analyst không thấy Attack Lab, Audit Log)
  const groups = NAV_GROUPS.map((g) => ({ ...g, items: g.items.filter((i) => hasRole(user, i.roles)) })).filter(
    (g) => g.items.length > 0
  )
  const navigate = useNavigate()
  // Dùng chung bộ nhớ đệm với trang Tổng quan (cùng queryKey) nên không tốn thêm request
  const dash = useDashboard(7)
  const badges: Record<BadgeKey, number> = {
    cases: dash.data
      ? dash.data.attention.open_cases + dash.data.attention.in_review_cases
      : 0,
    appeals: dash.data?.attention.open_appeals ?? 0,
  }

  // Tiêu đề tab theo mục đang mở (khớp đường dẫn dài nhất); Console là khu vực nội bộ nên luôn noindex
  const { pathname } = useLocation()
  const current = ALL_ITEMS.filter((i) => pathname === i.to || pathname.startsWith(i.to + "/"))
    .sort((a, b) => b.to.length - a.to.length)[0]

  return (
    <div className="console flex min-h-svh">
      <Seo title={`${current?.label ?? "Tổng quan"} · Risk Console`} path={pathname} noindex />
      <aside className="sticky top-0 hidden h-svh w-60 shrink-0 flex-col border-r bg-background/40 backdrop-blur md:flex">
        <Link
          to="/console"
          className="flex items-center gap-2.5 px-5 pt-5 pb-6"
        >
          <span className="flex size-9 items-center justify-center rounded-xl bg-primary/15 text-primary shadow-[0_0_20px_-4px_var(--glow)] ring-1 ring-primary/30">
            <ShieldCheck className="size-5" />
          </span>
          <span>
            <span className="block text-sm leading-tight font-semibold">
              Risk Console
            </span>
            <span className="block text-[11px] text-muted-foreground">
              RiskShop · Kiểm soát rủi ro
            </span>
          </span>
        </Link>
        <nav className="flex-1 overflow-y-auto px-3" aria-label="Menu Console">
          {groups.map((g) => (
            <div key={g.title} className="mb-5">
              <p className="mb-1.5 px-2 text-[10px] font-medium tracking-[0.14em] text-muted-foreground/80 uppercase">
                {g.title}
              </p>
              <ul className="grid gap-0.5">
                {g.items.map((item) => (
                  <li key={item.to}>
                    <SideLink
                      item={item}
                      count={item.badge ? badges[item.badge] : 0}
                    />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
        {user && (
          <div className="m-3 flex items-center gap-3 rounded-xl border bg-muted/40 p-3">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-xs font-semibold text-primary">
              {user.full_name.slice(0, 1)}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm">{user.full_name}</span>
              <span className="block text-[11px] text-muted-foreground">
                {ROLE_LABELS[user.role]}
              </span>
            </span>
            <button
              type="button"
              aria-label="Đăng xuất"
              title="Đăng xuất"
              disabled={logout.isPending}
              onClick={() =>
                logout.mutate(undefined, {
                  onSuccess: () => navigate("/login"),
                })
              }
              className="flex size-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <LogOut className="size-4" />
            </button>
          </div>
        )}
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/70 px-4 backdrop-blur-md sm:px-6">
          <span className="font-semibold md:hidden">Risk Console</span>
          <QuickJump />
          <div className="ml-auto flex items-center gap-2 text-sm">
            <SystemStatus />
            <Link
              to="/"
              className="hidden items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs text-muted-foreground transition hover:border-primary/40 hover:text-foreground sm:flex"
            >
              <Store className="size-3.5" /> Xem Shop
            </Link>
            <button
              type="button"
              aria-label="Đăng xuất"
              onClick={() =>
                logout.mutate(undefined, {
                  onSuccess: () => navigate("/login"),
                })
              }
              className="flex size-8 items-center justify-center rounded-lg text-muted-foreground hover:bg-muted md:hidden"
            >
              <LogOut className="size-4" />
            </button>
          </div>
        </header>
        {/* Điện thoại: thanh bên bị ẩn, thay bằng hàng menu cuộn ngang */}
        <nav
          aria-label="Menu Console"
          className="flex [scrollbar-width:none] gap-1 overflow-x-auto border-b px-3 py-2 text-sm md:hidden"
        >
          {groups.flatMap((g) => g.items).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  "shrink-0 rounded-full px-3 py-1.5 whitespace-nowrap text-muted-foreground hover:bg-muted",
                  isActive && "bg-primary/15 text-foreground"
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {/* key theo đường dẫn: đổi trang là nội dung mới mờ dần vào (.page-in), dữ liệu vẫn lấy từ bộ nhớ đệm */}
          <div key={pathname} className="page-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

function SideLink({ item, count }: { item: NavItem; count: number }) {
  const Icon = item.icon
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        cn(
          "group relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted/70 hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
          isActive && "bg-primary/10 text-foreground"
        )
      }
    >
      {({ isActive }) => (
        <>
          {/* Vạch sáng bên trái đánh dấu trang đang mở */}
          <span
            aria-hidden
            className={cn(
              "absolute top-1.5 bottom-1.5 left-0 w-0.5 rounded-full bg-primary opacity-0 transition-opacity",
              isActive && "opacity-100 shadow-[0_0_8px_var(--glow)]"
            )}
          />
          <Icon className={cn("size-4", isActive && "text-primary")} />
          <span className="flex-1">{item.label}</span>
          {count > 0 && (
            <span
              className="min-w-5 rounded-full bg-[#ec835a]/20 px-1.5 text-center text-[11px] leading-5 font-medium text-[#f3a283] tabular-nums"
              aria-label={`${count} việc chờ xử lý`}
            >
              {count}
            </span>
          )}
        </>
      )}
    </NavLink>
  )
}

// Ô "nhảy nhanh": gõ mã case (CS…) hoặc mã khiếu nại (AP…) rồi Enter để mở thẳng trang chi tiết
function QuickJump() {
  const navigate = useNavigate()
  const [code, setCode] = useState("")
  const [hint, setHint] = useState<string | null>(null)

  function submit(e: FormEvent) {
    e.preventDefault()
    const c = code.trim().toUpperCase()
    if (c.startsWith("CS")) navigate(`/console/cases/${c}`)
    else if (c.startsWith("AP")) navigate(`/console/appeals/${c}`)
    else {
      setHint("Nhập mã case (CS…) hoặc mã khiếu nại (AP…)")
      return
    }
    setCode("")
    setHint(null)
  }

  return (
    <form
      onSubmit={submit}
      className="relative hidden max-w-sm flex-1 sm:block"
      role="search"
    >
      <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
      <input
        value={code}
        onChange={(e) => {
          setCode(e.target.value)
          setHint(null)
        }}
        aria-label="Mở nhanh theo mã case hoặc mã khiếu nại"
        placeholder="Mở nhanh: mã case CS… hoặc khiếu nại AP…"
        className="h-9 w-full rounded-lg border bg-muted/40 pr-3 pl-9 text-sm outline-none placeholder:text-muted-foreground focus-visible:border-primary/60 focus-visible:ring-2 focus-visible:ring-primary/30"
      />
      {hint && (
        <p
          className="absolute top-full left-0 mt-1 rounded-md border bg-popover px-2 py-1 text-xs"
          role="alert"
        >
          {hint}
        </p>
      )}
    </form>
  )
}

function SystemStatus() {
  const health = useHealth()
  const ok = health.isSuccess
  return (
    <span
      className="flex items-center gap-2 rounded-lg border px-2.5 py-1.5 text-xs text-muted-foreground"
      role="status"
      title={
        ok
          ? "API và cơ sở dữ liệu hoạt động bình thường"
          : "Không kết nối được API hoặc cơ sở dữ liệu"
      }
    >
      <span className="relative flex size-2" aria-hidden>
        {ok && (
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-[#0ca30c] opacity-60 motion-reduce:animate-none" />
        )}
        <span
          className={cn(
            "relative inline-flex size-2 rounded-full",
            ok ? "bg-[#0ca30c]" : "bg-[#d03b3b]"
          )}
        />
      </span>
      <span className="hidden lg:inline">
        {ok ? "Hệ thống ổn định" : "Mất kết nối"}
      </span>
    </span>
  )
}
