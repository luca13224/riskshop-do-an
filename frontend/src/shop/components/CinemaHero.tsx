import { ArrowRight, Pause, Play, ShieldCheck } from "lucide-react"
import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
  type RefObject,
} from "react"
import { Link } from "react-router"

import {
  useCategories,
  useProducts,
  type Category,
  type CategoryCode,
} from "@/lib/api/catalog"
import { formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"

import { CategoryIcon } from "./CategoryIcon"
import { ProductImage } from "./ProductImage"

// ---------------------------------------------------------------------------------------------
// Banner "rạp chiếu phim" (ADR-005).
//
// Vòng màn ảnh: N tấm thẻ đặt trên một hình trụ bán kính R, CAMERA ĐẶT Ở TÂM hình trụ
// (giống khán giả ngồi giữa rạp). Mỗi thẻ tiếp tuyến với hình trụ nên luôn quay mặt về camera.
//   Thẻ ở góc a (độ, 0 = chính giữa):  x = R·sin(a),  z = R·(1 − cos a),  xoay rotateY(−a)
// Với perspective = R, thẻ càng ra hai bên càng tiến lại gần camera -> to hơn, tạo cảm giác
// bức tường màn ảnh bao quanh người xem. Thẻ có |a| > CULL thì ẩn đi (nửa sau của vòng).
// Vị trí được tính lại mỗi khung hình bằng requestAnimationFrame và ghi thẳng vào style,
// không qua state của React (60 lần/giây mà render lại React thì rất tốn).
// ---------------------------------------------------------------------------------------------
const N = 24 // số thẻ trên vòng (6 danh mục, mỗi danh mục lặp 4 lần)
const STEP = 360 / N // 15 độ giữa hai thẻ
const R = 760 // bán kính hình trụ (px trong khung thiết kế)
const CULL = 38 // góc lớn hơn thì ẩn thẻ (lớn quá thì thẻ ở rìa tiến sát camera, to và đè lên chữ)
const SPEED = 4 // độ/giây khi tự quay
const STAGE_W = 1100 // khung thiết kế của vòng; màn hình nhỏ hơn thì thu nhỏ cả khung theo tỉ lệ k
const STAGE_H = 330
const CARD_W = 170
const CARD_H = 250

// Màu riêng cho từng "màn ảnh" danh mục
const TINT: Record<CategoryCode, string> = {
  audio: "#8b5cf6",
  laptop: "#38bdf8",
  monitor: "#22d3ee",
  gear: "#f59e0b",
  phone: "#f43f5e",
  smart: "#34d399",
}

const easeOutCubic = (t: number) => 1 - (1 - t) ** 3
const DEG_PER_PX = 180 / (Math.PI * R) // kéo 1 px trên khung thiết kế = xoay bao nhiêu độ trên vòng

// Hạt bụi trong chùm sáng máy chiếu. Sinh bằng bộ số giả ngẫu nhiên có seed cố định
// để lần nào tải trang cũng giống nhau (Math.random trong lúc render sẽ đổi mỗi lần vẽ lại).
function seeded(seed: number) {
  return () => {
    seed = (seed * 16807) % 2147483647
    return (seed - 1) / 2147483646
  }
}
const rand = seeded(7)
const DUST = Array.from({ length: 16 }, () => ({
  left: 30 + rand() * 40, // % bề ngang, nằm trong chùm sáng
  top: 20 + rand() * 60, // % chiều cao
  size: 1 + rand() * 2,
  t: 7 + rand() * 8,
  delay: -rand() * 12,
  dx: (rand() - 0.5) * 40,
  o: 0.25 + rand() * 0.5,
}))

export function CinemaHero({
  onBrowse,
}: {
  onBrowse: (code: CategoryCode) => void
}) {
  const categories = useCategories()
  const cats = categories.data ?? []
  const [front, setFront] = useState<CategoryCode | null>(null) // danh mục đang ở chính giữa
  const [selected, setSelected] = useState<CategoryCode | null>(null) // danh mục người xem đã bấm chọn
  const showing = selected ?? front
  const sectionRef = useLightsOn()
  useSpotlight(sectionRef)
  const progressRef = useRef<HTMLDivElement>(null) // thanh "đang chiếu", vòng lặp của Ring ghi thẳng vào

  return (
    <section
      ref={sectionRef}
      id="hero"
      aria-label="Giới thiệu"
      // Tràn hết chiều ngang màn hình (thoát khỏi khung max-w của trang)
      className="relative isolate mx-[calc(50%-50vw)] overflow-hidden text-white"
    >
      {/* Nền tối của "phòng chiếu": dừng phía trên, nửa dưới màn hình chiếu chính nằm trên nền trắng */}
      <div
        aria-hidden
        data-hero-dark // header đo phần tử này để biết lúc nào đang nằm trên nền tối
        className="absolute inset-x-0 top-0 bottom-40 -z-10 bg-[#05070b] sm:bottom-56"
      >
        <div className="absolute inset-0 [background-image:radial-gradient(rgba(255,255,255,.55)_1px,transparent_1px)] [background-size:46px_46px] opacity-[.12]" />
        <div className="absolute inset-x-0 bottom-0 h-2/3 bg-[linear-gradient(180deg,transparent,rgba(25,127,255,.07)_60%,rgba(25,127,255,.04))]" />
        <div className="absolute top-[45%] left-1/2 size-[46rem] -translate-x-1/2 rounded-full bg-cyan-400/10 blur-3xl" />
        {/* Vùng sáng đi theo chuột (biến --mx, --my do useSpotlight ghi) */}
        <div className="absolute inset-0 bg-[radial-gradient(520px_circle_at_var(--mx,50%)_var(--my,35%),rgba(80,200,255,.09),transparent_70%)]" />
        {/* Chùm sáng máy chiếu: hình thang hẹp ở trên, loe dần xuống phía màn hình chiếu chính */}
        <div className="absolute top-0 left-1/2 h-[88%] w-[min(1200px,140%)] -translate-x-1/2 bg-[linear-gradient(180deg,rgba(190,235,255,.10),rgba(190,235,255,.03)_65%,transparent)] blur-md [clip-path:polygon(44%_0,56%_0,100%_100%,0_100%)]" />
        {DUST.map((d, i) => (
          <span
            key={i}
            className="dust absolute rounded-full bg-cyan-50"
            style={
              {
                left: `${d.left}%`,
                top: `${d.top}%`,
                width: d.size,
                height: d.size,
                "--t": `${d.t}s`,
                "--delay": `${d.delay}s`,
                "--dx": `${d.dx}px`,
                "--o": d.o,
              } as CSSProperties
            }
          />
        ))}
      </div>

      <div className="relative z-10 mx-auto flex max-w-7xl flex-col items-center px-4 pt-14 text-center sm:px-6 sm:pt-20">
        <p
          className="rise flex h-10 items-center gap-3 rounded-xl border border-white/10 bg-white/[.03] py-1 pr-4 pl-1 text-[13px] text-white/90 backdrop-blur"
          style={{ "--d": "100ms" } as CSSProperties}
        >
          <span className="flex size-8 items-center justify-center rounded-lg bg-[linear-gradient(to_top,#46afc8,#0b859d_4px,#004e66_8px,#031a2a_14px,#090c1c)] shadow-[inset_1px_0_0_rgba(150,220,250,.4),inset_-1px_0_0_rgba(150,220,250,.5)]">
            <ShieldCheck className="size-4 text-cyan-100" />
          </span>
          Mỗi đơn hàng được kiểm tra rủi ro trước khi giao
        </p>

        <h1
          className="rise mt-6 text-[clamp(1.7rem,8vw,2.6rem)] leading-[0.95] font-black tracking-tight uppercase [text-shadow:0_0_34px_rgba(130,180,255,.22)] sm:text-7xl"
          style={{ "--d": "220ms" } as CSSProperties}
        >
          <span className="block whitespace-nowrap">Nâng cấp thiết bị</span>
          <span className="block whitespace-nowrap">mua sắm an tâm</span>
        </h1>

        <p
          className="rise mt-5 max-w-xl text-[15px] leading-relaxed text-white/65 sm:text-base"
          style={{ "--d": "380ms" } as CSSProperties}
        >
          <b className="font-semibold text-white">
            Âm thanh, laptop, màn hình, phụ kiện
          </b>{" "}
          chọn lọc cho góc làm việc và giải trí. Ưu đãi thật dành cho người dùng
          thật.
        </p>

        <div
          className="rise mt-7 flex flex-wrap justify-center gap-3"
          style={{ "--d": "500ms" } as CSSProperties}
        >
          <a
            href="#san-pham"
            className="btn-glow h-13 rounded-[13px] px-7 text-base font-medium"
          >
            <span>Xem sản phẩm</span>
          </a>
          <Link
            to="/register"
            className="flex h-13 items-center rounded-[13px] border border-white/15 px-6 text-base text-white/85 transition hover:bg-white/5"
          >
            Nhận mã TANTHU
          </Link>
        </div>
      </div>

      <Ring
        cats={cats}
        selected={selected}
        onFront={setFront}
        onSelect={setSelected}
        progressRef={progressRef}
      />

      <MainScreen
        category={cats.find((c) => c.code === showing) ?? null}
        progressRef={progressRef}
        paused={selected !== null}
        onResume={() => setSelected(null)}
        onBrowse={onBrowse}
      />

      {/* "Đèn rạp bật sáng": lớp trắng phủ lên banner, đậm dần khi banner cuộn ra khỏi màn hình */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 z-20 bg-white"
        style={{ opacity: "var(--lights, 0)" }}
      />
    </section>
  )
}

// Cập nhật biến CSS --lights (0 -> 0.9) theo tiến độ cuộn qua banner.
// Bắt đầu sáng khi đã cuộn qua 30% banner; cập nhật tối đa 1 lần mỗi khung hình.
function useLightsOn() {
  const ref = useRef<HTMLElement>(null)
  useEffect(() => {
    let raf = 0
    function update() {
      raf = 0
      const el = ref.current
      if (!el) return
      const rect = el.getBoundingClientRect()
      const progress = Math.min(1, Math.max(0, -rect.top / rect.height))
      const lights = Math.max(0, (progress - 0.3) / 0.7) * 0.9
      el.style.setProperty("--lights", lights.toFixed(3))
    }
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update)
    }
    update()
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => {
      window.removeEventListener("scroll", onScroll)
      cancelAnimationFrame(raf)
    }
  }, [])
  return ref
}

