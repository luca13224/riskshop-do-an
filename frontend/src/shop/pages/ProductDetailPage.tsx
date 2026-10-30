import { ArrowLeft, ShieldCheck, Truck } from "lucide-react"
import { Link, useParams } from "react-router"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useProduct } from "@/lib/api/catalog"
import { ApiError } from "@/lib/api/client"
import { formatVND } from "@/lib/format"
import { AddToCart } from "@/shop/components/AddToCart"
import { ProductImage } from "@/shop/components/ProductImage"

export function ProductDetailPage() {
  const { slug = "" } = useParams()
  const product = useProduct(slug)

  if (product.isPending) {
    return (
      <div className="grid gap-8 py-8 md:grid-cols-2" aria-busy="true">
        <Skeleton className="aspect-square w-full rounded-xl" />
        <div className="grid content-start gap-3">
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-7 w-1/3" />
          <Skeleton className="h-20 w-full" />
        </div>
      </div>
    )
  }

  if (product.isError) {
    const notFound =
      product.error instanceof ApiError && product.error.status === 404
    return (
      <div className="py-16 text-center">
        <h1 className="text-xl font-semibold">
          {notFound ? "Không tìm thấy sản phẩm" : "Không tải được sản phẩm"}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          {notFound ? "Sản phẩm có thể đã ngừng bán." : product.error.message}
        </p>
        <Button variant="outline" className="mt-6" asChild>
          <Link to="/">Về trang chủ</Link>
        </Button>
      </div>
    )
  }

  const p = product.data
  const outOfStock = p.stock <= 0

  return (
    <div className="py-6 pb-16">
      <Link
        to="/"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-4" /> Tiếp tục mua sắm
      </Link>

      <div className="mt-4 grid gap-8 md:grid-cols-2">
        <div className="mx-auto w-full max-w-sm overflow-hidden rounded-xl border md:max-w-none">
          <ProductImage
            category={p.category}
            imageUrl={p.image_url}
            name={p.name}
            iconClassName="size-24"
          />
        </div>

        <div className="flex flex-col gap-4">
          <div>
            <Link
              to={`/?category=${p.category}`}
              className="text-sm text-muted-foreground underline-offset-4 hover:underline"
            >
              {p.category_name}
            </Link>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
              {p.name}
            </h1>
            <p className="mt-1 font-mono text-xs text-muted-foreground">
              Mã: {p.sku}
            </p>
          </div>

          <p className="text-3xl font-semibold">{formatVND(p.price)}</p>

          <div>
            {outOfStock ? (
              <Badge variant="secondary">Hết hàng</Badge>
            ) : (
              <span className="text-sm text-muted-foreground">
                Còn {p.stock} sản phẩm
              </span>
            )}
          </div>

          <p className="leading-relaxed text-muted-foreground">
            {p.description}
          </p>

          <AddToCart product={p} />

          <ul className="mt-2 grid gap-2 text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <Truck className="size-4" /> Hỗ trợ thanh toán khi nhận hàng (COD)
            </li>
            <li className="flex items-center gap-2">
              <ShieldCheck className="size-4" /> Đơn hàng được kiểm tra an toàn
              trước khi giao
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
