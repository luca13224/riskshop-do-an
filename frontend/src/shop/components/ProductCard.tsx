import { Link } from "react-router"

import { Badge } from "@/components/ui/badge"
import type { Product } from "@/lib/api/catalog"
import { formatVND } from "@/lib/format"

import { ProductImage } from "./ProductImage"

export function ProductCard({ product }: { product: Product }) {
  const outOfStock = product.stock <= 0
  return (
    <Link
      to={`/products/${product.slug}`}
      className="group flex flex-col overflow-hidden rounded-xl border bg-card transition hover:-translate-y-0.5 hover:shadow-lg focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
    >
      <div className="relative overflow-hidden">
        <ProductImage
          category={product.category}
          imageUrl={product.image_url}
          name={product.name}
          className="transition duration-300 group-hover:scale-105"
        />
        {outOfStock && (
          <Badge variant="secondary" className="absolute top-2 left-2">
            Hết hàng
          </Badge>
        )}
      </div>
      <div className="flex flex-1 flex-col gap-1 p-3">
        <span className="text-xs text-muted-foreground">
          {product.category_name}
        </span>
        <h3 className="line-clamp-2 text-sm font-medium">{product.name}</h3>
        <p className="mt-auto pt-2 font-semibold">{formatVND(product.price)}</p>
      </div>
    </Link>
  )
}
