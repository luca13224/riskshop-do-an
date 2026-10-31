import { ArrowLeft, ArrowRight, ChevronRight, Search, X } from "lucide-react"
import { useState, type CSSProperties, type FormEvent } from "react"
import { Link, useParams, useSearchParams } from "react-router"

import { Button } from "@/components/ui/button"
import { useCategories, useProducts, type CategoryCode } from "@/lib/api/catalog"
import { cn } from "@/lib/utils"
import { ProductGridSkeleton, RoundButton } from "@/shop/components/bits"
import { ProductCard } from "@/shop/components/ProductCard"
import { Reveal } from "@/shop/components/Reveal"

// Trang danh mục: /danh-muc (tất cả) và /danh-muc/:code. Mỗi danh mục có địa chỉ riêng (tốt cho SEO),
// từ khóa tìm kiếm và số trang nằm trên URL (?q=, ?page=) để chia sẻ link hay bấm Back đều giữ đúng.
export function CatalogPage() {
  const { code } = useParams()
  const [params, setParams] = useSearchParams()
  const q = params.get("q") ?? ""
  const page = Number(params.get("page") ?? "1") || 1
  const categories = useCategories()
  const category = categories.data?.find((c) => c.code === code)
  const products = useProducts({ q, category: code as CategoryCode | undefined, page })

  function update(next: { q?: string; page?: number }) {
    const p = new URLSearchParams(params)
    if (next.q !== undefined) {
      if (next.q) p.set("q", next.q)
      else p.delete("q")
    }
    if (next.page && next.page > 1) p.set("page", String(next.page))
    else p.delete("page")
    setParams(p)
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
          <Chip to={`/danh-muc${q ? `?q=${encodeURIComponent(q)}` : ""}`} active={!code}>
            Tất cả
          </Chip>
          {categories.data?.map((c) => (
            <Chip key={c.code} to={`/danh-muc/${c.code}${q ? `?q=${encodeURIComponent(q)}` : ""}`} active={code === c.code}>
              {c.name}
            </Chip>
          ))}
        </div>
        <SearchForm key={q} initialQuery={q} onSearch={(text) => update({ q: text, page: 1 })} />
      </div>

      <div className="mt-8">
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
            <Button variant="outline" className="mt-4 rounded-full" asChild>
              <Link to="/danh-muc">Xem tất cả sản phẩm</Link>
            </Button>
          </div>
        ) : (
          <>
            {/* key theo bộ lọc: đổi danh mục/trang là các thẻ "bước vào" lại từ đầu */}
            <div
              key={`${code}-${q}-${page}`}
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
