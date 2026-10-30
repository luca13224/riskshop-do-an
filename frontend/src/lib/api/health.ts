import { useQuery } from "@tanstack/react-query"

import { apiFetch } from "./client"

// Kiểu dữ liệu khớp với response của GET /api/health bên backend
export interface Health {
  status: "ok"
  db: "ok"
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiFetch<Health>("/api/health"),
    retry: false,
  })
}
