import { useEffect, useRef, useState } from "react"

import { cn } from "@/lib/utils"

// Biểu đồ cột theo ngày, vẽ bằng SVG tự viết (không cần thư viện biểu đồ).
// Hỗ trợ cột chồng (nhiều chuỗi). Theo quy tắc của skill dataviz:
//   - cột rộng tối đa 24px, bo 4px ở đầu cột, vuông ở đáy; các đoạn chồng cách nhau 2px
//   - một trục y duy nhất, đường lưới mảnh; nhãn chữ dùng màu chữ, không dùng màu dữ liệu
//   - từ 2 chuỗi trở lên luôn có chú thích (legend); rê chuột/focus từng ngày có tooltip
//   - luôn có bảng số liệu thay thế (người đọc màn hình, khi in báo cáo)

export interface Series {
  key: string
  label: string
  color: string // giá trị CSS, ví dụ "var(--series-1)"
}

interface Props {
  data: ({ date: string } & Record<string, number | string>)[]
  series: Series[]
  height?: number
  format?: (v: number) => string
  emptyText?: string
  xLabel?: (key: string) => string // nhãn trục x; mặc định coi key là ngày "YYYY-MM-DD"
  xTitle?: string // tên cột đầu của bảng thay thế
}

const M = { top: 10, right: 18, bottom: 22, left: 44 } // lề phải đủ cho nửa nhãn ngày cuối
const GAP = 2

