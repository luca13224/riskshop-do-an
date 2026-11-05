import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { BrowserRouter } from "react-router"

import "./index.css"
import App from "./App.tsx"
import { ThemeProvider } from "@/components/theme-provider.tsx"
import { ApiError } from "@/lib/api/client"

// QueryClient: "bộ nhớ đệm" cho dữ liệu lấy từ API, dùng chung toàn ứng dụng.
// Lỗi 4xx (chưa đăng nhập, không có quyền, không tìm thấy...) gọi lại cũng vẫn lỗi, nên không thử lại;
// chỉ thử lại tối đa 2 lần khi mất mạng hoặc lỗi máy chủ.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) =>
        !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failureCount < 2,
    },
  },
})

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>
)
