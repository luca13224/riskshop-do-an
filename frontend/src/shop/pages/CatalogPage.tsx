import { ArrowLeft, ArrowRight, ChevronDown, ChevronRight, Search, X } from "lucide-react"
import { useState, type CSSProperties, type FormEvent } from "react"
import { Link, useParams, useSearchParams } from "react-router"

import { Button } from "@/components/ui/button"
import { useCategories, useProducts, type CategoryCode, type ProductSort } from "@/lib/api/catalog"
import { cn } from "@/lib/utils"
import { ProductGridSkeleton, RoundButton } from "@/shop/components/bits"
import { ProductCard } from "@/shop/components/ProductCard"
import { Reveal } from "@/shop/components/Reveal"

const SORTS: { value: ProductSort; label: string }[] = [
  { value: "new", label: "Mới nhất" },
  { value: "price_asc", label: "Giá thấp → cao" },
  { value: "price_desc", label: "Giá cao → thấp" },
]

// Khoảng giá dạng mốc sẵn (dễ bấm trên điện thoại hơn hai ô nhập số). Mã trên URL: ?gia=...
const PRICE_RANGES: { value: string; label: string; min?: number; max?: number }[] = [
  { value: "duoi-500k", label: "Dưới 500.000đ", max: 499_999 },
  { value: "500k-2tr", label: "500.000đ – 2 triệu", min: 500_000, max: 2_000_000 },
  { value: "2tr-10tr", label: "2 – 10 triệu", min: 2_000_001, max: 10_000_000 },
  { value: "tren-10tr", label: "Trên 10 triệu", min: 10_000_001 },
]

type Filters = { q?: string; page?: number; sort?: ProductSort; gia?: string | null }

