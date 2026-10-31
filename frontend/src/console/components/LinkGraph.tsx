import { Globe, MapPin, Smartphone, type LucideIcon } from "lucide-react"
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from "react"

import { Skeleton } from "@/components/ui/skeleton"
import {
  DECISION_LABELS,
  useLinkGraph,
  type GraphNode,
  type LinkGraph as Graph,
} from "@/lib/api/risk"
import { cn } from "@/lib/utils"

// ---------------------------------------------------------------------------------------------
// Sơ đồ mạng lưới tài khoản <-> điểm chung (thiết bị, IP, địa chỉ giao hàng).
//
// Bố trí bằng mô phỏng lực (force-directed), tự viết, không dùng thư viện:
//   - mọi cặp nút ĐẨY nhau (như nam châm cùng cực), lực tỉ lệ 1/khoảng cách²
//   - mỗi cạnh KÉO hai đầu về một độ dài mong muốn (như lò xo)
//   - một lực nhẹ kéo tất cả về giữa khung để đồ thị không trôi đi
// Mỗi bước cập nhật vận tốc, rồi giảm dần (damping) cho tới khi đồ thị đứng yên.
// Chạy dần qua nhiều khung hình nên người xem thấy mạng lưới "bung" ra; ai bật giảm chuyển động
// thì tính xong một lần rồi vẽ luôn.
// ---------------------------------------------------------------------------------------------
const W = 760
const H = 440
const TICKS = 320
const PER_FRAME = 8
const SPRING = 115 // độ dài lò xo mong muốn (px)

type Pos = { x: number; y: number; vx: number; vy: number }
type Layout = Map<string, { x: number; y: number }>

// Bản chụp toạ độ để vẽ (React chỉ đọc bản chụp, còn mô phỏng thì sửa bản gốc trong ref)
const snapshot = (pos: Map<string, Pos>): Layout =>
  new Map([...pos].map(([id, p]) => [id, { x: p.x, y: p.y }]))

const ENTITY: Record<
  "device" | "ip" | "address",
  { icon: LucideIcon; label: string }
> = {
  device: { icon: Smartphone, label: "Thiết bị" },
  ip: { icon: Globe, label: "IP" },
  address: { icon: MapPin, label: "Địa chỉ giao hàng" },
}
const DECISION_COLOR: Record<string, string> = {
  ALLOW: "var(--st-good)",
  ALLOW_WITH_RESTRICTION: "var(--st-warning)",
  REVIEW: "var(--st-serious)",
  BLOCK: "var(--st-critical)",
}

function initial(graph: Graph): Map<string, Pos> {
  // Vị trí ban đầu xếp vòng tròn theo thứ tự (không ngẫu nhiên) để lần nào mở cũng ra cùng một hình
  const m = new Map<string, Pos>()
  graph.nodes.forEach((n, i) => {
    const a = (i / graph.nodes.length) * Math.PI * 2
    const r = n.id === graph.root ? 0 : 140 + (i % 3) * 30
    m.set(n.id, {
      x: W / 2 + r * Math.cos(a),
      y: H / 2 + r * Math.sin(a),
      vx: 0,
      vy: 0,
    })
  })
  return m
}

