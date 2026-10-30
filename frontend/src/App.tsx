import { Navigate, Route, Routes } from "react-router"

import { ConsoleLayout } from "@/console/ConsoleLayout"
import { RequireStaff } from "@/console/RequireStaff"
import { ConsoleHomePage } from "@/console/pages/ConsoleHomePage"
import { ShopLayout } from "@/shop/ShopLayout"
import { HomePage } from "@/shop/pages/HomePage"
import { LoginPage } from "@/shop/pages/LoginPage"
import { RegisterPage } from "@/shop/pages/RegisterPage"

// Bản đồ đường dẫn của cả ứng dụng: hai khu vực Shop (/) và Risk Console (/console)
export function App() {
  return (
    <Routes>
      <Route element={<ShopLayout />}>
        <Route index element={<HomePage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
      </Route>

      <Route path="console" element={<RequireStaff />}>
        <Route element={<ConsoleLayout />}>
          <Route index element={<ConsoleHomePage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