// Trang danh mục: /danh-muc (tất cả) và /danh-muc/:code. Mỗi danh mục có địa chỉ riêng (tốt cho SEO).
// Từ khóa, sắp xếp, khoảng giá, số trang nằm trên URL (?q=, ?sort=, ?gia=, ?page=): chia sẻ link
// hay bấm Back đều giữ đúng; đổi danh mục vẫn giữ các bộ lọc còn lại.
export function CatalogPage() {
  const { code } = useParams()
  const [params, setParams] = useSearchParams()
  const q = params.get("q") ?? ""
  const page = Number(params.get("page") ?? "1") || 1
  const sort = (SORTS.find((s) => s.value === params.get("sort"))?.value ?? "new") as ProductSort
  const range = PRICE_RANGES.find((r) => r.value === params.get("gia"))
  const categories = useCategories()
  const category = categories.data?.find((c) => c.code === code)
  const products = useProducts({
    q,
    category: code as CategoryCode | undefined,
    page,
    sort,
    minPrice: range?.min,
    maxPrice: range?.max,
  })

  function update(next: Filters) {
    const p = new URLSearchParams(params)
    const put = (key: string, value: string | null | undefined) => {
      if (value === undefined) return
      if (value) p.set(key, value)
      else p.delete(key)
    }
    put("q", next.q)
    put("sort", next.sort === undefined ? undefined : next.sort === "new" ? null : next.sort)
    put("gia", next.gia)
    if (next.page && next.page > 1) p.set("page", String(next.page))
    else p.delete("page")
    setParams(p)
  }

  // Link sang danh mục khác: giữ từ khóa, sắp xếp, khoảng giá; về trang 1
  function categoryHref(target?: string) {
    const p = new URLSearchParams(params)
    p.delete("page")
    const qs = p.toString()
    return `/danh-muc${target ? `/${target}` : ""}${qs ? `?${qs}` : ""}`
  }

  const totalPages = products.data ? Math.max(1, Math.ceil(products.data.total / products.data.page_size)) : 1
  const unknownCategory = code && categories.data && !category

  return (
    <div className="pt-6">
      <nav aria-label="Vị trí trang" className="flex flex-wrap items-center gap-1 text-sm text-muted-foreground">
        <Link to="/" className="hover:text-foreground">
          Trang chủ
        </Link>
        <ChevronRight className="size-4" />
        {category ? (
          <>
            <Link to="/danh-muc" className="hover:text-foreground">
              Sản phẩm
            </Link>
            <ChevronRight className="size-4" />
            <span className="text-foreground" aria-current="page">
              {category.name}
            </span>
          </>
        ) : (
          <span className="text-foreground" aria-current="page">
            Sản phẩm
          </span>
        )}
      </nav>

      {/* Dải đầu trang: ảnh danh mục mờ phía sau tiêu đề */}
      <header className="relative isolate mt-5 overflow-hidden rounded-[2rem] bg-[#0b1322] px-6 ring-1 ring-white/[.06] py-10 text-white sm:px-10 sm:py-14">
        {category && (
          <img
            key={category.code}
            src={`/categories/${category.code}.webp`}
            alt=""
            className="reveal absolute inset-y-0 right-0 -z-10 h-full w-full object-cover opacity-45 [mask-image:linear-gradient(90deg,transparent,black_60%)] sm:w-2/3"
            data-variant="zoom"
            data-shown=""
          />
        )}
        <div
          aria-hidden
          className="absolute inset-0 -z-20 bg-[radial-gradient(60%_90%_at_85%_30%,rgba(255,214,10,.18),transparent_60%),radial-gradient(50%_70%_at_10%_100%,rgba(80,200,255,.16),transparent_60%)]"
        />
        <p className="rise text-xs font-semibold tracking-[0.2em] text-white/60 uppercase">
          {category ? "Danh mục" : "Cửa hàng"}
        </p>
        <h1 className="rise mt-2 text-3xl font-semibold tracking-tight sm:text-5xl" style={{ "--d": "80ms" } as CSSProperties}>
          {category?.name ?? (unknownCategory ? "Không có danh mục này" : "Tất cả sản phẩm")}
        </h1>
        <p className="rise mt-3 text-sm text-white/65 sm:text-base" style={{ "--d": "160ms" } as CSSProperties}>
          {products.data ? `${products.data.total} sản phẩm` : "Đang tải…"}
          {q && ` cho “${q}”`}
        </p>
      </header>

      {/* Thanh lọc: chip danh mục cuộn ngang trên điện thoại + ô tìm kiếm */}
      <div className="mt-6 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div
          className="-mx-4 flex gap-2 overflow-x-auto px-4 [scrollbar-width:none] lg:mx-0 lg:flex-wrap lg:px-0"
          aria-label="Lọc theo danh mục"
          data-lenis-prevent
        >
          <Chip to={categoryHref()} active={!code}>
            Tất cả
          </Chip>
          {categories.data?.map((c) => (
            <Chip key={c.code} to={categoryHref(c.code)} active={code === c.code}>
              {c.name}
            </Chip>
          ))}
        </div>
        <SearchForm key={q} initialQuery={q} onSearch={(text) => update({ q: text, page: 1 })} />
      </div>

      {/* Hàng thứ hai: bộ lọc đang áp dụng (bấm để gỡ từng cái) + khoảng giá + sắp xếp */}
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex min-h-9 flex-wrap items-center gap-2 text-sm" aria-live="polite">
          {q || range ? (
            <>
              <span className="text-muted-foreground">Đang lọc:</span>
              {q && <ActiveFilter label={`“${q}”`} onRemove={() => update({ q: "", page: 1 })} />}
              {range && <ActiveFilter label={range.label} onRemove={() => update({ gia: null, page: 1 })} />}
              <button
                type="button"
                onClick={() => update({ q: "", gia: null, page: 1 })}
                className="text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
              >
                Xóa tất cả
              </button>
            </>
          ) : (
            <span className="text-muted-foreground">
              {products.data ? `${products.data.total} sản phẩm` : ""}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <SelectBox
            label="Khoảng giá"
            value={range?.value ?? ""}
            onChange={(v) => update({ gia: v || null, page: 1 })}
            options={[{ value: "", label: "Mọi mức giá" }, ...PRICE_RANGES]}
          />
          <SelectBox
            label="Sắp xếp"
            value={sort}
            onChange={(v) => update({ sort: v as ProductSort, page: 1 })}
            options={SORTS}
          />
        </div>
      </div>

      <div className="mt-6">
        {products.isPending ? (
          <ProductGridSkeleton />
        ) : products.isError ? (
          <div className="rounded-3xl bg-secondary p-10 text-center">
            <p className="font-medium">Không tải được danh sách sản phẩm.</p>
            <p className="mt-1 text-sm text-muted-foreground">{products.error.message}</p>
            <Button variant="outline" className="mt-4 rounded-full" onClick={() => products.refetch()}>
              Thử lại
            </Button>
          </div>
        ) : products.data.items.length === 0 ? (
          <div className="rounded-3xl bg-secondary p-10 text-center">
            <p className="font-medium">Không có sản phẩm nào phù hợp.</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Thử bỏ bớt bộ lọc, hoặc xem các danh mục khác.
            </p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {(q || range) && (
                <Button className="rounded-full" onClick={() => update({ q: "", gia: null, page: 1 })}>
                  Xóa bộ lọc
                </Button>
              )}
              <Button variant="outline" className="rounded-full" asChild>
                <Link to="/danh-muc">Xem tất cả sản phẩm</Link>
              </Button>
            </div>
          </div>
        ) : (
          <>
            {/* key theo bộ lọc: đổi danh mục/trang là các thẻ "bước vào" lại từ đầu */}
            <div
              key={`${code}-${q}-${page}-${sort}-${range?.value ?? ""}`}
              className={cn(
                "grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4",
                products.isPlaceholderData && "opacity-60 transition-opacity"
              )}
            >
              {products.data.items.map((p, i) => (
                <Reveal key={p.id} delay={(i % 4) * 70}>
                  <ProductCard product={p} />
                </Reveal>
              ))}
            </div>
            {totalPages > 1 && (
              <nav className="mt-10 flex items-center justify-center gap-3" aria-label="Phân trang">
                <RoundButton label="Trang trước" disabled={page <= 1} onClick={() => update({ page: page - 1 })}>
                  <ArrowLeft className="size-5" />
                </RoundButton>
                <span className="text-sm text-muted-foreground tabular-nums">
                  Trang {page} / {totalPages}
                </span>
                <RoundButton
                  label="Trang sau"
                  disabled={page >= totalPages}
                  onClick={() => update({ page: page + 1 })}
                >
                  <ArrowRight className="size-5" />
                </RoundButton>
              </nav>
            )}
          </>
        )}
      </div>
    </div>
  )
}

function ActiveFilter({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <button
      type="button"
      onClick={onRemove}
      aria-label={`Bỏ bộ lọc ${label}`}
      className="flex items-center gap-1.5 rounded-full border border-cyan-300/30 bg-cyan-300/10 py-1 pr-2 pl-3 text-cyan-100 transition hover:bg-cyan-300/20"
    >
      {label}
      <X className="size-3.5" />
    </button>
  )
}

// <select> gốc của trình duyệt: dùng tốt bằng bàn phím và trên điện thoại (bật bảng chọn của hệ điều hành)
function SelectBox({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: { value: string; label: string }[]
}) {
  return (
    <label className="relative flex-1 sm:flex-none">
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-10 w-full cursor-pointer appearance-none rounded-full bg-secondary py-0 pr-9 pl-4 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring sm:w-auto"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-muted-foreground" />
    </label>
  )
}

function Chip({ to, active, children }: { to: string; active: boolean; children: string }) {
  return (
    <Link
      to={to}
      aria-current={active ? "page" : undefined}
      className={cn(
        "shrink-0 rounded-full bg-secondary px-4 py-2 text-sm whitespace-nowrap transition hover:bg-accent",
        active && "bg-foreground text-background hover:bg-foreground/90"
      )}
    >
      {children}
    </Link>
  )
}

function SearchForm({ initialQuery, onSearch }: { initialQuery: string; onSearch: (text: string) => void }) {
  const [text, setText] = useState(initialQuery)
  function submit(e: FormEvent) {
    e.preventDefault()
    onSearch(text.trim())
  }
  return (
    <form onSubmit={submit} className="flex w-full gap-2 lg:max-w-sm" role="search">
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute top-1/2 left-4 size-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Tìm trong cửa hàng…"
          aria-label="Tìm sản phẩm"
          className="h-11 w-full rounded-full bg-secondary pr-10 pl-10 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        {text && (
          <button
            type="button"
            aria-label="Xóa từ khóa"
            onClick={() => {
              setText("")
              onSearch("")
            }}
            className="absolute top-1/2 right-3 -translate-y-1/2 rounded-full p-1 text-muted-foreground hover:bg-background"
          >
            <X className="size-4" />
          </button>
        )}
      </div>
      <Button type="submit" className="h-11 rounded-full px-5">
        Tìm
      </Button>
    </form>
  )
}
