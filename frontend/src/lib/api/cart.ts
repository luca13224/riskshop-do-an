import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { useMe } from "./auth"
import type { CategoryCode } from "./catalog"
import { apiFetch } from "./client"

// Khớp với schema CartOut bên backend (app/modules/cart/schemas.py)
export interface CartItem {
  product_id: number
  slug: string
  name: string
  category: CategoryCode
  image_url: string | null
  unit_price: number
  quantity: number
  stock: number
  line_total: number
}

export interface Cart {
  items: CartItem[]
  item_count: number
  subtotal: number
  discount: number
  total: number
  voucher: { code: string; description: string; discount: number } | null
  notice: string | null
}

const CART_KEY = ["cart"]

export function useCart() {
  const { data: user } = useMe()
  return useQuery({
    queryKey: CART_KEY,
    queryFn: () => apiFetch<Cart>("/api/cart"),
    enabled: user?.role === "customer", // chỉ khách hàng mới có giỏ
  })
}

// Mọi thao tác trên giỏ đều trả về giỏ mới nhất -> ghi thẳng vào cache, giao diện cập nhật ngay
function useCartMutation<TInput>(request: (input: TInput) => Promise<Cart>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: request,
    onSuccess: (cart) => queryClient.setQueryData(CART_KEY, cart),
  })
}

const post = (path: string, body?: unknown) =>
  apiFetch<Cart>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  })

export const useAddToCart = () =>
  useCartMutation((input: { product_id: number; quantity: number }) =>
    post("/api/cart/items", input)
  )

export const useUpdateCartItem = () =>
  useCartMutation(
    ({ product_id, quantity }: { product_id: number; quantity: number }) =>
      apiFetch<Cart>(`/api/cart/items/${product_id}`, {
        method: "PATCH",
        body: JSON.stringify({ quantity }),
      })
  )

export const useRemoveCartItem = () =>
  useCartMutation((product_id: number) =>
    apiFetch<Cart>(`/api/cart/items/${product_id}`, { method: "DELETE" })
  )

export const useApplyVoucher = () =>
  useCartMutation((code: string) => post("/api/cart/voucher", { code }))

export const useRemoveVoucher = () =>
  useCartMutation(() =>
    apiFetch<Cart>("/api/cart/voucher", { method: "DELETE" })
  )
