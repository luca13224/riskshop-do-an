import { Navigate, Route, Routes } from "react-router"

import { ScrollToTop } from "@/components/scroll-to-top"
import { ConsoleLayout } from "@/console/ConsoleLayout"
import { RequireRole } from "@/console/RequireRole"
import { RequireStaff } from "@/console/RequireStaff"
import { ConsoleHomePage } from "@/console/pages/ConsoleHomePage"
import { ConsoleOrdersPage } from "@/console/pages/ConsoleOrdersPage"
import { LiveMonitorPage } from "@/console/pages/LiveMonitorPage"
import { CasesPage } from "@/console/pages/CasesPage"
import { AttackLabPage } from "@/console/pages/AttackLabPage"
import { AppealDetailPage } from "@/console/pages/AppealDetailPage"
import { AppealsPage as ConsoleAppealsPage } from "@/console/pages/AppealsPage"
import { RulesPage } from "@/console/pages/RulesPage"
import { ReportsPage } from "@/console/pages/ReportsPage"
import { AuditLogPage } from "@/console/pages/AuditLogPage"
import { CaseDetailPage } from "@/console/pages/CaseDetailPage"
import { AUDIT_ROLES, LAB_ROLES } from "@/lib/api/auth"
import { CatalogPage } from "@/shop/pages/CatalogPage"
import { ShopLayout } from "@/shop/ShopLayout"
import { AppealsPage } from "@/shop/pages/AppealsPage"
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
          <Route path="danh-muc" element={<CatalogPage />} />
          <Route path="danh-muc/:code" element={<CatalogPage />} />
          <Route path="products/:slug" element={<ProductDetailPage />} />
          <Route path="cart" element={<CartPage />} />
          <Route path="checkout" element={<CheckoutPage />} />
          <Route path="orders" element={<OrdersPage />} />
          <Route path="appeals" element={<AppealsPage />} />
          <Route path="orders/:code" element={<OrderDetailPage />} />
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
        </Route>

        <Route path="console" element={<RequireStaff />}>
          <Route element={<ConsoleLayout />}>
            <Route index element={<ConsoleHomePage />} />
            <Route path="orders" element={<ConsoleOrdersPage />} />
            <Route path="monitor" element={<LiveMonitorPage />} />
            <Route path="cases" element={<CasesPage />} />
            <Route path="cases/:code" element={<CaseDetailPage />} />
            <Route path="appeals" element={<ConsoleAppealsPage />} />
            <Route path="appeals/:code" element={<AppealDetailPage />} />
            <Route element={<RequireRole roles={LAB_ROLES} />}>
              <Route path="lab" element={<AttackLabPage />} />
            </Route>
            <Route path="rules" element={<RulesPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route element={<RequireRole roles={AUDIT_ROLES} />}>
              <Route path="audit" element={<AuditLogPage />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default App