function step(graph: Graph, pos: Map<string, Pos>, pinned: string | null) {
  const ids = graph.nodes.map((n) => n.id)
  for (let i = 0; i < ids.length; i++) {
    const a = pos.get(ids[i])!
    for (let j = i + 1; j < ids.length; j++) {
      const b = pos.get(ids[j])!
      const dx = a.x - b.x
      const dy = a.y - b.y
      const d2 = Math.max(dx * dx + dy * dy, 30)
      const f = 7000 / d2 // lực đẩy
      const d = Math.sqrt(d2)
      a.vx += (dx / d) * f
      a.vy += (dy / d) * f
      b.vx -= (dx / d) * f
      b.vy -= (dy / d) * f
    }
  }
  for (const e of graph.edges) {
    const a = pos.get(e.source)
    const b = pos.get(e.target)
    if (!a || !b) continue
    const dx = b.x - a.x
    const dy = b.y - a.y
    const d = Math.max(Math.sqrt(dx * dx + dy * dy), 1)
    const f = (d - SPRING) * 0.04 // lực lò xo
    a.vx += (dx / d) * f
    a.vy += (dy / d) * f
    b.vx -= (dx / d) * f
    b.vy -= (dy / d) * f
  }
  for (const id of ids) {
    const p = pos.get(id)!
    if (id === pinned) {
      p.vx = p.vy = 0
      continue
    }
    p.vx += (W / 2 - p.x) * 0.0035 // kéo về giữa
    p.vy += (H / 2 - p.y) * 0.0035
    p.vx *= 0.82 // giảm dần để đồ thị dừng lại
    p.vy *= 0.82
    p.x = Math.min(W - 24, Math.max(24, p.x + p.vx))
    p.y = Math.min(H - 24, Math.max(24, p.y + p.vy))
  }
}

export function LinkGraphPanel({ userId }: { userId: number }) {
  const graph = useLinkGraph(userId)
  if (graph.isPending) return <Skeleton className="h-[440px] rounded-xl" />
  if (graph.isError)
    return <p className="text-sm text-destructive">{graph.error.message}</p>
  return <LinkGraphView key={userId} graph={graph.data} />
}

