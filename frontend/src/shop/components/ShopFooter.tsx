import { ArrowUp, BadgeCheck, RotateCcw, Truck } from "lucide-react"
import { useEffect, useRef, type ReactNode, type RefObject } from "react"
import { Link } from "react-router"

import { useMe } from "@/lib/api/auth"
import { useCategories } from "@/lib/api/catalog"
import { scrollToTopNow } from "@/lib/smooth-scroll"

// Footer (phần FOOT) kiểu "kéo màn": footer nằm yên phía dưới (sticky, index.css .curtain-footer),
// nội dung trang trượt lên để lộ nó ra. Chữ RISKSHOP cỡ lớn được tô màu dần theo mức footer đã lộ (--p).
// Mọi link đều trỏ tới trang có thật trong hệ thống: không đặt link "Điều khoản", "Hotline"... khi chưa có.
export function ShopFooter() {
  const categories = useCategories()
  const { data: user } = useMe()
  const ref = useRef<HTMLElement>(null)
  useRevealProgress(ref)

  return (
    <footer ref={ref} className="curtain-footer overflow-hidden bg-[#0a0b0f] text-white/60">
      <div className="mx-auto grid max-w-7xl gap-x-8 gap-y-10 px-4 pt-16 pb-10 sm:grid-cols-3 sm:px-6 lg:grid-cols-[1.6fr_1fr_1fr_1fr]">
        <div className="sm:col-span-3 lg:col-span-1">
          <Link to="/" className="inline-flex items-center gap-2 text-white" aria-label="RiskShop, về trang chủ">
            <span className="flex size-8 items-center justify-center rounded-xl bg-white">
              <span className="size-2.5 rounded-full bg-buy" aria-hidden />
            </span>
            <span className="text-lg font-bold tracking-tight">RiskShop</span>
          </Link>
          <p className="mt-4 max-w-sm text-sm leading-relaxed">
            Đồ công nghệ chọn lọc cho góc làm việc và giải trí. Mỗi đơn hàng đều được kiểm tra an toàn trước khi
            giao.
          </p>
          <ul className="mt-6 grid max-w-sm gap-2.5 text-sm text-white/75">
            <Perk icon={Truck}>Giao hàng toàn quốc</Perk>
            <Perk icon={RotateCcw}>Đổi trả trong 7 ngày</Perk>
            <Perk icon={BadgeCheck}>Thanh toán khi nhận hàng hoặc trả trước</Perk>
          </ul>
        </div>

        <FooterCol title="Sản phẩm">
          <FooterLink to="/danh-muc">Tất cả sản phẩm</FooterLink>
          {categories.data?.map((c) => (
            <FooterLink key={c.code} to={`/danh-muc/${c.code}`}>
              {c.name}
            </FooterLink>
          ))}
        </FooterCol>

        <FooterCol title="Tài khoản">
          {user ? (
            <>
              <FooterLink to="/orders">Đơn hàng của tôi</FooterLink>
              <FooterLink to="/cart">Giỏ hàng</FooterLink>
            </>
          ) : (
            <>
              <FooterLink to="/login">Đăng nhập</FooterLink>
              <FooterLink to="/register">Tạo tài khoản</FooterLink>
            </>
          )}
          <FooterLink to="/appeals">Gửi khiếu nại</FooterLink>
        </FooterCol>

        <FooterCol title="Ưu đãi">
          <li>
            <Link to="/#uu-dai" className="group block transition hover:text-white">
              <span className="font-mono font-semibold text-buy">TANTHU</span>
              <span className="block text-xs">Giảm 50.000đ cho khách mới</span>
            </Link>
          </li>
          <li>
            <Link to="/#uu-dai" className="group block transition hover:text-white">
              <span className="font-mono font-semibold text-buy">GIAM10</span>
              <span className="block text-xs">Giảm 10%, tối đa 100.000đ</span>
            </Link>
          </li>
        </FooterCol>
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <p
          aria-hidden
          className="brand-fill text-center text-[clamp(4rem,17vw,15rem)] leading-[0.8] font-black tracking-tighter select-none"
        >
          RISKSHOP
        </p>
      </div>

      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 border-t border-white/10 px-4 py-5 text-xs sm:px-6">
        <p>© 2026 RiskShop. Bảo lưu mọi quyền.</p>
        <button
          type="button"
          onClick={scrollToTopNow}
          className="flex items-center gap-2 rounded-full border border-white/15 px-3 py-1.5 transition hover:bg-white/10 hover:text-white"
        >
          <ArrowUp className="size-3.5" /> Lên đầu trang
        </button>
      </div>
    </footer>
  )
}

function FooterCol({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <p className="text-sm font-semibold text-white">{title}</p>
      <ul className="mt-4 grid gap-2.5 text-sm">{children}</ul>
    </div>
  )
}

function FooterLink({ to, children }: { to: string; children: string }) {
  return (
    <li>
      <Link to={to} className="transition hover:text-white">
        {children}
      </Link>
    </li>
  )
}

function Perk({ icon: Icon, children }: { icon: typeof Truck; children: string }) {
  return (
    <li className="flex items-center gap-2.5">
      <Icon className="size-4 shrink-0 text-buy" />
      {children}
    </li>
  )
}

// Ghi --p (0 → 1) lên footer: footer đã lộ ra bao nhiêu phần. Footer "dính" đáy màn hình nên không đo
// được vị trí của chính nó; thay vào đó đo đáy của lớp nội dung (data-curtain) đang trượt lên.
function useRevealProgress(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const footer = ref.current
    const content = document.querySelector("[data-curtain]")
    if (!footer || !content) return
    let raf = 0
    function update() {
      raf = 0
      const shown = window.innerHeight - content!.getBoundingClientRect().bottom
      const p = Math.min(1, Math.max(0, shown / footer!.offsetHeight))
      footer!.style.setProperty("--p", p.toFixed(3))
    }
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update)
    }
    update()
    window.addEventListener("scroll", onScroll, { passive: true })
    window.addEventListener("resize", onScroll)
    return () => {
      window.removeEventListener("scroll", onScroll)
      window.removeEventListener("resize", onScroll)
      cancelAnimationFrame(raf)
    }
  }, [ref])
}
