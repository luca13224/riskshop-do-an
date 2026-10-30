import { Navigate, Route, Routes } from "react-router"

import { ScrollToTop } from "@/components/scroll-to-top"
import { ConsoleLayout } from "@/console/ConsoleLayout"
import { RequireStaff } from "@/console/RequireStaff"
import { ConsoleHomePage } from "@/console/pages/ConsoleHomePage"
import { ConsoleOrdersPage } from "@/console/pages/ConsoleOrdersPage"
import { LiveMonitorPage } from "@/console/pages/LiveMonitorPage"
import { ShopLayout } from "@/shop/ShopLayout"
import { CartPage } from "@/shop/pages/CartPage"
import { CheckoutPage } from "@/shop/pages/CheckoutPage"
import { OrderDetailPage } from "@/shop/pages/OrderDetailPage"
import { OrdersPage } from "@/shop/pages/OrdersPage"
import { HomePage } from "@/shop/pages/HomePage"
import { LoginPage } from "@/shop/pages/LoginPage"
import { ProductDetailPage } from "@/shop/pages/ProductDetailPage"
import { RegisterPage } from "@/shop/pages/RegisterPage"

// Bản đồ đường dẫn của cả ứng dụng: hai khu vực Shop (/) và Risk Console (/console)
export function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route element={<ShopLayout />}>
          <Route index element={<HomePage />} />
          <Route path="products/:slug" element={<ProductDetailPage />} />
          <Route path="cart" element={<CartPage />} />
          <Route path="checkout" element={<CheckoutPage />} />
          <Route path="orders" element={<OrdersPage />} />
          <Route path="orders/:code" element={<OrderDetailPage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
        </Route>

        <Route path="console" element={<RequireStaff />}>
          <Route element={<ConsoleLayout />}>
            <Route index element={<ConsoleHomePage />} />
            <Route path="orders" element={<ConsoleOrdersPage />} />
            <Route path="monitor" element={<LiveMonitorPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default App
