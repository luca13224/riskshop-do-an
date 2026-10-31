import { Outlet, useLocation } from "react-router"

import { useSmoothScroll } from "@/lib/smooth-scroll"
import { cn } from "@/lib/utils"
import { ShopFooter } from "@/shop/components/ShopFooter"
import { ShopHeader } from "@/shop/components/ShopHeader"
import { ShopSeo } from "@/shop/ShopSeo"

// Khung chung của khu vực Shop. Lớp .shop (index.css) giữ Shop luôn ở tông sáng (ADR-005).
// Bố cục HEAD / BODY / FOOT: header (ShopHeader) và nội dung nằm trong một "tấm màn" (data-curtain)
// trượt lên trên footer khi cuộn tới cuối trang (ShopFooter).
export function ShopLayout() {
  useSmoothScroll()
  const isHome = useLocation().pathname === "/"

  return (
    <div className="shop flex min-h-svh flex-col overflow-x-clip">
      <ShopSeo />
      <div
        data-curtain
        className="curtain-content flex flex-1 flex-col border-b border-white/[.06] bg-background pb-20 shadow-[0_40px_80px_-30px_rgba(0,0,0,.9)] md:rounded-b-[2.5rem] md:pb-28"
      >
        {/* Trang chủ mở đầu bằng "phòng chiếu" tối, nên thanh thông báo cũng tối theo (nhấn cyan, ADR-005) */}
        <p
          className={cn(
            "px-4 py-2 text-center text-xs font-medium sm:text-sm",
            isHome ? "border-b border-white/5 bg-background text-white/70" : "bg-buy text-buy-foreground"
          )}
        >
          Khách mới nhập mã <b className={isHome ? "text-cyan-300" : undefined}>NGUOIMOI</b> giảm 50.000đ cho
          đơn từ 200.000đ
        </p>

        <ShopHeader />

        <main className="mx-auto w-full max-w-7xl flex-1 px-4 sm:px-6">
          <Outlet />
        </main>
      </div>

      <ShopFooter />
    </div>
  )
}
