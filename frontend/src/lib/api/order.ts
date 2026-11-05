import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import { useMe } from "./auth"
import { apiFetch } from "./client"

// Khớp với schema bên backend (app/modules/order/schemas.py)
export type OrderStatus =
  | "PENDING_REVIEW"
  | "CONFIRMED"
  | "SHIPPING"
  | "DELIVERED"
  | "DELIVERY_FAILED"
  | "CANCELLED"
  | "REJECTED"

export type PaymentMethod = "COD" | "PREPAID"

export interface Address {
  recipient_name: string
  phone: string
  line: string
  ward: string
  district: string
  province: string
}

export interface OrderItem {
  product_id: number
  product_name: string
  category: string
  unit_price: number
  quantity: number
  line_total: number
}

export interface Order {
  order_code: string
  status: OrderStatus
  payment_method: PaymentMethod
  payment_status: "PAID" | "UNPAID"
  subtotal: number
  discount: number
  total: number
  voucher_code: string | null
  created_at: string
  items: OrderItem[]
  address: Address
  events: { status: OrderStatus; note: string; occurred_at: string }[]
}

export interface OrderSummary {
  order_code: string
  status: OrderStatus
  payment_method: PaymentMethod
  total: number
  item_count: number
  created_at: string
}

export interface StaffOrder extends OrderSummary {
  customer_email: string
  customer_name: string
}

export const STATUS_LABELS: Record<OrderStatus, string> = {
  PENDING_REVIEW: "Chờ xác minh",
  CONFIRMED: "Đã xác nhận",
  SHIPPING: "Đang giao",
  DELIVERED: "Đã giao",
  DELIVERY_FAILED: "Giao thất bại",
  CANCELLED: "Đã hủy",
  REJECTED: "Bị từ chối",
}

export const PAYMENT_LABELS: Record<PaymentMethod, string> = {
  COD: "Thanh toán khi nhận hàng",
  PREPAID: "Trả trước (chuyển khoản)",
}

export function useCheckout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      idempotencyKey,
      ...body
    }: {
      idempotencyKey: string
      address: Address
      payment_method: PaymentMethod
    }) =>
      apiFetch<Order>("/api/orders/checkout", {
        method: "POST",
        body: JSON.stringify(body),
        headers: { "Idempotency-Key": idempotencyKey },
      }),
    onSuccess: (order) => {
      queryClient.setQueryData(["order", order.order_code], order)
      queryClient.invalidateQueries({ queryKey: ["cart"] })
      queryClient.invalidateQueries({ queryKey: ["orders"] })
    },
  })
}

export function useMyOrders() {
  const { data: user } = useMe()
  return useQuery({
    queryKey: ["orders"],
    queryFn: () => apiFetch<OrderSummary[]>("/api/orders"),
    enabled: user?.role === "customer", // chưa đăng nhập thì không gọi (tránh 401 thừa)
  })
}

export function useOrder(code: string) {
  return useQuery({
    queryKey: ["order", code],
    queryFn: () => apiFetch<Order>(`/api/orders/${encodeURIComponent(code)}`),
    retry: false,
  })
}

export interface StaffOrderPage {
  items: StaffOrder[]
  total: number
  page: number
  page_size: number
  status_counts: Partial<Record<OrderStatus, number>> // số đơn theo trạng thái, để chip lọc hiện con số
}

export interface StaffOrderFilters {
  status?: OrderStatus
  q?: string // mã đơn, email hoặc tên khách
  page?: number
}

export function useStaffOrders(filters: StaffOrderFilters) {
  const params = new URLSearchParams()
  if (filters.status) params.set("status", filters.status)
  if (filters.q) params.set("q", filters.q)
  params.set("page", String(filters.page ?? 1))
  params.set("page_size", "20")
  return useQuery({
    queryKey: ["console", "orders", filters],
    queryFn: () => apiFetch<StaffOrderPage>(`/api/console/orders?${params}`),
    placeholderData: keepPreviousData, // đổi bộ lọc: giữ bảng cũ (mờ đi) thay vì nháy skeleton
  })
}

export function useUpdateShipment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      code,
      status,
    }: {
      code: string
      status: "SHIPPING" | "DELIVERED" | "DELIVERY_FAILED"
    }) =>
      apiFetch<StaffOrder>(
        `/api/console/orders/${encodeURIComponent(code)}/shipment`,
        {
          method: "POST",
          body: JSON.stringify({ status }),
        }
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["console", "orders"] }),
  })
}

// Risk Engine (context payment_options): có cho thanh toán COD với giỏ hiện tại không
export function usePaymentOptions(enabled: boolean) {
  return useQuery({
    queryKey: ["payment-options"],
    queryFn: () =>
      apiFetch<{ cod_allowed: boolean; message: string | null }>(
        "/api/orders/payment-options"
      ),
    enabled,
    staleTime: 0,
  })
}
