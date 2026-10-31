import { ChevronRight, RotateCcw, ShieldCheck, Truck } from "lucide-react"
import { Link, useParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useProduct, useProducts, type Product } from "@/lib/api/catalog"
import { ApiError } from "@/lib/api/client"
import { formatVND } from "@/lib/format"
import { AddToCart } from "@/shop/components/AddToCart"
import { ProductCard } from "@/shop/components/ProductCard"
import { ProductImage } from "@/shop/components/ProductImage"

export function ProductDetailPage() {
  const { slug = "" } = useParams()
  const product = useProduct(slug)

  if (product.isPending) {
    return (
      <div className="grid gap-10 py-10 md:grid-cols-2" aria-busy="true">
        <Skeleton className="aspect-square w-full rounded-[2rem]" />
        <div className="grid content-start gap-4">
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-8 w-1/3" />
          <Skeleton className="h-24 w-full" />
        </div>
      </div>
    )
  }

  if (product.isError) {
    const notFound =
      product.error instanceof ApiError && product.error.status === 404
    return (
      <div className="py-20 text-center">
        <h1 className="text-2xl font-semibold">
          {notFound ? "Không tìm thấy sản phẩm" : "Không tải được sản phẩm"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {notFound ? "Sản phẩm có thể đã ngừng bán." : product.error.message}
        </p>
        <Button className="mt-6 rounded-full" asChild>
          <Link to="/">Về trang chủ</Link>
        </Button>
      </div>
    )
  }

  const p = product.data
  const outOfStock = p.stock <= 0

  return (
    <div className="pt-6">
      <nav
        aria-label="Vị trí trang"
        className="flex flex-wrap items-center gap-1 text-sm text-muted-foreground"
      >
        <Link to="/" className="hover:text-foreground">
          Trang chủ
        </Link>
        <ChevronRight className="size-4" />
        <Link
          to={`/danh-muc/${p.category}`}
          className="hover:text-foreground"
        >
          {p.category_name}
        </Link>
        <ChevronRight className="size-4" />
        <span className="text-foreground" aria-current="page">
          {p.name}
        </span>
      </nav>

      <div className="mt-6 grid gap-10 md:grid-cols-2 lg:gap-16">
        <div className="overflow-hidden rounded-[2rem] bg-secondary">
          <ProductImage
            category={p.category}
            imageUrl={p.image_url}
            name={p.name}
            iconClassName="size-32"
          />
        </div>

        <div className="flex flex-col gap-5 md:py-4">
          <div>
            <p className="text-xs font-medium tracking-widest text-muted-foreground uppercase">
              {p.category_name}
            </p>
            <h1 className="mt-2 text-3xl leading-tight font-semibold tracking-tight sm:text-4xl">
              {p.name}
            </h1>
            <p className="mt-2 font-mono text-xs text-muted-foreground">
              Mã sản phẩm: {p.sku}
            </p>
          </div>

          <p className="text-3xl font-semibold">{formatVND(p.price)}</p>

          <p className="flex items-center gap-2 text-sm">
            <span
              className={
                outOfStock
                  ? "size-2 rounded-full bg-destructive"
                  : "size-2 rounded-full bg-emerald-500"
              }
            />
            {outOfStock ? "Tạm hết hàng" : `Còn hàng (${p.stock} sản phẩm)`}
          </p>

          <p className="leading-relaxed text-muted-foreground">
            {p.description}
          </p>

          <AddToCart product={p} />

          <ul className="mt-2 grid gap-3 rounded-3xl bg-secondary p-5 text-sm">
            <li className="flex items-center gap-3">
              <Truck className="size-5 shrink-0" /> Giao hàng toàn quốc, thanh
              toán khi nhận hàng (COD) hoặc trả trước
            </li>
            <li className="flex items-center gap-3">
              <RotateCcw className="size-5 shrink-0" /> Đổi trả trong 7 ngày nếu
              lỗi do nhà sản xuất
            </li>
            <li className="flex items-center gap-3">
              <ShieldCheck className="size-5 shrink-0" /> Đơn hàng được kiểm tra
              an toàn trước khi giao
            </li>
          </ul>
        </div>
      </div>

      <div className="mt-16 grid gap-10 lg:grid-cols-[3fr_2fr]">
        {p.specs.length > 0 && (
          <section aria-labelledby="thong-so">
            <h2 id="thong-so" className="text-2xl font-semibold tracking-tight">
              Thông số kỹ thuật
            </h2>
            <dl className="mt-5 overflow-hidden rounded-3xl border">
              {p.specs.map(([label, value]) => (
                <div
                  key={label}
                  className="grid grid-cols-[minmax(7rem,2fr)_3fr] gap-4 px-5 py-3.5 text-sm odd:bg-secondary"
                >
                  <dt className="text-muted-foreground">{label}</dt>
                  <dd className="font-medium">{value}</dd>
                </div>
              ))}
            </dl>
          </section>
        )}
        <section aria-labelledby="mo-ta">
          <h2 id="mo-ta" className="text-2xl font-semibold tracking-tight">
            Mô tả
          </h2>
          <p className="mt-5 leading-relaxed text-muted-foreground">
            {p.description}
          </p>
        </section>
      </div>

      <RelatedProducts product={p} />
    </div>
  )
}

function RelatedProducts({ product }: { product: Product }) {
  const related = useProducts({
    category: product.category,
    page: 1,
    pageSize: 5,
  })
  const items =
    related.data?.items.filter((x) => x.id !== product.id).slice(0, 4) ?? []
  if (items.length === 0) return null
  return (
    <section aria-labelledby="cung-danh-muc" className="mt-20">
      <h2
        id="cung-danh-muc"
        className="text-2xl font-semibold tracking-tight sm:text-3xl"
      >
        Cùng danh mục {product.category_name.toLowerCase()}
      </h2>
      <div className="mt-6 grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-4">
        {items.map((x) => (
          <ProductCard key={x.id} product={x} />
        ))}
      </div>
    </section>
  )
}