export function ColumnChart({
  data,
  series,
  height = 220,
  format = (v) => v.toLocaleString("vi-VN"),
  emptyText = "Chưa có dữ liệu trong khoảng này",
  xLabel = shortDate,
  xTitle = "Ngày",
}: Props) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(600)
  const [hover, setHover] = useState<number | null>(null)

  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => setWidth(e.contentRect.width))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const totals = data.map((d) =>
    series.reduce((s, x) => s + Number(d[x.key] ?? 0), 0)
  )
  const max = Math.max(0, ...totals)
  const { top: yMax, step } = niceScale(max)
  const plotW = Math.max(10, width - M.left - M.right)
  const plotH = height - M.top - M.bottom
  const band = plotW / Math.max(1, data.length)
  const barW = Math.min(24, band * 0.62)
  const y = (v: number) => M.top + plotH - (v / yMax) * plotH
  const labelEvery = Math.ceil(data.length / 7)

  return (
    // minmax(0,1fr): ô lưới không bị SVG đẩy rộng ra, nên ResizeObserver đo được bề rộng thật của thẻ
    <div className="viz grid min-w-0 grid-cols-[minmax(0,1fr)] gap-3">
      {series.length > 1 && (
        <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
          {series.map((s) => (
            <li key={s.key} className="flex items-center gap-1.5">
              <span
                className="size-2.5 rounded-sm"
                style={{ background: s.color }}
                aria-hidden
              />
              {s.label}
            </li>
          ))}
        </ul>
      )}

      <div
        ref={wrapRef}
        className="relative"
        onPointerLeave={() => setHover(null)}
      >
        <svg
          width={width}
          height={height}
          className="block overflow-visible"
          aria-hidden
        >
          {/* Lưới ngang + nhãn trục y */}
          {Array.from(
            { length: Math.round(yMax / step) + 1 },
            (_, i) => i * step
          ).map((v) => (
            <g key={v}>
              <line
                x1={M.left}
                x2={width - M.right}
                y1={y(v)}
                y2={y(v)}
                stroke="var(--grid)"
              />
              <text
                x={M.left - 8}
                y={y(v)}
                textAnchor="end"
                dominantBaseline="middle"
                className="fill-muted-foreground text-[11px] tabular-nums"
              >
                {compact(v, format)}
              </text>
            </g>
          ))}

          {data.map((d, i) => {
            const cx = M.left + band * i + band / 2
            let base = 0
            const values = series.map((s) => Number(d[s.key] ?? 0))
            const lastNonZero = values.findLastIndex((v) => v > 0)
            return (
              <g
                key={d.date}
                opacity={hover === null || hover === i ? 1 : 0.45}
                // Cột mọc lên lần lượt khi biểu đồ xuất hiện (tắt nếu người dùng chọn giảm chuyển động)
                className="bar-grow transition-opacity"
                style={{ animationDelay: `${Math.min(i * 25, 500)}ms` }}
              >
                {series.map((s, k) => {
                  const v = values[k]
                  if (v <= 0) return null
                  const y0 = y(base)
                  base += v
                  let h = Math.max(2, y0 - y(base)) // giá trị > 0 thì ít nhất 2px để còn nhìn thấy
                  const isTop = k === lastNonZero
                  if (!isTop) h = Math.max(0.5, h - GAP) // chừa khe 2px cho đoạn phía trên
                  return (
                    <path
                      key={s.key}
                      d={roundedTop(
                        cx - barW / 2,
                        y0 - h,
                        barW,
                        h,
                        isTop ? 4 : 0
                      )}
                      fill={s.color}
                    />
                  )
                })}
              </g>
            )
          })}

          {/* Nhãn trục x: thưa bớt khi nhiều ngày */}
          {data.map((d, i) =>
            i % labelEvery === 0 || i === data.length - 1 ? (
              <text
                key={d.date}
                x={M.left + band * i + band / 2}
                y={height - 6}
                textAnchor="middle"
                className="fill-muted-foreground text-[11px]"
              >
                {xLabel(d.date)}
              </text>
            ) : null
          )}
        </svg>

        {/* Vùng bắt chuột/focus cho từng ngày: rộng cả cột, dễ trỏ hơn thân cột mảnh */}
        {data.map((d, i) => (
          <button
            key={d.date}
            type="button"
            tabIndex={0}
            aria-label={`${xLabel(d.date)}: ${series
              .map((s) => `${s.label} ${format(Number(d[s.key] ?? 0))}`)
              .join(", ")}`}
            className="absolute cursor-default rounded-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            style={{
              left: M.left + band * i,
              top: M.top,
              width: band,
              height: plotH,
            }}
            onPointerEnter={() => setHover(i)}
            onFocus={() => setHover(i)}
            onBlur={() => setHover(null)}
          />
        ))}

        {hover !== null && data[hover] && (
          <div
            role="status"
            className="pointer-events-none absolute top-0 z-10 min-w-36 rounded-lg border bg-popover px-3 py-2 text-xs shadow-md"
            style={{
              left: Math.min(
                Math.max(M.left + band * hover + band / 2, 80),
                width - 80
              ),
              transform: "translateX(-50%)",
            }}
          >
            <p className="mb-1 text-muted-foreground">
              {xLabel(data[hover].date)}
            </p>
            {series.map((s) => (
              <p key={s.key} className="flex items-center gap-2">
                <span
                  className="h-0.5 w-3 rounded-full"
                  style={{ background: s.color }}
                  aria-hidden
                />
                <b className="tabular-nums">
                  {format(Number(data[hover][s.key] ?? 0))}
                </b>
                <span className="text-muted-foreground">{s.label}</span>
              </p>
            ))}
          </div>
        )}

        {max === 0 && (
          <p className="absolute inset-0 flex items-center justify-center text-sm text-muted-foreground">
            {emptyText}
          </p>
        )}
      </div>

      <details className="text-xs">
        <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
          Xem dạng bảng
        </summary>
        <div className="mt-2 max-h-56 overflow-auto rounded-md border">
          <table className="w-full text-left tabular-nums">
            <thead className="sticky top-0 bg-muted">
              <tr>
                <th className="px-2 py-1 font-medium">{xTitle}</th>
                {series.map((s) => (
                  <th key={s.key} className="px-2 py-1 text-right font-medium">
                    {s.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((d) => (
                <tr key={d.date} className={cn("border-t")}>
                  <td className="px-2 py-1">{xLabel(d.date)}</td>
                  {series.map((s) => (
                    <td key={s.key} className="px-2 py-1 text-right">
                      {format(Number(d[s.key] ?? 0))}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  )
}

// "2026-10-31" -> "31/10"
function shortDate(iso: string) {
  const [, m, d] = iso.split("-")
  return `${d}/${m}`
}

// Trục y "tròn số": chia khoảng [0, max] thành ~4 bước 1/2/2,5/5 x 10^n
function niceScale(max: number) {
  if (max <= 0) return { top: 4, step: 1 }
  const rough = max / 4
  const mag = 10 ** Math.floor(Math.log10(rough))
  const step =
    [1, 2, 2.5, 5, 10].map((f) => f * mag).find((s) => s >= rough) ?? 10 * mag
  return { top: Math.ceil(max / step) * step, step }
}

// Nhãn trục gọn: 1.200.000 -> 1,2 tr ; 15.000 -> 15 N
function compact(v: number, format: (v: number) => string) {
  if (v >= 1_000_000)
    return `${(v / 1_000_000).toLocaleString("vi-VN", { maximumFractionDigits: 1 })} tr`
  if (v >= 10_000) return `${Math.round(v / 1000)} N`
  return Number.isInteger(v) ? v.toLocaleString("vi-VN") : format(v)
}

// Hình chữ nhật bo tròn 2 góc trên (đầu cột), vuông ở đáy
function roundedTop(x: number, y: number, w: number, h: number, r: number) {
  const rr = Math.min(r, h, w / 2)
  return `M${x},${y + h} V${y + rr} Q${x},${y} ${x + rr},${y} H${x + w - rr} Q${x + w},${y} ${x + w},${y + rr} V${y + h} Z`
}
