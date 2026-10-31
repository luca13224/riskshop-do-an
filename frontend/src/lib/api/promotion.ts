import { useQuery } from "@tanstack/react-query"

import { apiFetch } from "./client"

// Túi voucher của khách (bộ luật v3). Khớp với backend/app/modules/promotion/router.py
export type WalletStatus = "usable" | "used" | "locked" | "not_eligible"

export interface WalletItem {
  code: string
  description: string
  min_order_value: number
  granted: boolean // shop cấp riêng cho tài khoản (khác mã công khai)
  status: WalletStatus
}

// Nhãn cho khách: chung chung, không nhắc tới điểm tin cậy hay luật
export const WALLET_STATUS_LABELS: Record<WalletStatus, string> = {
  usable: "Dùng được",
  used: "Đã dùng",
  locked: "Tạm chưa áp dụng",
  not_eligible: "Chưa đủ điều kiện",
}

export function useWallet(enabled: boolean) {
  return useQuery({
    queryKey: ["wallet"],
    queryFn: () => apiFetch<WalletItem[]>("/api/vouchers/wallet"),
    enabled,
  })
}
