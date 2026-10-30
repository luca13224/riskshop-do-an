import { useState } from "react"

import { cn } from "@/lib/utils"

const DAYS = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
const DAY_NAMES = [
  "Thứ Hai",
  "Thứ Ba",
  "Thứ Tư",
  "Thứ Năm",
  "Thứ Sáu",
  "Thứ Bảy",
  "Chủ nhật",
]

// Heatmap thứ × giờ: mỗi ô là số lượt can thiệp trong khung giờ đó (giờ Việt Nam).
// Thang màu tuần tự MỘT sắc độ (xanh cyan nhạt -> đậm), ô bằng 0 để màu nền: đọc ngay khung giờ bị tấn công.
export function Heatmap({ data }: { data: number[][] }) {
  const [hover, setHover] = useState<[number, number] | null>(null)
  const max = Math.max(0, ...data.flat())
  const shade = (v: number) =>
    v === 0
      ? "color-mix(in oklab, var(--foreground) 7%, transparent)" // ô 0: mờ nhưng vẫn thấy lưới
      : `color-mix(in oklab, #38bdf8 ${Math.round(18 + (v / max) * 82)}%, var(--muted))`

  return (
    <div className="grid gap-3">
      <div className="overflow-x-auto pb-1">
        <div
          className="grid min-w-[340px] gap-[3px]"
          style={{ gridTemplateColumns: "28px repeat(24, minmax(0, 1fr))" }}
          onPointerLeave={() => setHover(null)}
        >
          <span />
          {Array.from({ length: 24 }, (_, h) => (
            <span
              key={h}
              className="text-center text-[10px] text-muted-foreground tabular-nums"
            >
              {h % 3 === 0 ? h : ""}
            </span>
          ))}
          {data.map((row, d) => (
            <div key={d} className="contents">
              <span className="flex items-center text-[11px] text-muted-foreground">
                {DAYS[d]}
              </span>
              {row.map((v, h) => (
                <span
                  key={h}
                  role="img"
                  aria-label={`${DAY_NAMES[d]}, ${h} giờ: ${v} lượt can thiệp`}
                  onPointerEnter={() => setHover([d, h])}
                  className={cn(
                    "aspect-square rounded-[3px] outline-1 outline-transparent transition-[outline-color]",
                    hover?.[0] === d &&
                      hover?.[1] === h &&
                      "outline-foreground/60"
                  )}
                  style={{ background: shade(v) }}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
        <p aria-live="polite" className="min-h-4">
          {hover
            ? `${DAY_NAMES[hover[0]]}, ${hover[1]}:00–${hover[1]}:59 · ${data[hover[0]][hover[1]]} lượt can thiệp`
            : max === 0
              ? "Chưa có lượt can thiệp nào trong kỳ"
              : "Rê chuột lên ô để xem chi tiết"}
        </p>
        <div className="flex items-center gap-2">
          <span>0</span>
          <span
            className="h-2 w-28 rounded-full"
            style={{
              background: "linear-gradient(90deg, var(--muted), #38bdf8)",
            }}
            aria-hidden
          />
          <span className="tabular-nums">{max}</span>
        </div>
      </div>
    </div>
  )
}
