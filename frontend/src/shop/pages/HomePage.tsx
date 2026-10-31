import {
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  Check,
  Copy,
  MessageSquareText,
  PackageCheck,
  RotateCcw,
  ShieldCheck,
  ShoppingCart,
  Truck,
} from "lucide-react"
import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type PointerEvent,
  type ReactNode,
  type RefObject,
} from "react"
import { Link, Navigate, useNavigate, useSearchParams } from "react-router"

import { Skeleton } from "@/components/ui/skeleton"
import { useMe } from "@/lib/api/auth"
import { useProducts, type Product } from "@/lib/api/catalog"
import { formatVND } from "@/lib/format"
import { cn } from "@/lib/utils"
import { RoundButton, SectionHeading } from "@/shop/components/bits"
import { CinemaHero } from "@/shop/components/CinemaHero"
import { ProductCard } from "@/shop/components/ProductCard"
import { ProductImage } from "@/shop/components/ProductImage"
import { Reveal, useInView } from "@/shop/components/Reveal"

// Trang chủ (phần BODY) là một chuỗi "chương", mỗi chương bước vào một kiểu khác nhau khi lăn tới:
// rạp chiếu (danh mục) → hàng nổi bật (trượt ngang) → vì sao chọn RiskShop (bento, viền sáng theo chuột)
// → sản phẩm chủ lực (ghim lại khi cuộn) → các bước mua sắm (đường kẻ tự vẽ) → ưu đãi.
// Danh sách đầy đủ có bộ lọc nằm ở trang danh mục (/danh-muc), không đổ hết ra trang chủ.
export function HomePage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()

  // Link cũ dạng /?category=... chuyển sang trang danh mục mới
  const legacy = params.get("category")
  if (legacy) return <Navigate to={`/danh-muc/${legacy}`} replace />

  return (
    // Lưới 1 cột minmax(0,1fr): cột không bị nội dung cuộn ngang (hàng Nổi bật) kéo giãn ra ngoài màn hình
    <div className="grid grid-cols-[minmax(0,1fr)] gap-24 sm:gap-32">
      <CinemaHero onBrowse={(code) => navigate(`/danh-muc/${code}`)} />
      <FeaturedRow />
      <WhyBento />
      <FlagshipStory />
      <SafeSteps />
      <OfferCta />
    </div>
  )
}

// ---------- Chương 1: hàng "Nổi bật" — thẻ trượt vào từ phải, lần lượt ----------
function FeaturedRow() {
  // Lấy cả danh mục rồi xếp xen kẽ theo danh mục, để hàng nổi bật có đủ loại thay vì 8 món cùng nhóm
  const products = useProducts({ page: 1, pageSize: 24 })
  const featured = interleaveByCategory(products.data?.items ?? []).slice(0, 8)
  const rowRef = useRef<HTMLDivElement>(null)

  function scrollBy(direction: 1 | -1) {
    const row = rowRef.current
    if (row) row.scrollBy({ left: direction * row.clientWidth * 0.8, behavior: "smooth" })
  }

  return (
    <section aria-labelledby="noi-bat">
      <Reveal className="flex items-end justify-between gap-4">
        <SectionHeading id="noi-bat" eyebrow="Tuần này">
          Nổi bật
        </SectionHeading>
        <div className="flex items-center gap-2">
          <Link
            to="/danh-muc"
            className="mr-2 hidden items-center gap-1 text-sm font-semibold underline-offset-4 hover:underline sm:flex"
          >
            Xem tất cả <ArrowRight className="size-4" />
          </Link>
          <span className="hidden gap-2 sm:flex">
            <RoundButton label="Xem sản phẩm trước" onClick={() => scrollBy(-1)}>
              <ArrowLeft className="size-5" />
            </RoundButton>
            <RoundButton label="Xem sản phẩm tiếp theo" onClick={() => scrollBy(1)}>
              <ArrowRight className="size-5" />
            </RoundButton>
          </span>
        </div>
      </Reveal>
      <div
        ref={rowRef}
        className="-mx-4 mt-8 flex snap-x snap-mandatory scroll-px-4 [scrollbar-width:none] gap-4 overflow-x-auto px-4 pb-2 sm:-mx-6 sm:scroll-px-6 sm:px-6"
      >
        {products.isPending
          ? Array.from({ length: 4 }, (_, i) => (
              <Skeleton key={i} className="aspect-[3/4] w-64 shrink-0 rounded-3xl" />
            ))
          : featured.map((p, i) => (
              <Reveal
                key={p.id}
                variant="left"
                delay={Math.min(i, 4) * 90}
                className="w-[70%] shrink-0 snap-start sm:w-64 lg:w-[calc((100%-3*1rem)/4)]"
              >
                <ProductCard product={p} />
              </Reveal>
            ))}
      </div>
      <Link
        to="/danh-muc"
        className="mt-6 flex items-center justify-center gap-1 rounded-full border py-3 text-sm font-semibold sm:hidden"
      >
        Xem tất cả sản phẩm <ArrowRight className="size-4" />
      </Link>
    </section>
  )
}

