import { resolve } from "node:path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    // Khi chạy dev, mọi request /api/... được chuyển sang backend FastAPI,
    // nên frontend gọi "/api/health" mà không cần ghi địa chỉ backend.
    proxy: {
      "/api": "http://127.0.0.1:8000",
      // SEO: robots.txt và sitemap.xml do backend sinh từ danh mục sản phẩm
      "/robots.txt": "http://127.0.0.1:8000",
      "/sitemap.xml": "http://127.0.0.1:8000",
    },
  },
})
