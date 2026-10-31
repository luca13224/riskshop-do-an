import type { ReactNode } from "react"

import { Skeleton } from "@/components/ui/skeleton"

// Mảnh giao diện nhỏ dùng chung giữa trang chủ và trang danh mục

export function SectionHeading({
  id,
  eyebrow,
  children,
}: {
  id: string
  eyebrow?: string
  children: ReactNode
}) {
  return (
    <div>
      {eyebrow && (
        <p className="text-xs font-semibold tracking-[0.2em] text-muted-foreground uppercase">{eyebrow}</p>
      )}
      <h2 id={id} className="mt-2 text-2xl font-semibold tracking-tight text-balance sm:text-4xl">
        {children}
      </h2>
    </div>
  )
}

export function RoundButton({
  label,
  onClick,
  disabled,
  children,
}: {
  label: string
  onClick: () => void
  disabled?: boolean
  children: ReactNode
}) {
  return (
    <button
      type="button"
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
      className="flex size-11 items-center justify-center rounded-full border bg-background transition hover:bg-buy hover:text-buy-foreground disabled:pointer-events-none disabled:opacity-40"
    >
      {children}
    </button>
  )
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4" aria-busy="true" aria-label="Đang tải">
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} className="aspect-[3/4] w-full rounded-3xl" />
      ))}
    </div>
  )
}