// ---------- Chương 2: "Vì sao chọn RiskShop" — bento, viền sáng chạy theo chuột ----------
function WhyBento() {
  return (
    <section aria-labelledby="vi-sao">
      <Reveal>
        <SectionHeading id="vi-sao" eyebrow="Mua sắm an tâm">
          Vì sao chọn RiskShop
        </SectionHeading>
      </Reveal>
      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:grid-rows-2">
        <Reveal variant="zoom" className="sm:col-span-2 lg:row-span-2">
          <GlowCard dark className="h-full min-h-80">
            <ShieldVisual />
            <div className="relative mt-auto max-w-sm">
              <p className="text-xs font-semibold tracking-[0.2em] text-white/50 uppercase">Bảo vệ ưu đãi</p>
              <h3 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
                Ưu đãi thật cho người dùng thật
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-white/65">
                Mỗi đơn hàng được kiểm tra an toàn tự động trong tích tắc, để mã giảm giá đến đúng tay khách
                hàng thật chứ không bị tài khoản ảo gom hết.
              </p>
            </div>
          </GlowCard>
        </Reveal>
        <BentoItem delay={80} icon={Truck} title="Giao toàn quốc">
          Thanh toán khi nhận hàng (COD) hoặc trả trước.
        </BentoItem>
        <BentoItem delay={160} icon={RotateCcw} title="Đổi trả 7 ngày">
          Lỗi do nhà sản xuất được đổi mới.
        </BentoItem>
        <BentoItem delay={240} icon={BadgeCheck} title="Thông số rõ ràng">
          Bảng thông số chi tiết cho từng sản phẩm.
        </BentoItem>
        <BentoItem delay={320} icon={MessageSquareText} title="Khiếu nại minh bạch" to="/appeals">
          Đơn bị hạn chế nhầm? Gửi khiếu nại, nhân viên xem xét và phản hồi.
        </BentoItem>
      </div>
    </section>
  )
}

function BentoItem({
  icon: Icon,
  title,
  delay,
  to,
  children,
}: {
  icon: typeof Truck
  title: string
  delay: number
  to?: string
  children: ReactNode
}) {
  const body = (
    <GlowCard className="h-full">
      <span className="flex size-11 items-center justify-center rounded-2xl bg-background shadow-sm transition group-hover:bg-buy group-hover:text-buy-foreground">
        <Icon className="size-5" />
      </span>
      <h3 className="mt-6 font-semibold">{title}</h3>
      <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{children}</p>
      {to && (
        <span className="mt-3 inline-flex items-center gap-1 text-sm font-semibold">
          Xem khiếu nại <ArrowRight className="size-4 transition group-hover:translate-x-1" />
        </span>
      )}
    </GlowCard>
  )
  return (
    <Reveal delay={delay} className="min-h-48">
      {to ? (
        <Link to={to} className="block h-full rounded-[1.75rem] focus-visible:ring-2 focus-visible:ring-ring">
          {body}
        </Link>
      ) : (
        body
      )}
    </Reveal>
  )
}

// Thẻ có viền sáng chạy theo chuột: ghi vị trí chuột vào --gx, --gy (CSS .glow-card trong index.css)
function GlowCard({ dark, className, children }: { dark?: boolean; className?: string; children: ReactNode }) {
  function onMove(e: PointerEvent<HTMLDivElement>) {
    const r = e.currentTarget.getBoundingClientRect()
    e.currentTarget.style.setProperty("--gx", `${e.clientX - r.left}px`)
    e.currentTarget.style.setProperty("--gy", `${e.clientY - r.top}px`)
  }
  return (
    <div
      onPointerMove={onMove}
      className={cn(
        "glow-card group flex flex-col overflow-hidden rounded-[1.75rem] p-6 transition duration-500 hover:-translate-y-1 sm:p-8",
        dark ? "bg-[linear-gradient(160deg,#10203a,#080d18_70%)] text-white ring-1 ring-cyan-300/10" : "bg-secondary ring-1 ring-white/[.04]",
        className
      )}
    >
      {children}
    </div>
  )
}

