import { useEffect } from "react"
import { useLocation } from "react-router"

import { scrollToElement, scrollToTopNow } from "@/lib/smooth-scroll"

// Mỗi khi đổi trang (đổi pathname), cuộn lên đầu. Chỉ đổi bộ lọc (?q=..., ?page=...) thì giữ nguyên vị trí.
// Có #neo trên URL (ví dụ /#uu-dai) thì cuộn tới phần tử đó; đợi một khung hình để trang kịp vẽ.
export function ScrollToTop() {
  const { pathname, hash } = useLocation()
  useEffect(() => {
    if (!hash) {
      scrollToTopNow()
      return
    }
    const id = requestAnimationFrame(() => {
      const el = document.getElementById(hash.slice(1))
      if (el) scrollToElement(el)
    })
    return () => cancelAnimationFrame(id)
  }, [pathname, hash])
  return null
}
