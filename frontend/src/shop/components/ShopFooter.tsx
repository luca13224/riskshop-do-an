import { ArrowUp } from "lucide-react"
import { useEffect, useRef, type ReactNode, type RefObject } from "react"
import { Link } from "react-router"

import { useCategories } from "@/lib/api/catalog"
import { scrollToTopNow } from "@/lib/smooth-scroll"

// Footer (phần FOOT) kiểu "kéo màn": footer nằm yên phía dưới (sticky, index.css .curtain-footer),
// nội dung trang trượt lên để lộ nó ra. Chữ RISKSHOP cỡ lớn được "tô sáng" dần theo mức footer đã lộ (--p).
export function ShopFooter() {
  const categories = useCategories()
  const ref = useRef<HTMLElement>(null)
  useRevealProgress(ref)

  return (
    <footer ref={ref} className="curtain-footer overflow-hidden bg-[#0a0b0f] text-white/65">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 pt-16 pb-8 sm:grid-cols-2 sm:px-6 lg:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <p className="text-lg font-bold text-white">RiskShop</p>
          <p className="mt-3 max-w-xs text-sm leading-relaxed">
            Sàn đồ công nghệ mô phỏng, có hệ thống kiểm soát rủi ro và ngăn ngừa lạm dụng chính sách chạy
            phía sau mọi đơn hàng.
          </p>
        </div>
        <FooterCol title="Danh mục">
          {categories.data?.map((c) => (
            <li key={c.code}>
              <Link to={`/danh-muc/${c.code}`} className="transition hover:text-white">
                {c.name}
              </Link>
            </li>
          ))}
        </FooterCol>
        <FooterCol title="Mua sắm">
          <li>COD hoặc trả trước</li>
          <li>Mã TANTHU cho khách mới</li>
          <li>Mã GIAM10 giảm 10%, tối đa 100.000đ</li>
          <li>
            <Link to="/appeals" className="transition hover:text-white">
              Gửi khiếu nại
            </Link>
          </li>
        </FooterCol>
        <FooterCol title="Về dự án">
          <li>Đồ án tốt nghiệp, Trường Đại học Thủy Lợi</li>
          <li>Sản phẩm, giá và đơn hàng đều là dữ liệu mô phỏng</li>
        </FooterCol>
      </div>

      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        <p
          aria-hidden
          className="brand-outline text-center text-[clamp(4rem,17vw,15rem)] leading-[0.8] font-black tracking-tighter select-none"
        >
          RISKSHOP
        </p>
      </div>

      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 border-t border-white/10 px-4 py-5 text-xs sm:px-6">
        <p>© 2026 RiskShop · Dữ liệu mô phỏng, không phải cửa hàng thật</p>
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
      <p className="font-semibold text-white">{title}</p>
      <ul className="mt-3 grid gap-2 text-sm">{children}</ul>
    </div>
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

