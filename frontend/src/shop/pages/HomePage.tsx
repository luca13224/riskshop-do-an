import { Search } from "lucide-react"
import { useState, type FormEvent, type ReactNode } from "react"
import { useSearchParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { useMe } from "@/lib/api/auth"
import {
  useCategories,
  useProducts,
  type CategoryCode,
} from "@/lib/api/catalog"
import { cn } from "@/lib/utils"
import { ProductCard } from "@/shop/components/ProductCard"

export function HomePage() {
  const { data: user } = useMe()
  // Bộ lọc nằm trên URL (?q=...&category=...&page=...): tải lại trang hay gửi link vẫn giữ đúng kết quả
  const [params, setParams] = useSearchParams()
  const q = params.get("q") ?? ""
  const category = (params.get("category") as CategoryCode | null) ?? undefined
  const page = Number(params.get("page") ?? "1") || 1

  const products = useProducts({ q, category, page })
  const categories = useCategories()

  function updateParams(next: {
    q?: string
    category?: CategoryCode | null
    page?: number
  }) {
    const p = new URLSearchParams(params)
    setOrDelete(p, "q", next.q)
    setOrDelete(p, "category", next.category)
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
    <div className="pb-16">
      <section className="py-10 sm:py-14">
        <p className="text-sm font-medium text-muted-foreground">
          {user ? `Xin chào, ${user.full_name}!` : "Chào mừng tới RiskShop"}
        </p>
        <h1 className="mt-2 max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl">
          Mua sắm an tâm, ưu đãi thật cho người dùng thật.
        </h1>
        {/* key={q}: khi từ khóa trên URL đổi (ví dụ bấm "Xóa bộ lọc"), React tạo lại ô tìm kiếm
            với giá trị mới, thay vì phải đồng bộ bằng useEffect */}
        <SearchForm
          key={q}
          initialQuery={q}
          onSearch={(text) => updateParams({ q: text, page: 1 })}
        />
      </section>

      <div className="mb-6 flex flex-wrap gap-2" aria-label="Danh mục">
        <CategoryChip
          active={!category}
          onClick={() => updateParams({ category: null, page: 1 })}
        >
          Tất cả
        </CategoryChip>
        {categories.data?.map((c) => (
          <CategoryChip
            key={c.code}
            active={category === c.code}
            onClick={() => updateParams({ category: c.code, page: 1 })}
          >
            {c.name}{" "}
            <span className="text-muted-foreground">({c.product_count})</span>
          </CategoryChip>
        ))}
      </div>

      {products.isPending ? (
        <ProductGridSkeleton />
      ) : products.isError ? (
        <div className="rounded-xl border p-8 text-center">
          <p className="font-medium">Không tải được danh sách sản phẩm.</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {products.error.message}
          </p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => products.refetch()}
          >
            Thử lại
          </Button>
        </div>
      ) : products.data.items.length === 0 ? (
        <div className="rounded-xl border p-8 text-center">
          <p className="font-medium">Không có sản phẩm nào phù hợp.</p>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() => setParams(new URLSearchParams())}
          >
            Xóa bộ lọc
          </Button>
        </div>
      ) : (
        <>
          <p className="mb-3 text-sm text-muted-foreground">
            {products.data.total} sản phẩm
          </p>
          <div
            className={cn(
              "grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4",
              products.isPlaceholderData && "opacity-60 transition-opacity"
            )}
          >
            {products.data.items.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
          {totalPages > 1 && (
            <nav
              className="mt-8 flex items-center justify-center gap-3"
              aria-label="Phân trang"
            >
              <Button
                variant="outline"
                disabled={page <= 1}
                onClick={() => updateParams({ page: page - 1 })}
              >
                Trang trước
              </Button>
              <span className="text-sm text-muted-foreground">
                Trang {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                disabled={page >= totalPages}
                onClick={() => updateParams({ page: page + 1 })}
              >
                Trang sau
              </Button>
            </nav>
          )}
        </>
      )}
    </div>
  )
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
    <form onSubmit={submit} className="mt-6 flex max-w-lg gap-2" role="search">
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Tìm sản phẩm…"
          aria-label="Tìm sản phẩm"
          className="pl-9"
        />
      </div>
      <Button type="submit">Tìm</Button>
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
        "rounded-full border px-3 py-1.5 text-sm transition hover:bg-muted",
        active &&
          "border-foreground bg-foreground text-background hover:bg-foreground/90"
      )}
    >
      {children}
    </button>
  )
}

function ProductGridSkeleton() {
  return (
    <div
      className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4"
      aria-busy="true"
      aria-label="Đang tải"
    >
      {Array.from({ length: 8 }, (_, i) => (
        <div key={i} className="overflow-hidden rounded-xl border">
          <Skeleton className="aspect-square w-full rounded-none" />
          <div className="grid gap-2 p-3">
            <Skeleton className="h-3 w-1/3" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  )
}
