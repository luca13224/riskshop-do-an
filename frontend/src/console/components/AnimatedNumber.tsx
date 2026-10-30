import { useEffect, useRef, useState } from "react"

// Số chạy từ giá trị cũ tới giá trị mới (~0,7 giây) khi dữ liệu đổi, giúp mắt bắt được "số vừa thay đổi".
// Người dùng bật giảm chuyển động thì hiện ngay giá trị mới.
export function AnimatedNumber({
  value,
  format = (v) => Math.round(v).toLocaleString("vi-VN"),
  duration = 700,
}: {
  value: number
  format?: (v: number) => string
  duration?: number
}) {
  const [shown, setShown] = useState(value)
  const from = useRef(value)

  useEffect(() => {
    const start = from.current
    if (
      start === value ||
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    ) {
      from.current = value
      const id = requestAnimationFrame(() => setShown(value))
      return () => cancelAnimationFrame(id)
    }
    let raf = 0
    const t0 = performance.now()
    const tick = (t: number) => {
      const p = Math.min(1, (t - t0) / duration)
      const eased = 1 - (1 - p) ** 3
      setShown(start + (value - start) * eased)
      if (p < 1) raf = requestAnimationFrame(tick)
      else from.current = value
    }
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      from.current = value
    }
  }, [value, duration])

  return <span className="tabular-nums">{format(shown)}</span>
}
