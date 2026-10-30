// Biểu đồ đường mini trong thẻ KPI: chỉ để thấy xu hướng, không có trục.
// Số liệu chi tiết từng ngày nằm ở biểu đồ lớn và bảng thay thế, nên phần này ẩn với trình đọc màn hình.
// viewBox co giãn theo bề rộng thẻ (preserveAspectRatio="none"); nét vẽ giữ đúng 2px nhờ
// vector-effect, còn chấm cuối là thẻ HTML riêng để không bị méo thành hình bầu dục.
export function Sparkline({
  values,
  color = "var(--series-1)",
  height = 32,
}: {
  values: number[]
  color?: string
  height?: number
}) {
  if (values.length < 2) return null
  const max = Math.max(...values)
  const min = Math.min(...values)
  const span = max - min || 1
  const pad = 3 // chừa chỗ cho nét vẽ ở mép trên/dưới
  const pts = values.map((v, i) => {
    const x = (i / (values.length - 1)) * 100
    const y = pad + (1 - (v - min) / span) * (height - pad * 2)
    return [x, y] as const
  })
  const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x},${y}`).join(" ")
  const last = pts[pts.length - 1]

  return (
    <div className="viz relative" style={{ height }} aria-hidden>
      <svg
        viewBox={`0 0 100 ${height}`}
        preserveAspectRatio="none"
        className="size-full overflow-visible"
      >
        {/* Vùng tô nhạt (~10%) dưới đường */}
        <path
          d={`${line} L100,${height} L0,${height} Z`}
          fill={color}
          opacity={0.1}
        />
        <path
          d={line}
          fill="none"
          stroke={color}
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      <span
        className="absolute size-2 -translate-x-1/2 -translate-y-1/2 rounded-full ring-2 ring-card"
        style={{ left: "100%", top: last[1], background: color }}
      />
    </div>
  )
}