// Vùng sáng đi theo chuột: ghi vị trí chuột (tính theo banner) vào --mx, --my.
// Chỉ bật trên thiết bị có chuột; màn hình cảm ứng giữ vị trí mặc định.
function useSpotlight(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    if (!window.matchMedia("(hover: hover)").matches) return
    let raf = 0
    let x = 0
    let y = 0
    function update() {
      raf = 0
      const el = ref.current
      if (!el) return
      const rect = el.getBoundingClientRect()
      el.style.setProperty("--mx", `${x - rect.left}px`)
      el.style.setProperty("--my", `${y - rect.top}px`)
    }
    const onMove = (e: PointerEvent) => {
      x = e.clientX
      y = e.clientY
      if (!raf) raf = requestAnimationFrame(update)
    }
    window.addEventListener("pointermove", onMove, { passive: true })
    return () => {
      window.removeEventListener("pointermove", onMove)
      cancelAnimationFrame(raf)
    }
  }, [ref])
}

// ---------------------------------------------------------------------------------------------
function Ring({
  cats,
  selected,
  onFront,
  onSelect,
  progressRef,
}: {
  cats: Category[]
  selected: CategoryCode | null
  onFront: (code: CategoryCode) => void
  onSelect: (code: CategoryCode | null) => void
  progressRef: RefObject<HTMLDivElement | null>
}) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const groupRef = useRef<HTMLDivElement>(null)
  const cardRefs = useRef<(HTMLButtonElement | null)[]>([])
  const [k, setK] = useState(1) // tỉ lệ thu nhỏ khung thiết kế cho vừa màn hình

  // Các giá trị dùng trong vòng lặp animation để ở ref, để vòng lặp không phải khởi động lại
  const phase = useRef(0)
  const hovering = useRef(false)
  // Kéo/vuốt để xoay: x lúc bắt đầu, phase lúc bắt đầu, đã thực sự kéo chưa (quá 6 px)
  const drag = useRef<{ x: number; phase: number; moved: boolean } | null>(null)
  const justDragged = useRef(false) // vừa kéo xong thì bỏ qua cú "click" đi kèm
  const selectedRef = useRef(selected)
  const anim = useRef<{ from: number; to: number; start: number } | null>(null)
  const frontRef = useRef<CategoryCode | null>(null)
  const catsRef = useRef(cats)
  const onFrontRef = useRef(onFront)

  useEffect(() => {
    selectedRef.current = selected
    catsRef.current = cats
    onFrontRef.current = onFront
  })

  // Thu nhỏ khung 1100 px theo bề rộng thật (điện thoại)
  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(([entry]) =>
      // Không thu nhỏ quá 0.55: trên điện thoại thà cắt bớt hai bên (section có overflow-hidden)
      // còn hơn để màn ảnh bé xíu
      setK(Math.min(1, Math.max(0.55, entry.contentRect.width / STAGE_W)))
    )
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // Vòng lặp animation
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)")
    let raf = 0
    let last = performance.now()
    // Thị sai theo chuột: điểm nhìn (perspective-origin) dịch nhẹ sang trái/phải theo chuột,
    // làm vòng màn ảnh hơi nghiêng theo. tilt đuổi dần theo target để chuyển động mượt.
    let tiltTarget = 0
    let tilt = 0
    const onMove = (e: PointerEvent) => {
      tiltTarget = e.clientX / window.innerWidth - 0.5
    }
    window.addEventListener("pointermove", onMove, { passive: true })

    function place() {
      let best = Infinity
      let bestA = 0
      let frontIdx = 0
      cardRefs.current.forEach((el, i) => {
        if (!el) return
        // Góc có dấu của thẻ i, đưa về khoảng (-180, 180]
        const a = ((((i * STEP + phase.current) % 360) + 540) % 360) - 180
        if (Math.abs(a) > CULL) {
          el.style.visibility = "hidden" // ẩn hẳn: không bấm được, không nhận focus bàn phím
          return
        }
        if (Math.abs(a) < best) {
          best = Math.abs(a)
          bestA = a
          frontIdx = i
        }
        const r = (a * Math.PI) / 180
        const c = Math.cos(r)
        el.style.visibility = "visible"
        el.style.transform = `translate3d(${R * Math.sin(r)}px,0,${R * (1 - c)}px) rotateY(${-a}deg)`
        // Thẻ chính giữa sáng nhất, ra rìa tối dần; gần mép ẩn thì mờ dần để không "bật" đột ngột
        el.style.filter = `brightness(${1 - 0.45 * ((1 - c) / (1 - Math.cos((CULL * Math.PI) / 180)))})`
        el.style.opacity = String(Math.min(1, (CULL - Math.abs(a)) / 8))
      })
      // Màn ở chính giữa phát sáng (CSS đọc thuộc tính data-front)
      cardRefs.current.forEach((el, i) =>
        el?.toggleAttribute("data-front", i === frontIdx)
      )
      // Thanh "đang chiếu": thẻ giữa đi từ góc +STEP/2 về −STEP/2 thì thanh chạy từ 0 đến 100%.
      // Tính thẳng từ góc nên dừng vòng (rê chuột, đã chọn) thì thanh cũng dừng theo.
      if (progressRef.current) {
        const p = selectedRef.current
          ? 1
          : Math.min(1, Math.max(0, (STEP / 2 - bestA) / STEP))
        progressRef.current.style.transform = `scaleX(${p})`
      }
      if (groupRef.current && !reduce.matches) {
        tilt += (tiltTarget - tilt) * 0.06
        groupRef.current.style.perspectiveOrigin = `${50 + tilt * 10}% ${STAGE_H * 1.9}px`
      }
      const list = catsRef.current
      if (list.length) {
        const code = list[frontIdx % list.length].code
        if (code !== frontRef.current) {
          frontRef.current = code
          onFrontRef.current(code) // chỉ báo cho React khi danh mục chính giữa thực sự đổi
        }
      }
    }

    function tick(t: number) {
      const dt = Math.min((t - last) / 1000, 0.1) // tab bị ẩn lâu cũng không nhảy cóc
      last = t
      if (anim.current) {
        if (anim.current.start < 0) anim.current.start = t
        const p = Math.min(1, (t - anim.current.start) / 700)
        phase.current =
          anim.current.from +
          (anim.current.to - anim.current.from) * easeOutCubic(p)
        if (p === 1) anim.current = null
      } else if (
        !hovering.current &&
        !drag.current?.moved &&
        !selectedRef.current &&
        !reduce.matches
      ) {
        phase.current -= SPEED * dt
      }
      place()
      raf = requestAnimationFrame(tick)
    }

    const onVisible = () => {
      last = performance.now()
    }
    document.addEventListener("visibilitychange", onVisible)
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      document.removeEventListener("visibilitychange", onVisible)
      window.removeEventListener("pointermove", onMove)
    }
  }, [progressRef])

  // ---- Kéo / vuốt để xoay vòng ----
  function onPointerDown(e: ReactPointerEvent) {
    if (e.pointerType === "mouse" && e.button !== 0) return
    drag.current = { x: e.clientX, phase: phase.current, moved: false }
  }
  function onPointerMove(e: ReactPointerEvent) {
    const d = drag.current
    if (!d) return
    const dx = e.clientX - d.x
    if (!d.moved) {
      if (Math.abs(dx) < 6) return // dưới 6 px coi như một cú bấm, không phải kéo
      d.moved = true
      anim.current = null
      wrapRef.current?.setPointerCapture(e.pointerId)
    }
    // Kéo sang phải thì vòng quay sang phải; chia cho k vì khung đang bị thu nhỏ
    phase.current = d.phase + (dx / k) * DEG_PER_PX
  }
  function onPointerUp() {
    const d = drag.current
    drag.current = null
    if (!d?.moved) return
    // Trình duyệt có thể bắn thêm một "click" ngay sau khi thả tay: chặn nó, rồi mở lại ở lượt sau
    justDragged.current = true
    setTimeout(() => (justDragged.current = false), 0)
    // Thả tay thì canh cho một màn ảnh nằm đúng chính giữa
    anim.current = {
      from: phase.current,
      to: Math.round(phase.current / STEP) * STEP,
      start: -1,
    }
    if (selectedRef.current) onSelect(null) // đã kéo sang danh mục khác thì bỏ chọn cũ
  }

  // Bấm một màn ảnh: xoay nó ra chính giữa rồi dừng lại. Bấm lại màn đang chọn thì chạy tiếp.
  function pick(i: number, code: CategoryCode) {
    if (justDragged.current) return
    if (selectedRef.current === code) {
      onSelect(null)
      return
    }
    const a = ((((i * STEP + phase.current) % 360) + 540) % 360) - 180
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches
    if (reduce) {
      phase.current -= a
    } else {
      // start = -1: khung hình kế tiếp của vòng lặp sẽ ghi mốc thời gian bắt đầu
      anim.current = { from: phase.current, to: phase.current - a, start: -1 }
    }
    onSelect(code)
  }

  return (
    <div
      ref={wrapRef}
      className="rise relative mx-auto mt-10 w-full max-w-[1100px] sm:mt-14"
      // touch-action: pan-y -> vuốt dọc vẫn cuộn trang, vuốt ngang thì xoay vòng
      style={
        {
          height: STAGE_H * k,
          "--d": "650ms",
          touchAction: "pan-y",
        } as CSSProperties
      }
      onPointerEnter={(e) => {
        if (e.pointerType === "mouse") hovering.current = true
      }}
      onPointerLeave={() => (hovering.current = false)}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
      onFocus={() => (hovering.current = true)}
      onBlur={() => (hovering.current = false)}
    >
      <div
        ref={groupRef}
        role="group"
        aria-label="Các danh mục, đang quay như màn ảnh rạp phim"
        className="absolute top-0 left-1/2"
        style={{
          width: STAGE_W,
          height: STAGE_H,
          marginLeft: -STAGE_W / 2,
          transform: `scale(${k})`,
          transformOrigin: "50% 0",
          perspective: `${R}px`,
          perspectiveOrigin: `50% ${STAGE_H * 1.9}px`, // đường chân trời thấp hơn thẻ -> mép trên thẻ nghiêng
          transformStyle: "preserve-3d",
        }}
      >
        {cats.length > 0 &&
          Array.from({ length: N }, (_, i) => {
            const cat = cats[i % cats.length]
            const active = selected === cat.code
            return (
              <button
                key={i}
                ref={(el) => {
                  cardRefs.current[i] = el
                }}
                type="button"
                onClick={() => pick(i, cat.code)}
                aria-pressed={active}
                aria-label={`${cat.name}, ${cat.product_count} sản phẩm`}
                className={cn(
                  "group invisible absolute cursor-pointer overflow-hidden rounded-xl text-left select-none [backface-visibility:hidden] focus-visible:outline-2 focus-visible:outline-cyan-300",
                  active && "outline-2 outline-cyan-300"
                )}
                style={{
                  left: STAGE_W / 2 - CARD_W / 2,
                  top: 30,
                  width: CARD_W,
                  height: CARD_H,
                  // Ảnh danh mục (tông tối) + lớp phủ tối dần xuống dưới để chữ luôn đọc được + ánh màu riêng của danh mục
                  background: `linear-gradient(180deg, rgba(5,7,11,.1), rgba(5,7,11,.55) 38%, rgba(5,7,11,.92) 68%), linear-gradient(170deg, ${TINT[cat.code]}66, transparent 55%), url(/categories/${cat.code}.webp) center / cover, #0b0f18`,
                  boxShadow:
                    "0 24px 46px rgba(0,0,0,.6), inset 0 0 0 1px rgba(255,255,255,.14), inset 0 16px 30px rgba(255,255,255,.05)",
                }}
              >
                {/* Vân quét mờ + vệt sáng mặt kính: cho thẻ giống một màn hình thật */}
                <span
                  aria-hidden
                  className="absolute inset-0 bg-[repeating-linear-gradient(0deg,rgba(255,255,255,.035)_0_1px,transparent_1px_3px)]"
                />
                <span
                  aria-hidden
                  className="absolute inset-x-0 top-0 h-1/2 bg-[linear-gradient(160deg,rgba(255,255,255,.14),transparent_45%)]"
                />
                {/* Phát sáng khi đang ở chính giữa (thuộc tính data-front do vòng lặp gắn) */}
                <span
                  aria-hidden
                  className="absolute inset-0 rounded-xl opacity-0 transition-opacity duration-500 group-data-[front]:opacity-100"
                  style={{
                    boxShadow: `inset 0 0 0 1px ${TINT[cat.code]}aa, inset 0 0 46px ${TINT[cat.code]}40`,
                  }}
                />
                <span
                  className="absolute top-[24%] left-1/2 -translate-x-1/2 -translate-y-1/2"
                  style={{
                    color: TINT[cat.code],
                    filter: `drop-shadow(0 0 14px ${TINT[cat.code]})`,
                  }}
                >
                  <CategoryIcon
                    category={cat.code}
                    className="size-11"
                    strokeWidth={1.5}
                  />
                </span>
                {/* Tên đặt ở nửa trên: nửa dưới thẻ bị màn hình chiếu chính che (cố ý, để tạo chiều sâu) */}
                <span className="absolute inset-x-3 top-[44%] text-center">
                  <span className="block text-[15px] leading-tight font-semibold text-white">
                    {cat.name}
                  </span>
                  <span className="mt-1 block text-xs text-white/55">
                    {cat.product_count} sản phẩm
                  </span>
                </span>
              </button>
            )
          })}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------------------------
// Màn hình chiếu chính: đặt TRƯỚC vòng màn ảnh, đè lên phần dưới của vòng.
// Tự chiếu sản phẩm của danh mục đang ở chính giữa (hoặc danh mục người xem vừa bấm).
function MainScreen({
  category,
  progressRef,
  paused,
  onResume,
  onBrowse,
}: {
  category: Category | null
  progressRef: RefObject<HTMLDivElement | null>
  paused: boolean
  onResume: () => void
  onBrowse: (code: CategoryCode) => void
}) {
  const products = useProducts({
    category: category?.code,
    page: 1,
    pageSize: 4,
  })
  const items = category ? (products.data?.items ?? []) : []

  return (
    <div
      className="rise relative z-10 mx-auto -mt-16 w-[calc(100%-2rem)] max-w-5xl sm:-mt-24"
      style={{ "--d": "850ms" } as CSSProperties}
    >
      <div className="overflow-hidden rounded-[22px] bg-[#10131c]/90 shadow-[0_-14px_44px_rgba(0,0,0,.55),0_30px_60px_-20px_rgba(0,0,0,.35)] ring-1 ring-white/10 backdrop-blur-md sm:rounded-[28px]">
        {/* Thanh trình duyệt giả */}
        <div className="flex h-11 items-center gap-3 px-4 sm:px-6">
          <span className="hidden gap-1.5 sm:flex" aria-hidden>
            <i className="size-2.5 rounded-full bg-[#ee5c62]" />
            <i className="size-2.5 rounded-full bg-[#f6b719]" />
            <i className="size-2.5 rounded-full bg-[#12c02f]" />
          </span>
          <p className="mx-auto max-w-[60%] truncate rounded-md bg-black/40 px-4 py-1 text-xs text-white/70 ring-1 ring-white/5">
            riskshop · {category ? category.name : "Đang tải…"}
          </p>
          <button
            type="button"
            onClick={onResume}
            disabled={!paused}
            aria-label={
              paused ? "Tiếp tục quay vòng danh mục" : "Vòng danh mục đang quay"
            }
            className="flex size-7 items-center justify-center rounded-full text-white/70 hover:bg-white/10 disabled:opacity-40"
          >
            {paused ? (
              <Play className="size-3.5" />
            ) : (
              <Pause className="size-3.5" />
            )}
          </button>
        </div>

        {/* Thanh "đang chiếu": chạy từ trái sang phải trong lúc một danh mục ở chính giữa */}
        <div
          className="mx-4 mb-2 h-0.5 overflow-hidden rounded-full bg-white/10 sm:mx-6"
          aria-hidden
        >
          <div
            ref={progressRef}
            className="h-full origin-left scale-x-0 bg-cyan-300 shadow-[0_0_8px_#67e8f9]"
          />
        </div>

        {/* "Trang web" bên trong màn hình: nền trắng như shop thật */}
        <div className="mx-1.5 rounded-t-[14px] bg-white p-4 text-foreground sm:mx-2 sm:p-6">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-[11px] font-medium tracking-widest text-muted-foreground uppercase">
                Đang chiếu
              </p>
              <p
                className="truncate text-lg font-semibold sm:text-xl"
                aria-live="polite"
              >
                {category?.name ?? "…"}
              </p>
            </div>
            {category && (
              <button
                type="button"
                onClick={() => onBrowse(category.code)}
                className="flex shrink-0 items-center gap-2 rounded-full bg-buy py-2 pr-2 pl-4 text-sm font-semibold text-buy-foreground transition hover:bg-buy/85"
              >
                Xem tất cả
                <ArrowRight className="size-4" />
              </button>
            )}
          </div>

          <div
            className={cn(
              "mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4",
              products.isPlaceholderData && "opacity-60 transition-opacity"
            )}
          >
            {(items.length ? items : Array.from({ length: 4 }, () => null)).map(
              (p, i) =>
                p ? (
                  <Link
                    key={p.id}
                    to={`/products/${p.slug}`}
                    className={cn("group", i >= 2 && "hidden sm:block")}
                  >
                    <div className="overflow-hidden rounded-2xl bg-secondary">
                      <ProductImage
                        category={p.category}
                        imageUrl={p.image_url}
                        name={p.name}
                        iconClassName="size-10"
                        className="transition duration-500 group-hover:scale-105"
                      />
                    </div>
                    <p className="mt-2 line-clamp-1 text-sm font-medium">
                      {p.name}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {formatVND(p.price)}
                    </p>
                  </Link>
                ) : (
                  <div
                    key={i}
                    className={cn(
                      "aspect-square rounded-2xl bg-secondary",
                      i >= 2 && "hidden sm:block"
                    )}
                  />
                )
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
