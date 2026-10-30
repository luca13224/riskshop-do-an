import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { ApiError, apiFetch } from "./client"

// Kiểu dữ liệu khớp với schema UserOut bên backend (app/modules/auth/schemas.py)
export type Role = "customer" | "analyst" | "risk_manager" | "admin"

export interface User {
  id: number
  email: string
  full_name: string
  phone: string | null
  role: Role
}

export interface LoginInput {
  email: string
  password: string
}

export interface RegisterInput extends LoginInput {
  full_name: string
  phone?: string
}

export const STAFF_ROLES: Role[] = ["analyst", "risk_manager", "admin"]

export const ROLE_LABELS: Record<Role, string> = {
  customer: "Khách hàng",
  analyst: "Analyst",
  risk_manager: "Risk Manager",
  admin: "Admin",
}

export function isStaff(user: User | null | undefined): boolean {
  return !!user && STAFF_ROLES.includes(user.role)
}

const ME_KEY = ["auth", "me"]

// Người dùng hiện tại. Trả về null nếu chưa đăng nhập (thay vì báo lỗi).
export function useMe() {
  return useQuery({
    queryKey: ME_KEY,
    queryFn: async () => {
      try {
        return await apiFetch<User>("/api/auth/me")
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) return null
        throw err
      }
    },
    staleTime: 60_000,
    retry: false,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: LoginInput) =>
      apiFetch<User>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: (user) => queryClient.setQueryData(ME_KEY, user),
  })
}

export function useRegister() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: RegisterInput) =>
      apiFetch<User>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: (user) => queryClient.setQueryData(ME_KEY, user),
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => apiFetch<void>("/api/auth/logout", { method: "POST" }),
    onSuccess: () => {
      queryClient.setQueryData(ME_KEY, null)
      queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== "auth" })
    },
  })
}
