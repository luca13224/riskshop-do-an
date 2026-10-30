import { Check, ShoppingCart } from "lucide-react"
import { useState } from "react"
import { Link, useLocation, useNavigate } from "react-router"

import { Button } from "@/components/ui/button"
import { useMe } from "@/lib/api/auth"
import { useAddToCart } from "@/lib/api/cart"
import type { Product } from "@/lib/api/catalog"

import { QuantityStepper } from "./QuantityStepper"

export function AddToCart({ product }: { product: Product }) {
  const { data: user } = useMe()
  const navigate = useNavigate()
  const location = useLocation()
  const addToCart = useAddToCart()
  const [quantity, setQuantity] = useState(1)
  const [added, setAdded] = useState(false)

  const outOfStock = product.stock <= 0
  const isCustomer = user?.role === "customer"

  function onAdd() {
    if (!user) {
      // Chưa đăng nhập: đưa sang trang đăng nhập, xong quay lại đúng sản phẩm này
      navigate(`/login?next=${encodeURIComponent(location.pathname)}`)
      return
    }
    setAdded(false)
    addToCart.mutate(
      { product_id: product.id, quantity },
      { onSuccess: () => setAdded(true) }
    )
  }

  if (user && !isCustomer) {
    return (
      <p className="text-sm text-muted-foreground">
        Tài khoản nhân viên không dùng giỏ hàng.
      </p>
    )
  }

  return (
    <div className="grid gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <QuantityStepper
          value={quantity}
          max={Math.max(1, Math.min(product.stock, 99))}
          onChange={setQuantity}
          disabled={outOfStock}
        />
        <Button
          variant="buy"
          size="lg"
          className="h-11 rounded-full px-6"
          onClick={onAdd}
          disabled={outOfStock || addToCart.isPending}
        >
          <ShoppingCart />
          {addToCart.isPending ? "Đang thêm…" : "Thêm vào giỏ"}
        </Button>
      </div>
      {addToCart.isError && (
        <p className="text-sm text-destructive" role="alert">
          {addToCart.error.message}
        </p>
      )}
      {added && !addToCart.isError && (
        <p
          className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400"
          role="status"
        >
          <Check className="size-4" /> Đã thêm vào giỏ.
          <Link to="/cart" className="font-medium underline underline-offset-4">
            Xem giỏ hàng
          </Link>
        </p>
      )}
    </div>
  )
}
