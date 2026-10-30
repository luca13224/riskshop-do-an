import { useEffect } from "react"
import { useLocation } from "react-router"

// Mỗi khi đổi trang (đổi pathname), cuộn lên đầu. Chỉ đổi bộ lọc (?category=...) thì giữ nguyên vị trí.
// Có #neo trên URL (ví dụ /#san-pham) thì cuộn tới phần tử đó; đợi một khung hình để trang kịp vẽ.
export function ScrollToTop() {
  const { pathname, hash } = useLocation()
  useEffect(() => {
    if (!hash) {
      window.scrollTo(0, 0)
      return
    }
    const id = requestAnimationFrame(() =>
      document
        .getElementById(hash.slice(1))
        ?.scrollIntoView({ behavior: "smooth" })
    )
    return () => cancelAnimationFrame(id)
  }, [pathname, hash])
  return null
}
