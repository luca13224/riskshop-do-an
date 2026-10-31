import { useLocation, useMatch, useSearchParams } from "react-router"

import { useCategories, useProduct, type Product } from "@/lib/api/catalog"
import { absoluteUrl, clip, Seo, SITE_NAME } from "@/lib/seo"

const HOME_DESCRIPTION =
  "RiskShop: đồ công nghệ chính hãng (tai nghe, laptop, màn hình, bàn phím, điện thoại, thiết bị thông minh). " +
  "Giao nhanh, đổi trả 7 ngày, thanh toán COD hoặc trả trước."

// Trang riêng tư hoặc không có nội dung cho máy tìm kiếm: chỉ cần tiêu đề tab + noindex
const PRIVATE_PAGES: [prefix: string, title: string][] = [
  ["/cart", "Giỏ hàng"],
  ["/checkout", "Thanh toán"],
  ["/orders", "Đơn hàng của tôi"],
  ["/appeals", "Khiếu nại"],
  ["/login", "Đăng nhập"],
  ["/register", "Đăng ký"],
]

// SEO cho toàn khu vực Shop, render một lần trong ShopLayout (xem quy ước ở lib/seo.tsx)
export function ShopSeo() {
  const { pathname } = useLocation()
  const productMatch = useMatch("/products/:slug")
  if (productMatch) return <ProductSeo slug={productMatch.params.slug ?? ""} />
  if (pathname === "/") return <HomeSeo />
  const priv = PRIVATE_PAGES.find(([prefix]) => pathname.startsWith(prefix))
  return <Seo title={priv?.[1] ?? SITE_NAME} path={pathname} noindex />
}

function HomeSeo() {
  const [params] = useSearchParams()
  const categories = useCategories()
  const code = params.get("category")
  const category = categories.data?.find((c) => c.code === code)

  // Trang kết quả tìm kiếm / trang 2, 3...: không lập chỉ mục để tránh nội dung trùng lặp
  const isListingVariant = params.has("q") || (params.get("page") ?? "1") !== "1"
  if (category) {
    return (
      <Seo
        title={`${category.name} chính hãng`}
        description={`${category.product_count} sản phẩm ${category.name.toLowerCase()} tại ${SITE_NAME}. Giá rõ ràng, giao nhanh, đổi trả 7 ngày.`}
        path={`/?category=${category.code}`}
        noindex={isListingVariant}
      />
    )
  }
  return (
    <Seo
      title={SITE_NAME}
      description={HOME_DESCRIPTION}
      path="/"
      noindex={isListingVariant}
      jsonLd={{
        "@context": "https://schema.org",
        "@type": "WebSite",
        name: SITE_NAME,
        url: absoluteUrl("/"),
        inLanguage: "vi",
      }}
    />
  )
}

function ProductSeo({ slug }: { slug: string }) {
  // Cùng queryKey với ProductDetailPage nên React Query dùng chung một request
  const product = useProduct(slug)
  if (!product.data) {
    return <Seo title="Sản phẩm" path={`/products/${slug}`} noindex={product.isError} />
  }
  const p = product.data
  return (
    <Seo
      title={p.name}
      description={clip(p.description || `${p.name} chính hãng tại ${SITE_NAME}.`)}
      path={`/products/${p.slug}`}
      image={p.image_url}
      type="product"
      jsonLd={[productJsonLd(p), breadcrumbJsonLd(p)]}
    />
  )
}

// Dữ liệu có cấu trúc schema.org/Product: giúp Google hiện giá, tình trạng còn hàng ngay ở kết quả tìm kiếm
function productJsonLd(p: Product) {
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: p.name,
    sku: p.sku,
    description: p.description || undefined,
    category: p.category_name,
    image: p.image_url ? [absoluteUrl(p.image_url)] : undefined,
    offers: {
      "@type": "Offer",
      url: absoluteUrl(`/products/${p.slug}`),
      price: p.price,
      priceCurrency: "VND",
      availability: p.stock > 0 ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
      itemCondition: "https://schema.org/NewCondition",
    },
  }
}

function breadcrumbJsonLd(p: Product) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Trang chủ", item: absoluteUrl("/") },
      { "@type": "ListItem", position: 2, name: p.category_name, item: absoluteUrl(`/?category=${p.category}`) },
      { "@type": "ListItem", position: 3, name: p.name },
    ],
  }
}
