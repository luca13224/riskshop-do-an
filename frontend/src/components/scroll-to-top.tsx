import { useEffect } from "react"
import { useLocation } from "react-router"

// Mỗi khi đổi trang (đổi pathname), cuộn lên đầu. Chỉ đổi bộ lọc (?category=...) thì giữ nguyên vị trí.
export function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}
