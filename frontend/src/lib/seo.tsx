// Thẻ SEO dùng chung. React 19 tự "kéo" <title>, <meta>, <link> lên <head> dù ta render chúng ở đâu
// trong cây component, nên không cần thư viện như react-helmet.
// Quy ước: MỖI trang chỉ render đúng MỘT <Seo> (do layout lo), nếu không <head> sẽ có hai <title>.

export const SITE_NAME = "RiskShop"

// Địa chỉ gốc để ghép URL tuyệt đối (canonical, og:url). Khi triển khai thật đặt VITE_SITE_URL trong .env.
export const SITE_URL = (
  (import.meta.env.VITE_SITE_URL as string | undefined) ?? window.location.origin
).replace(/\/$/, "")

export function absoluteUrl(path: string) {
  return path.startsWith("http") ? path : `${SITE_URL}${path}`
}

export interface SeoProps {
  title: string
  description?: string
  path: string // đường dẫn chuẩn (canonical) của trang, ví dụ "/products/tai-nghe-a"
  image?: string | null
  type?: "website" | "product"
  noindex?: boolean // trang riêng tư (giỏ hàng, đơn hàng, Console...): không cho máy tìm kiếm lập chỉ mục
  jsonLd?: object | object[] // dữ liệu có cấu trúc schema.org
}

export function Seo({ title, description, path, image, type = "website", noindex, jsonLd }: SeoProps) {
  const fullTitle = title === SITE_NAME ? title : `${title} | ${SITE_NAME}`
  const url = absoluteUrl(path)
  return (
    <>
      <title>{fullTitle}</title>
      <meta name="robots" content={noindex ? "noindex, nofollow" : "index, follow"} />
      {description && <meta name="description" content={description} />}
      {!noindex && <link rel="canonical" href={url} />}
      {!noindex && (
        <>
          <meta property="og:type" content={type} />
          <meta property="og:title" content={fullTitle} />
          <meta property="og:url" content={url} />
          {description && <meta property="og:description" content={description} />}
          {image && <meta property="og:image" content={absoluteUrl(image)} />}
          <meta name="twitter:card" content={image ? "summary_large_image" : "summary"} />
        </>
      )}
      {jsonLd && (
        <script
          type="application/ld+json"
          // Đổi "<" thành < để chuỗi dữ liệu (tên, mô tả sản phẩm) không thể tự đóng thẻ </script> (chống XSS)
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c") }}
        />
      )}
    </>
  )
}

// Rút gọn mô tả về ~160 ký tự (độ dài Google thường hiển thị), cắt ở ranh giới từ
export function clip(text: string, max = 160) {
  const t = text.replace(/\s+/g, " ").trim()
  if (t.length <= max) return t
  return t.slice(0, t.lastIndexOf(" ", max - 1)).replace(/[,.;:]$/, "") + "…"
}
