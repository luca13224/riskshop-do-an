import { useState } from "react"
import { useLocation, useNavigate } from "react-router"

import { useMe } from "@/lib/api/auth"
import { useAddToCart } from "@/lib/api/cart"
import type { Product } from "@/lib/api/catalog"

// Thêm nhanh 1 sản phẩm vào giỏ từ thẻ sản phẩm (không cần vào trang chi tiết).
// Chưa đăng nhập -> chuyển sang đăng nhập rồi quay lại đúng trang đang xem.
export function useQuickAdd(product: Product) {
  const { data: user } = useMe()
  const navigate = useNavigate()
  const location = useLocation()
  const addToCart = useAddToCart()
  const [added, setAdded] = useState(false)

  const canBuy = !user || user.role === "customer" // nhân viên không có giỏ hàng
  const outOfStock = product.stock <= 0

  function add() {
    if (!user) {
      navigate(
        `/login?next=${encodeURIComponent(location.pathname + location.search)}`
      )
      return
    }
    setAdded(false)
    addToCart.mutate(
      { product_id: product.id, quantity: 1 },
      {
        onSuccess: () => {
          setAdded(true)
          window.setTimeout(() => setAdded(false), 2000)
        },
      }
    )
  }

  return {
    add,
    canBuy,
    outOfStock,
    added,
    pending: addToCart.isPending,
    error: addToCart.isError ? addToCart.error.message : null,
  }
}