// Hình minh họa: khiên ở giữa, các vòng "quét" lan ra, vài đơn hàng đã được kiểm tra bay quanh
function ShieldVisual() {
  return (
    <div aria-hidden className="relative -mx-2 mb-6 flex h-44 items-center justify-center sm:h-52">
      <div className="absolute inset-0 bg-[radial-gradient(50%_60%_at_50%_50%,rgba(80,200,255,.18),transparent_70%)]" />
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="absolute size-28 rounded-full border border-cyan-300/30 motion-safe:animate-[ping_3.6s_cubic-bezier(0,0,.2,1)_infinite]"
          style={{ animationDelay: `${i * 1.2}s` }}
        />
      ))}
      <span className="relative flex size-20 items-center justify-center rounded-3xl bg-[linear-gradient(160deg,#1c2a3a,#0b0d12)] shadow-[0_0_40px_-6px_rgba(80,200,255,.55)] ring-1 ring-cyan-300/30">
        <ShieldCheck className="size-9 text-cyan-200" />
      </span>
      {[
        { label: "Đơn #A12", cls: "left-[6%] top-[14%]" },
        { label: "Đơn #B07", cls: "right-[4%] top-[30%]" },
        { label: "Đơn #C33", cls: "left-[14%] bottom-[8%]" },
      ].map((o, i) => (
        <span
          key={o.label}
          className={cn(
            "absolute flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/80 backdrop-blur motion-safe:animate-[float_6s_ease-in-out_infinite]",
            o.cls
          )}
          style={{ animationDelay: `${i * -2}s` }}
        >
          <Check className="size-3.5 text-emerald-300" /> {o.label}
        </span>
      ))}
    </div>
  )
}

// ---------- Chương 3: sản phẩm chủ lực — khối được GHIM lại trong lúc cuộn ----------
// Phần cao 260vh, bên trong là khung dính (sticky) cao bằng màn hình. Cuộn qua phần này thì --p chạy 0 → 1:
// ảnh phóng to dần, từng dòng thông số hiện ra. Giảm chuyển động: bỏ ghim, hiện tất cả ngay.
function FlagshipStory() {
  const products = useProducts({ category: "monitor", page: 1, pageSize: 12 })
  const p = flagship(products.data?.items ?? [])
  const ref = useRef<HTMLElement>(null)
  useScrollProgress(ref)
  const specs = (p?.specs ?? []).slice(0, 5)

  return (
    <section
      ref={ref}
      aria-labelledby="chu-luc"
      className="relative mx-[calc(50%-50vw)] h-[260vh] bg-[linear-gradient(180deg,var(--background),#03060c_12%,#03060c_88%,var(--background))] text-white motion-reduce:h-auto"
      style={{ "--p": 0 } as CSSProperties}
    >
      <div className="sticky top-0 flex h-svh items-center overflow-hidden motion-reduce:static motion-reduce:h-auto motion-reduce:py-20">
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(45%_55%_at_70%_50%,rgba(80,200,255,calc(.08_+_var(--p)*.14)),transparent_70%),radial-gradient(40%_50%_at_15%_90%,rgba(255,214,10,.10),transparent_70%)]"
        />
        <div className="relative mx-auto grid w-full max-w-7xl items-center gap-6 px-4 sm:px-6 md:grid-cols-[1fr_1.15fr] md:gap-12">
          <div className="order-2 md:order-1">
            <p className="text-xs font-semibold tracking-[0.2em] text-cyan-300/80 uppercase">Góc làm việc</p>
            <h2 id="chu-luc" className="mt-3 text-3xl leading-tight font-semibold tracking-tight sm:text-5xl">
              {p?.name ?? "Một màn hình tốt đổi cả ngày làm việc."}
            </h2>
            {p && <p className="mt-3 text-lg font-semibold text-buy tabular-nums">{formatVND(p.price)}</p>}
            <dl className="mt-6 grid gap-0 text-sm">
              {specs.map(([label, value], i) => (
                <div
                  key={label}
                  className="flex justify-between gap-6 border-t border-white/10 py-2.5 motion-reduce:opacity-100!"
                  // Dòng thứ i hiện khi --p vượt qua mốc của nó; translate trượt nhẹ từ trái vào
                  style={{
                    opacity: `clamp(0, calc((var(--p) - ${0.12 + i * 0.1}) * 8), 1)`,
                    translate: `calc(clamp(0, calc((var(--p) - ${0.12 + i * 0.1}) * 8), 1) * 24px - 24px) 0`,
                  }}
                >
                  <dt className="text-white/50">{label}</dt>
                  <dd className="text-right font-medium">{value}</dd>
                </div>
              ))}
            </dl>
            {p && (
              <Link
                to={`/products/${p.slug}`}
                className="btn-glow mt-7 inline-flex h-12 items-center rounded-[13px] px-6 text-sm font-medium"
              >
                <span>Xem chi tiết</span>
              </Link>
            )}
          </div>
          <div className="order-1 md:order-2">
            <div
              className="mx-auto aspect-square w-[min(72vw,30rem)] overflow-hidden rounded-[2rem] bg-secondary shadow-[0_40px_120px_-30px_rgba(80,200,255,.45)] motion-reduce:scale-100! md:w-full md:max-w-xl"
              style={{ scale: "calc(0.78 + var(--p) * 0.26)", rotate: "calc((1 - var(--p)) * -4deg)" }}
            >
              {p ? (
                <ProductImage category={p.category} imageUrl={p.image_url} name={p.name} />
              ) : (
                <Skeleton className="size-full" />
              )}
            </div>
          </div>
        </div>
        {/* Thanh tiến trình mảnh ở đáy khung ghim */}
        <div aria-hidden className="absolute inset-x-0 bottom-0 h-px bg-white/10 motion-reduce:hidden">
          <div className="h-full origin-left bg-cyan-300" style={{ scale: "var(--p) 1" }} />
        </div>
      </div>
    </section>
  )
}

