import { keepPreviousData, useQuery } from "@tanstack/react-query"

import { apiFetch } from "./client"

// Kiểu dữ liệu khớp với schema bên backend (app/modules/catalog/schemas.py)
export type CategoryCode =
  "audio" | "laptop" | "monitor" | "gear" | "phone" | "smart"

export interface Product {
  id: number
  sku: string
  slug: string
  name: string
  category: CategoryCode
  category_name: string
  description: string
  price: number
  image_url: string | null
  stock: number
  specs: [label: string, value: string][] // thông số kỹ thuật theo thứ tự hiển thị
}

// Generic: Page<Product> nghĩa là "một trang kết quả mà mỗi phần tử là Product"
export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface Category {
  code: CategoryCode
  name: string
  product_count: number
}

export interface ProductFilters {
  q?: string
  category?: CategoryCode
  page?: number
  pageSize?: number
}

export function useProducts(filters: ProductFilters) {
  const params = new URLSearchParams()
  if (filters.q) params.set("q", filters.q)
  if (filters.category) params.set("category", filters.category)
  params.set("page", String(filters.page ?? 1))
  params.set("page_size", String(filters.pageSize ?? 12))

  return useQuery({
    queryKey: ["products", filters],
    queryFn: () => apiFetch<Page<Product>>(`/api/products?${params}`),
    placeholderData: keepPreviousData, // giữ kết quả cũ trong lúc tải trang mới, tránh nhấp nháy
  })
}

export function useProduct(slug: string) {
  return useQuery({
    queryKey: ["product", slug],
    queryFn: () =>
      apiFetch<Product>(`/api/products/${encodeURIComponent(slug)}`),
    retry: false,
  })
}

export function useCategories() {
  return useQuery({
    queryKey: ["categories"],
    queryFn: () => apiFetch<Category[]>("/api/categories"),
    staleTime: 5 * 60_000,
  })
}