function LinkGraphView({ graph }: { graph: Graph }) {
  const sim = useRef<Map<string, Pos> | null>(null) // toạ độ + vận tốc đang được mô phỏng
  const [layout, setLayout] = useState<Layout>(() => snapshot(initial(graph)))
  const [hover, setHover] = useState<GraphNode | null>(null)
  const dragging = useRef<string | null>(null)
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    const pos = initial(graph)
    sim.current = pos
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    if (reduce) {
      for (let t = 0; t < TICKS; t++) step(graph, pos, null)
      const id = requestAnimationFrame(() => setLayout(snapshot(pos)))
      return () => cancelAnimationFrame(id)
    }
    let t = 0
    let raf = 0
    const loop = () => {
      for (let k = 0; k < PER_FRAME && t < TICKS; k++, t++)
        step(graph, pos, dragging.current)
      setLayout(snapshot(pos))
      if (t < TICKS) raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [graph])

  // Kéo một nút: đổi toạ độ con trỏ sang toạ độ trong SVG rồi đặt nút tại đó
  function moveTo(e: ReactPointerEvent) {
    const id = dragging.current
    const svg = svgRef.current
    const pos = sim.current
    if (!id || !svg || !pos) return
    const pt = svg.createSVGPoint()
    pt.x = e.clientX
    pt.y = e.clientY
    const p = pt.matrixTransform(svg.getScreenCTM()!.inverse())
    const node = pos.get(id)!
    node.x = Math.min(W - 24, Math.max(24, p.x))
    node.y = Math.min(H - 24, Math.max(24, p.y))
    for (let k = 0; k < 3; k++) step(graph, pos, id) // các nút khác "đi theo" nhẹ nhàng
    setLayout(snapshot(pos))
  }

  const s = graph.summary
  const showLabels =
    graph.nodes.filter((n) => n.type === "account").length <= 12
  const linkedToHover = useMemo(() => {
    if (!hover) return null
    const set = new Set([hover.id])
    for (const e of graph.edges) {
      if (e.source === hover.id) set.add(e.target)
      if (e.target === hover.id) set.add(e.source)
    }
    return set
  }, [hover, graph.edges])

  return (
    <div className="viz grid gap-4">
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Tài khoản trong cụm" value={s.accounts} />
        <Stat
          label="Tài khoản mới (< 7 ngày)"
          value={s.new_accounts}
          tone={s.new_accounts >= 3 ? "warn" : undefined}
        />
        <Stat
          label="Đã bị hạn chế / chặn"
          value={s.restricted_accounts}
          tone={s.restricted_accounts ? "warn" : undefined}
        />
        <Stat label="Điểm chung (≥ 2 tài khoản)" value={s.shared_points} />
      </dl>

      <div className="relative overflow-hidden rounded-xl border bg-[radial-gradient(circle_at_50%_50%,rgba(56,189,248,.06),transparent_70%)]">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${W} ${H}`}
          className="block h-auto w-full touch-none select-none"
          role="img"
          aria-label={`Mạng liên kết: ${s.accounts} tài khoản, ${s.shared_points} điểm chung`}
          onPointerMove={moveTo}
          onPointerUp={() => (dragging.current = null)}
          onPointerLeave={() => {
            dragging.current = null
            setHover(null)
          }}
        >
          {graph.edges.map((e) => {
            const a = layout.get(e.source)
            const b = layout.get(e.target)
            if (!a || !b) return null
            const lit =
              linkedToHover?.has(e.source) && linkedToHover?.has(e.target)
            return (
              <line
                key={`${e.source}-${e.target}`}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                stroke={lit ? "#38bdf8" : "currentColor"}
                strokeOpacity={lit ? 0.9 : hover ? 0.08 : 0.22}
                strokeWidth={lit ? 1.6 : 1}
                className="text-foreground transition-[stroke-opacity]"
              />
            )
          })}
          {graph.nodes.map((n) => {
            const p = layout.get(n.id)
            if (!p) return null
            const dim = linkedToHover && !linkedToHover.has(n.id)
            return (
              <g
                key={n.id}
                transform={`translate(${p.x},${p.y})`}
                opacity={dim ? 0.3 : 1}
                className="cursor-grab transition-opacity active:cursor-grabbing"
                onPointerDown={(e) => {
                  dragging.current = n.id
                  ;(e.target as Element).setPointerCapture?.(e.pointerId)
                }}
                onPointerEnter={() => setHover(n)}
              >
                {n.type === "account" ? (
                  <AccountDot n={n} />
                ) : (
                  <EntityBadge n={n} />
                )}
                {(showLabels || n.root) && n.type === "account" && (
                  <text
                    y={n.root ? 30 : 24}
                    textAnchor="middle"
                    className="fill-muted-foreground text-[10px]"
                  >
                    {n.label}
                  </text>
                )}
              </g>
            )
          })}
        </svg>

        {hover && <HoverCard n={hover} />}
        {graph.truncated && (
          <p className="absolute bottom-2 left-3 rounded-md bg-background/80 px-2 py-1 text-[11px] text-muted-foreground">
            Cụm lớn: chỉ hiện 40 tài khoản đầu tiên
          </p>
        )}
      </div>

      <Legend />

      <details className="text-xs">
        <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
          Xem dạng danh sách
        </summary>
        <ul className="mt-2 grid gap-1">
          {graph.nodes
            .filter((n) => n.type !== "account")
            .map((n) => (
              <li key={n.id}>
                {ENTITY[n.type as keyof typeof ENTITY].label} {n.label}:{" "}
                {n.accounts} tài khoản (
                {graph.edges
                  .filter((e) => e.target === n.id)
                  .map((e) => graph.nodes.find((x) => x.id === e.source)?.label)
                  .join(", ")}
                )
              </li>
            ))}
        </ul>
      </details>
    </div>
  )
}

function AccountDot({ n }: { n: GraphNode }) {
  const color = n.worst_decision
    ? DECISION_COLOR[n.worst_decision]
    : "var(--muted-foreground)"
  const r = n.root ? 15 : 11
  return (
    <>
      {n.root && (
        <circle
          r={r + 7}
          fill="none"
          stroke="#38bdf8"
          strokeOpacity={0.5}
          strokeWidth={1.5}
        />
      )}
      {n.confirmed_abuse && (
        <circle
          r={r + 3.5}
          fill="none"
          stroke="var(--st-critical)"
          strokeWidth={2}
          strokeDasharray="3 2"
        />
      )}
      <circle r={r} fill={color} stroke="var(--background)" strokeWidth={2} />
      {n.is_new && (
        <circle
          cx={r * 0.7}
          cy={-r * 0.7}
          r={3.5}
          fill="#38bdf8"
          stroke="var(--background)"
          strokeWidth={1.5}
        />
      )}
    </>
  )
}

function EntityBadge({ n }: { n: GraphNode }) {
  const { icon: Icon } = ENTITY[n.type as keyof typeof ENTITY]
  const big = (n.accounts ?? 0) >= 3
  const size = big ? 30 : 24
  return (
    <>
      <rect
        x={-size / 2}
        y={-size / 2}
        width={size}
        height={size}
        rx={7}
        fill="var(--card)"
        stroke={big ? "#38bdf8" : "currentColor"}
        strokeOpacity={big ? 0.8 : 0.3}
        className="text-foreground"
      />
      <Icon
        x={-7}
        y={-7}
        width={14}
        height={14}
        className="text-foreground/80"
      />
    </>
  )
}

function HoverCard({ n }: { n: GraphNode }) {
  return (
    <div
      className="pointer-events-none absolute top-3 right-3 w-60 rounded-xl border bg-popover/95 p-3 text-xs shadow-lg backdrop-blur"
      role="status"
    >
      {n.type === "account" ? (
        <>
          <p className="font-medium">{n.label}</p>
          <p className="mt-1 text-muted-foreground">
            {n.root ? "Tài khoản đang xem · " : ""}tạo {n.age_days} ngày trước
            {n.is_new ? " (mới)" : ""}
          </p>
          <p className="mt-1">
            {n.worst_decision
              ? `Nặng nhất: ${DECISION_LABELS[n.worst_decision]} (${n.max_score} điểm)`
              : "Chưa có lượt chấm điểm trong 30 ngày"}
          </p>
          {n.confirmed_abuse && (
            <p className="mt-1 text-[#f87171]">Đã được kết luận lạm dụng</p>
          )}
        </>
      ) : (
        <>
          <p className="font-medium">
            {ENTITY[n.type as keyof typeof ENTITY].label}: {n.label}
          </p>
          <p className="mt-1 text-muted-foreground">
            Dùng chung bởi {n.accounts} tài khoản
          </p>
        </>
      )}
    </div>
  )
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string
  value: number
  tone?: "warn"
}) {
  return (
    <div className="rounded-xl border bg-muted/30 px-3 py-2">
      <dt className="text-[11px] text-muted-foreground">{label}</dt>
      <dd
        className={cn(
          "text-xl font-semibold tabular-nums",
          tone === "warn" && "text-[#fbbf24]"
        )}
      >
        {value}
      </dd>
    </div>
  )
}

function Legend() {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
      {Object.entries(DECISION_COLOR).map(([k, c]) => (
        <li key={k} className="flex items-center gap-1.5">
          <span
            className="size-2.5 rounded-full"
            style={{ background: c }}
            aria-hidden
          />
          Tài khoản: {DECISION_LABELS[k as keyof typeof DECISION_LABELS]}
        </li>
      ))}
      <li className="flex items-center gap-1.5">
        <span className="size-2.5 rounded-full bg-[#38bdf8]" aria-hidden /> Tài
        khoản mới
      </li>
      <li className="flex items-center gap-1.5">
        <span
          className="size-2.5 rounded-full border-2 border-dashed border-[#d03b3b]"
          aria-hidden
        />{" "}
        Đã kết luận lạm dụng
      </li>
      {Object.values(ENTITY).map(({ icon: Icon, label }) => (
        <li key={label} className="flex items-center gap-1.5">
          <Icon className="size-3.5" aria-hidden /> {label}
        </li>
      ))}
      <li>· Rê chuột để soi liên kết, kéo nút để sắp xếp lại</li>
    </ul>
  )
}
