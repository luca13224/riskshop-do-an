import Lenis from "lenis"
import { useEffect } from "react"

// Cuộn mượt cho Shop bằng Lenis: con lăn chuột không "giật cục" từng nấc mà trượt có quán tính.
// Lenis vẫn cuộn bằng thanh cuộn thật của trình duyệt, nên các sự kiện scroll khác vẫn chạy bình thường.
// Không bật cho Console (công cụ làm việc cần cuộn nhanh, chính xác) và khi người dùng chọn giảm chuyển động.

let current: Lenis | null = null

export function useSmoothScroll() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return
    const lenis = new Lenis({
      autoRaf: true,
      lerp: 0.12,
      anchors: true, // link #neo cũng cuộn mượt
      // Vùng tự cuộn riêng (hàng cuộn ngang, hộp thoại) giữ cách cuộn gốc: gắn data-lenis-prevent
    })
    current = lenis
    return () => {
      lenis.destroy()
      current = null
    }
  }, [])
}

// Cuộn về đầu trang ngay lập tức (khi đổi trang). Có Lenis thì báo Lenis để nó không "kéo" ngược lại.
export function scrollToTopNow() {
  if (current) current.scrollTo(0, { immediate: true, force: true })
  else window.scrollTo(0, 0)
}

export function scrollToElement(el: Element) {
  if (current) current.scrollTo(el as HTMLElement, { offset: -80 })
  else el.scrollIntoView({ behavior: "smooth" })
}
