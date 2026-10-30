import { Link, NavLink, Outlet, useNavigate } from "react-router"

import { Button } from "@/components/ui/button"
import { ROLE_LABELS, useLogout, useMe } from "@/lib/api/auth"
import { cn } from "@/lib/utils"

// Các mục menu theo kịch bản demo. Mục chưa làm thì hiện mờ (ready: false).
const NAV_ITEMS = [
  { to: "/console", label: "Tổng quan", ready: true, end: true },
  { to: "/console/monitor", label: "Live Monitor", ready: false },
  { to: "/console/cases", label: "Case", ready: false },
  { to: "/console/rules", label: "Luật rủi ro", ready: false },
  { to: "/console/lab", label: "Attack Lab", ready: false },
  { to: "/console/reports", label: "Báo cáo", ready: false },
  { to: "/console/audit", label: "Audit Log", ready: false },
]

export function ConsoleLayout() {
  const { data: user } = useMe()
  const logout = useLogout()
  const navigate = useNavigate()

  return (
    <div className="flex min-h-svh">
      <aside className="hidden w-56 shrink-0 border-r bg-muted/30 p-4 md:block">
        <Link to="/console" className="block px-2 text-lg font-semibold tracking-tight">
          Risk Console
        </Link>
        <nav className="mt-6 grid gap-1 text-sm">
          {NAV_ITEMS.map((item) =>
            item.ready ? (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    "rounded-md px-2 py-1.5 hover:bg-muted",
                    isActive && "bg-muted font-medium text-foreground",
                  )
                }
              >
                {item.label}
              </NavLink>
            ) : (
              <span key={item.to} className="cursor-not-allowed rounded-md px-2 py-1.5 text-muted-foreground/60">
                {item.label} <span className="text-xs">(sắp có)</span>
              </span>
            ),
          )}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between gap-4 border-b px-4">
          <span className="font-semibold md:hidden">Risk Console</span>
          <div className="ml-auto flex items-center gap-3 text-sm">
            {user && (
              <span className="hidden text-muted-foreground sm:inline">
                {user.full_name} · {ROLE_LABELS[user.role]}
              </span>
            )}
            <Button variant="outline" size="sm" asChild>
              <Link to="/">Xem Shop</Link>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              disabled={logout.isPending}
              onClick={() => logout.mutate(undefined, { onSuccess: () => navigate("/login") })}
            >
              Đăng xuất
            </Button>
          </div>
        </header>
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
