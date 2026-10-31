import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ElementType,
  type ReactNode,
  type RefObject,
} from "react"

import { cn } from "@/lib/utils"

// Báo khi phần tử lọt vào màn hình (IntersectionObserver: API có sẵn của trình duyệt, không tốn
// công đo vị trí mỗi lần cuộn). once=true: đã hiện thì giữ nguyên, không ẩn lại khi cuộn ngược.
export function useInView<T extends Element>(
  ref: RefObject<T | null>,
  { once = true, margin = "0px 0px -12% 0px" } = {}
) {
  const [inView, setInView] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true)
          if (once) io.disconnect()
        } else if (!once) setInView(false)
      },
      { rootMargin: margin }
    )
    io.observe(el)
    return () => io.disconnect()
  }, [ref, once, margin])
  return inView
}

type Variant = "up" | "left" | "zoom" | "fade"

// Bọc một khối để nó "bước vào" khi lăn tới. CSS ở index.css (.reveal), tự tắt khi giảm chuyển động.
export function Reveal({
  as: Tag = "div",
  variant = "up",
  delay = 0,
  className,
  style,
  children,
  ...rest
}: {
  as?: ElementType
  variant?: Variant
  delay?: number
  className?: string
  style?: CSSProperties
  children?: ReactNode
  id?: string
  "aria-labelledby"?: string
  "aria-label"?: string
}) {
  const ref = useRef<HTMLElement>(null)
  const shown = useInView(ref)
  return (
    <Tag
      ref={ref}
      data-variant={variant}
      data-shown={shown ? "" : undefined}
      className={cn("reveal", className)}
      style={{ "--d": `${delay}ms`, ...style } as CSSProperties}
      {...rest}
    >
      {children}
    </Tag>
  )
}