// Ghi --p (0 → 1) lên phần tử: đã cuộn qua bao nhiêu phần của nó (tính từ lúc mép trên chạm đỉnh màn hình)
function useScrollProgress(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const el = ref.current
    if (!el) return
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.style.setProperty("--p", "1")
      return
    }
    let raf = 0
    function update() {
      raf = 0
      const r = el!.getBoundingClientRect()
      const total = r.height - window.innerHeight
      const p = total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 1
      el!.style.setProperty("--p", p.toFixed(4))
    }
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update)
    }
    update()
    window.addEventListener("scroll", onScroll, { passive: true })
    window.addEventListener("resize", onScroll)
    return () => {
      window.removeEventListener("scroll", onScroll)
      window.removeEventListener("resize", onScroll)
      cancelAnimationFrame(raf)
    }
  }, [ref])
}

// ---------- Chương 4: các bước mua sắm — đường kẻ tự vẽ nối các bước ----------
const STEPS = [
  { icon: ShoppingCart, title: "Chọn món ưng ý", text: "Xem nhanh, so thông số, thêm vào giỏ." },
  {
    icon: ShieldCheck,
    title: "Đặt hàng",
    text: "Chọn COD hoặc trả trước. Đơn được kiểm tra an toàn tự động trong tích tắc.",
  },
  { icon: PackageCheck, title: "Nhận hàng", text: "Theo dõi trạng thái đơn ngay trong tài khoản." },
  {
    icon: MessageSquareText,
    title: "Cần hỗ trợ?",
    text: "Đơn bị hạn chế nhầm thì gửi khiếu nại, nhân viên sẽ xem xét.",
  },
]

