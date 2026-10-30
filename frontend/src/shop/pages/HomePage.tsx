import {
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  RotateCcw,
  Search,
  ShieldCheck,
  Truck,
} from "lucide-react"
import {
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
  type RefObject,
} from "react"
import { Link, useSearchParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { useMe } from "@/lib/api/auth"
import {
  useCategories,
  useProducts,
  type CategoryCode,
  type Product,
} from "@/lib/api/catalog"
import { cn } from "@/lib/utils"
import { CategoryIcon } from "@/shop/components/CategoryIcon"
import { ProductCard } from "@/shop/components/ProductCard"

// Trang chủ theo nhịp các khối (ADR-005): banner → danh mục → nổi bật → câu chuyện → tất cả sản phẩm → cam kết.
// Banner hiện tại là bản tạm; tuần 2 sẽ thay bằng banner "rạp chiếu phim".
export function HomePage() {
  const [params, setParams] = useSearchParams()
  const category = (params.get("category") as CategoryCode | null) ?? undefined
  const productsRef = useRef<HTMLElement>(null)

  // Chọn danh mục từ bất kỳ khối nào: đổi URL rồi cuộn xuống phần sản phẩm
  function pickCategory(code: CategoryCode | null) {
    const p = new URLSearchParams(params)
    setOrDelete(p, "category", code)
    p.delete("page")
    setParams(p)
    productsRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  return (
    // Lưới 1 cột minmax(0,1fr): cột không bị nội dung cuộn ngang (hàng Nổi bật) kéo giãn ra ngoài màn hình
    <div className="grid grid-cols-[minmax(0,1fr)] gap-16 pt-6 sm:gap-20">
      <Hero />
      <CategoryTiles active={category} onPick={pickCategory} />
      <FeaturedRow />
      <StoryBanner />
      <AllProducts sectionRef={productsRef} onPickCategory={pickCategory} />
      <ServiceStrip />
    </div>
  )
}

// ---------- Banner (bản tạm, tông tối, nhấn cyan theo ADR-005) ----------
function Hero() {
  const { data: user } = useMe()
  return (
    <section className="relative isolate overflow-hidden rounded-[2rem] bg-[#06080d] px-6 py-14 text-white sm:px-12 sm:py-20">
      {/* Lưới chấm mờ + quầng sáng cyan: gợi hình bo mạch, chuẩn bị cho ẩn dụ "tín hiệu điện" */}
      <div
        aria-hidden
        className="absolute inset-0 -z-10 [background-image:radial-gradient(rgba(120,225,255,.35)_1px,transparent_1px)] [mask-image:radial-gradient(70%_80%_at_75%_40%,#000,transparent)] [background-size:22px_22px] opacity-40"
      />
      <div
        aria-hidden
        className="absolute -top-32 -right-24 -z-10 size-[28rem] rounded-full bg-cyan-400/25 blur-3xl"
      />
      <p className="text-sm font-medium text-cyan-200/90">
        {user
          ? `Xin chào, ${user.full_name}`
          : "Đồ công nghệ cho góc làm việc và giải trí"}
      </p>
      <h1 className="mt-3 max-w-2xl text-4xl leading-[1.05] font-semibold tracking-tight sm:text-6xl">
        Nâng cấp thiết bị,
        <br />
        mua sắm an tâm.
      </h1>
      <p className="mt-5 max-w-lg text-base text-white/70">
        Tai nghe, màn hình, laptop, phụ kiện. Mọi đơn hàng đều được kiểm tra an
        toàn trước khi giao, ưu đãi thật dành cho người dùng thật.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Button
          variant="buy"
          size="lg"
          className="h-12 rounded-full px-7 text-base"
          asChild
        >
          <a href="#san-pham">Mua sắm ngay</a>
        </Button>
        <Button
          variant="outline"
          size="lg"
          className="h-12 rounded-full border-white/25 bg-white/5 px-7 text-base text-white hover:bg-white/10 hover:text-white"
          asChild
        >
          <Link to={user ? "/cart" : "/register"}>
            {user ? "Xem giỏ hàng" : "Nhận ưu đãi tân thủ"}
          </Link>
        </Button>
      </div>
    </section>
  )
}

// ---------- Ô danh mục ----------
function CategoryTiles({
  active,
  onPick,
}: {
  active?: CategoryCode
  onPick: (code: CategoryCode) => void
}) {
  const categories = useCategories()
  return (
    <section aria-labelledby="danh-muc">
      <SectionHeading id="danh-muc">Danh mục</SectionHeading>
      <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {categories.isPending
          ? Array.from({ length: 6 }, (_, i) => (
              <Skeleton key={i} className="h-36 rounded-3xl" />
            ))
          : categories.data?.map((c) => {
              return (
                <button
                  key={c.code}
                  type="button"
                  onClick={() => onPick(c.code)}
                  aria-pressed={active === c.code}
                  className={cn(
                    "group flex flex-col items-start gap-6 rounded-3xl bg-secondary p-5 text-left transition hover:-translate-y-0.5",
                    active === c.code && "bg-foreground text-background"
                  )}
                >
                  <span
                    className={cn(
                      "flex size-11 items-center justify-center rounded-full bg-background transition group-hover:bg-buy",
                      active === c.code && "bg-buy text-buy-foreground"
                    )}
                  >
                    <CategoryIcon
                      category={c.code}
                      className="size-5"
                      strokeWidth={1.75}
                    />
                  </span>
                  <span>
                    <span className="block text-sm leading-snug font-semibold">
                      {c.name}
                    </span>
                    <span
                      className={cn(
                        "text-xs text-muted-foreground",
                        active === c.code && "text-background/60"
                      )}
                    >
                      {c.product_count} sản phẩm
                    </span>
                  </span>
                </button>
              )
            })}
      </div>
    </section>
  )
}

// ---------- Hàng "Nổi bật": cuộn ngang có điểm dừng (scroll-snap), nút mũi tên trên máy tính ----------
function FeaturedRow() {
  // Lấy cả danh mục rồi xếp xen kẽ theo danh mục, để hàng nổi bật có đủ loại thay vì 8 món cùng nhóm
  const products = useProducts({ page: 1, pageSize: 24 })
  const featured = interleaveByCategory(products.data?.items ?? []).slice(0, 8)
  const rowRef = useRef<HTMLDivElement>(null)

  function scrollBy(direction: 1 | -1) {
    const row = rowRef.current
    if (row)
      row.scrollBy({
        left: direction * row.clientWidth * 0.8,
        behavior: "smooth",
      })
  }

  return (
    <section aria-labelledby="noi-bat">
      <div className="flex items-end justify-between gap-4">
        <SectionHeading id="noi-bat">Nổi bật tuần này</SectionHeading>
        <div className="hidden gap-2 sm:flex">
          <RoundButton label="Xem sản phẩm trước" onClick={() => scrollBy(-1)}>
            <ArrowLeft className="size-5" />
          </RoundButton>
          <RoundButton
            label="Xem sản phẩm tiếp theo"
            onClick={() => scrollBy(1)}
          >
            <ArrowRight className="size-5" />
          </RoundButton>
        </div>
      </div>
      <div
        ref={rowRef}
        className="-mx-4 mt-6 flex snap-x snap-mandatory scroll-px-4 [scrollbar-width:none] gap-4 overflow-x-auto px-4 pb-2 sm:-mx-6 sm:scroll-px-6 sm:px-6"
      >
        {products.isPending
          ? Array.from({ length: 4 }, (_, i) => (
              <Skeleton
                key={i}
                className="aspect-[3/4] w-64 shrink-0 rounded-3xl"
              />
            ))
          : featured.map((p) => (
              <div
                key={p.id}
                className="w-[70%] shrink-0 snap-start sm:w-64 lg:w-[calc((100%-3*1rem)/4)]"
              >
                <ProductCard product={p} />
              </div>
            ))}
      </div>
    </section>
  )
}

// ---------- Banner câu chuyện, có "vết khuyết" chứa nút ----------
function StoryBanner() {
  return (
    <section className="relative isolate overflow-hidden rounded-[2rem] bg-[#0b0d12] text-white">
      <div
        aria-hidden
        className="absolute inset-0 -z-10 bg-[radial-gradient(60%_90%_at_85%_30%,rgba(255,214,10,.22),transparent_60%),radial-gradient(50%_70%_at_10%_100%,rgba(80,200,255,.18),transparent_60%)]"
      />
      <div className="max-w-xl px-6 py-14 pb-28 sm:px-12 sm:py-20">
        <p className="text-sm font-medium tracking-widest text-white/60 uppercase">
          Góc làm việc
        </p>
        <h2 className="mt-3 text-3xl leading-tight font-semibold tracking-tight sm:text-5xl">
          Một màn hình tốt
          <br />
          đổi cả ngày làm việc.
        </h2>
        <p className="mt-4 text-white/70">
          Màn hình 2K, màn hình cong UltraWide, đèn treo chống lóa. Chọn đúng
          thiết bị cho đôi mắt của bạn.
        </p>
      </div>
      <div className="notch py-3 pr-3 pl-4 [--r:1.75rem] sm:py-4 sm:pr-4 sm:pl-6">
        <Link
          to="/?category=monitor#san-pham"
          className="flex items-center gap-3 rounded-full py-1 pr-1 pl-2 text-sm font-semibold text-foreground"
        >
          Xem màn hình
          <span className="flex size-11 items-center justify-center rounded-full bg-buy text-buy-foreground">
            <ArrowRight className="size-5" />
          </span>
        </Link>
      </div>
    </section>
  )
}

// ---------- Tất cả sản phẩm: tìm kiếm, lọc, phân trang (bộ lọc nằm trên URL) ----------
function AllProducts({
  sectionRef,
  onPickCategory,
}: {
  sectionRef: RefObject<HTMLElement | null>
  onPickCategory: (code: CategoryCode | null) => void
}) {
  const [params, setParams] = useSearchParams()
  const q = params.get("q") ?? ""
  const category = (params.get("category") as CategoryCode | null) ?? undefined
  const page = Number(params.get("page") ?? "1") || 1
  const products = useProducts({ q, category, page })
  const categories = useCategories()

  function updateParams(next: { q?: string; page?: number }) {
    const p = new URLSearchParams(params)
    setOrDelete(p, "q", next.q)
    setOrDelete(
      p,
      "page",
      next.page && next.page > 1 ? String(next.page) : null
    )
    setParams(p)
  }

  const totalPages = products.data
    ? Math.max(1, Math.ceil(products.data.total / products.data.page_size))
    : 1

  return (
    <section
      id="san-pham"
      ref={sectionRef}
      aria-labelledby="tat-ca"
      className="scroll-mt-24"
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <SectionHeading id="tat-ca">Tất cả sản phẩm</SectionHeading>
        {/* key={q}: khi từ khóa trên URL đổi, React tạo lại ô tìm kiếm với giá trị mới */}
        <SearchForm
          key={q}
          initialQuery={q}
          onSearch={(text) => updateParams({ q: text, page: 1 })}
        />
      </div>

      <div className="mt-5 flex flex-wrap gap-2" aria-label="Lọc theo danh mục">
        <CategoryChip active={!category} onClick={() => onPickCategory(null)}>
          Tất cả
        </CategoryChip>
        {categories.data?.map((c) => (
          <CategoryChip
            key={c.code}
            active={category === c.code}
            onClick={() => onPickCategory(c.code)}
          >
            {c.name}
          </CategoryChip>
        ))}
      </div>

      <div className="mt-6">
        {products.isPending ? (
          <ProductGridSkeleton />
        ) : products.isError ? (
          <div className="rounded-3xl bg-secondary p-10 text-center">
            <p className="font-medium">Không tải được danh sách sản phẩm.</p>
            <p className="mt-1 text-sm text-muted-foreground">
              {products.error.message}
            </p>
            <Button
              variant="outline"
              className="mt-4 rounded-full"
              onClick={() => products.refetch()}
            >
              Thử lại
            </Button>
          </div>
        ) : products.data.items.length === 0 ? (
          <div className="rounded-3xl bg-secondary p-10 text-center">
            <p className="font-medium">Không có sản phẩm nào phù hợp.</p>
            <Button
              variant="outline"
              className="mt-4 rounded-full"
              onClick={() => setParams(new URLSearchParams())}
            >
              Xóa bộ lọc
            </Button>
          </div>
        ) : (
          <>
            <p className="mb-4 text-sm text-muted-foreground">
              {products.data.total} sản phẩm
            </p>
            <div
              className={cn(
                "grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4",
                products.isPlaceholderData && "opacity-60 transition-opacity"
              )}
            >
              {products.data.items.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
            {totalPages > 1 && (
              <nav
                className="mt-10 flex items-center justify-center gap-3"
                aria-label="Phân trang"
              >
                <RoundButton
                  label="Trang trước"
                  disabled={page <= 1}
                  onClick={() => updateParams({ page: page - 1 })}
                >
                  <ArrowLeft className="size-5" />
                </RoundButton>
                <span className="text-sm text-muted-foreground tabular-nums">
                  Trang {page} / {totalPages}
                </span>
                <RoundButton
                  label="Trang sau"
                  disabled={page >= totalPages}
                  onClick={() => updateParams({ page: page + 1 })}
                >
                  <ArrowRight className="size-5" />
                </RoundButton>
              </nav>
            )}
          </>
        )}
      </div>
    </section>
  )
}

// ---------- Dải cam kết ----------
const SERVICES = [
  {
    icon: Truck,
    title: "Giao hàng toàn quốc",
    text: "Thanh toán khi nhận hàng hoặc trả trước",
  },
  {
    icon: RotateCcw,
    title: "Đổi trả 7 ngày",
    text: "Lỗi do nhà sản xuất được đổi mới",
  },
  {
    icon: BadgeCheck,
    title: "Ưu đãi minh bạch",
    text: "Mã giảm giá áp dụng rõ điều kiện",
  },
  {
    icon: ShieldCheck,
    title: "Đơn hàng an toàn",
    text: "Mỗi đơn được kiểm tra rủi ro trước khi giao",
  },
]

function ServiceStrip() {
  return (
    <section
      aria-label="Cam kết"
      className="grid gap-6 rounded-[2rem] bg-secondary p-6 sm:grid-cols-2 sm:p-10 lg:grid-cols-4"
    >
      {SERVICES.map(({ icon: Icon, title, text }) => (
        <div key={title} className="flex items-start gap-4">
          <span className="flex size-12 shrink-0 items-center justify-center rounded-full bg-buy text-buy-foreground">
            <Icon className="size-5" />
          </span>
          <div>
            <p className="font-semibold">{title}</p>
            <p className="mt-0.5 text-sm text-muted-foreground">{text}</p>
          </div>
        </div>
      ))}
    </section>
  )
}

// ---------- Mảnh nhỏ dùng chung ----------
function SectionHeading({ id, children }: { id: string; children: ReactNode }) {
  return (
    <h2 id={id} className="text-2xl font-semibold tracking-tight sm:text-4xl">
      {children}
    </h2>
  )
}

function RoundButton({
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

function interleaveByCategory(items: Product[]): Product[] {
  const groups = new Map<string, Product[]>()
  for (const p of items)
    groups.set(p.category, [...(groups.get(p.category) ?? []), p])
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

// Đặt giá trị vào URL; giá trị rỗng/null thì xóa tham số đó. undefined nghĩa là "không đụng tới".
function setOrDelete(
  p: URLSearchParams,
  key: string,
  value: string | null | undefined
) {
  if (value === undefined) return
  if (value) {
    p.set(key, value)
  } else {
    p.delete(key)
  }
}

function SearchForm({
  initialQuery,
  onSearch,
}: {
  initialQuery: string
  onSearch: (text: string) => void
}) {
  const [text, setText] = useState(initialQuery)

  function submit(e: FormEvent) {
    e.preventDefault()
    onSearch(text.trim())
  }

  return (
    <form
      onSubmit={submit}
      className="flex w-full max-w-sm gap-2"
      role="search"
    >
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Tìm sản phẩm…"
          aria-label="Tìm sản phẩm"
          className="h-11 rounded-full bg-secondary pl-10"
        />
      </div>
      <Button type="submit" className="h-11 rounded-full px-5">
        Tìm
      </Button>
    </form>
  )
}

function CategoryChip({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "rounded-full bg-secondary px-4 py-2 text-sm transition hover:bg-[#e8e8e5]",
        active && "bg-foreground text-background hover:bg-foreground/90"
      )}
    >
      {children}
    </button>
  )
}

function ProductGridSkeleton() {
  return (
    <div
      className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4"
      aria-busy="true"
      aria-label="Đang tải"
    >
      {Array.from({ length: 8 }, (_, i) => (
        <Skeleton key={i} className="aspect-[3/4] w-full rounded-3xl" />
      ))}
    </div>
  )
}