function SafeSteps() {
  const ref = useRef<HTMLOListElement>(null)
  const shown = useInView(ref, { margin: "0px 0px -25% 0px" })
  return (
    <section aria-labelledby="cac-buoc">
      <Reveal>
        <SectionHeading id="cac-buoc" eyebrow="4 bước">
          Mua sắm an tâm, từ giỏ hàng tới tay bạn
        </SectionHeading>
      </Reveal>
      <ol ref={ref} data-shown={shown ? "" : undefined} className="relative mt-10 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
        {/* Đường nối các bước (chỉ trên màn hình rộng, khi 4 bước nằm một hàng) */}
        <span
          aria-hidden
          className="draw-line absolute top-6 right-[12%] left-[12%] hidden h-px bg-[linear-gradient(90deg,#ffd60a,#67e8f9)] lg:block"
        />
        {STEPS.map(({ icon: Icon, title, text }, i) => (
          <li
            key={title}
            className="reveal relative text-center"
            data-shown={shown ? "" : undefined}
            style={{ "--d": `${250 + i * 220}ms` } as CSSProperties}
          >
            <span className="relative mx-auto flex size-12 items-center justify-center rounded-full border bg-background shadow-sm">
              <Icon className="size-5" />
              <span className="absolute -top-1.5 -right-1.5 flex size-5 items-center justify-center rounded-full bg-foreground text-[11px] font-semibold text-background">
                {i + 1}
              </span>
            </span>
            <h3 className="mt-4 font-semibold">{title}</h3>
            <p className="mx-auto mt-1 max-w-56 text-sm leading-relaxed text-muted-foreground">{text}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}

// ---------- Chương 5: ưu đãi — thẻ kính trên nền có các mảng màu trôi chậm ----------
const VOUCHERS = [
  { code: "NGUOIMOI", value: "−50.000đ", cond: "Khách mới, đơn từ 200.000đ" },
  { code: "GIAM10", value: "−10%", cond: "Tối đa 100.000đ, đơn từ 500.000đ" },
]

function OfferCta() {
  const { data: user } = useMe()
  return (
    <Reveal
      as="section"
      variant="zoom"
      id="uu-dai"
      aria-labelledby="uu-dai-title"
      className="relative isolate scroll-mt-24 overflow-hidden rounded-[2.5rem] bg-[#0a1120] px-6 ring-1 ring-white/[.07] py-14 text-white sm:px-12 sm:py-20"
    >
      <div aria-hidden className="absolute inset-0 -z-10">
        <span className="absolute -top-24 -left-16 size-80 rounded-full bg-cyan-400/30 blur-3xl motion-safe:animate-[drift-blob_14s_ease-in-out_infinite]" />
        <span className="absolute -right-10 -bottom-28 size-96 rounded-full bg-yellow-300/25 blur-3xl motion-safe:animate-[drift-blob_18s_ease-in-out_infinite_reverse]" />
      </div>
      <div className="grid items-center gap-10 lg:grid-cols-[1fr_auto]">
        <div className="max-w-xl">
          <p className="text-xs font-semibold tracking-[0.2em] text-white/60 uppercase">Ưu đãi đang chạy</p>
          <h2 id="uu-dai-title" className="mt-3 text-3xl leading-tight font-semibold tracking-tight sm:text-5xl">
            Mã giảm giá thật, dành cho người mua thật.
          </h2>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link to="/danh-muc" className="btn-glow h-12 rounded-[13px] px-6 text-sm font-medium">
              <span>Mua sắm ngay</span>
            </Link>
            {!user && (
              <Link
                to="/register"
                className="flex h-12 items-center rounded-[13px] border border-white/15 px-5 text-sm text-white/85 transition hover:bg-white/5"
              >
                Tạo tài khoản
              </Link>
            )}
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:w-[30rem] lg:grid-cols-1">
          {VOUCHERS.map((v) => (
            <VoucherTicket key={v.code} {...v} />
          ))}
        </div>
      </div>
    </Reveal>
  )
}

function VoucherTicket({ code, value, cond }: { code: string; value: string; cond: string }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1800)
    } catch {
      // Trình duyệt chặn clipboard (ví dụ không phải HTTPS): người dùng vẫn đọc và gõ mã được
    }
  }
  return (
    <div className="flex items-center gap-4 rounded-3xl border border-white/10 bg-white/[.06] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,.08)] backdrop-blur-xl">
      <span className="min-w-20 text-center text-xl font-bold text-buy tabular-nums">{value}</span>
      <span className="h-10 border-l border-dashed border-white/20" aria-hidden />
      <span className="min-w-0 flex-1">
        <span className="block font-mono font-semibold tracking-wider">{code}</span>
        <span className="block text-xs text-white/60">{cond}</span>
      </span>
      <button
        type="button"
        onClick={copy}
        aria-label={copied ? `Đã chép mã ${code}` : `Chép mã ${code}`}
        className="flex size-10 shrink-0 items-center justify-center rounded-full bg-white/10 transition hover:bg-white/20"
      >
        {copied ? <Check className="size-4 text-emerald-300" /> : <Copy className="size-4" />}
      </button>
    </div>
  )
}

// ---------- Tiện ích ----------
function interleaveByCategory(items: Product[]): Product[] {
  const groups = new Map<string, Product[]>()
  for (const p of items) groups.set(p.category, [...(groups.get(p.category) ?? []), p])
  const queues = [...groups.values()]
  const result: Product[] = []
  while (queues.some((q) => q.length > 0)) {
    for (const q of queues) {
      const next = q.shift()
      if (next) result.push(next)
    }
  }
  return result
}

// Sản phẩm chủ lực: món đắt nhất còn hàng trong danh mục (có thì ưu tiên món có ảnh)
function flagship(items: Product[]): Product | undefined {
  return [...items]
    .filter((p) => p.stock > 0)
    .sort((a, b) => Number(!!b.image_url) - Number(!!a.image_url) || b.price - a.price)[0]
}
