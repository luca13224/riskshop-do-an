import { useQuery } from "@tanstack/react-query"

import { apiFetch } from "./client"

// Khớp với schema DecisionOut bên backend (app/modules/risk/schemas.py)
export type Decision = "ALLOW" | "ALLOW_WITH_RESTRICTION" | "REVIEW" | "BLOCK"
export type RiskContext = "voucher_apply" | "payment_options" | "place_order"

export interface RuleHit {
  rule_code: string
  points: number
  strength: "strong" | "medium" | "weak" | "positive"
  reason_text: string
}

export interface RiskDecision {
  id: number
  public_id: string
  created_at: string
  context: RiskContext
  decision: Decision
  score: number
  policy_scores: Record<string, number>
  actions: Record<string, boolean>
  latency_ms: number
  error: string | null
  user_email: string
  user_name: string
  order_code: string | null
  hits: RuleHit[]
}

export const DECISION_LABELS: Record<Decision, string> = {
  ALLOW: "Cho phép",
  ALLOW_WITH_RESTRICTION: "Hạn chế",
  REVIEW: "Chờ duyệt",
  BLOCK: "Chặn",
}

export const CONTEXT_LABELS: Record<RiskContext, string> = {
  voucher_apply: "Áp voucher",
  payment_options: "Chọn thanh toán",
  place_order: "Đặt hàng",
}

export const ACTION_LABELS: Record<string, string> = {
  remove_voucher: "Gỡ voucher",
  disable_cod: "Tắt COD",
  hold_order: "Giữ đơn",
  block: "Chặn đơn",
  open_case: "Mở case",
}

// Live Monitor: hỏi server mỗi 2 giây (polling). Đủ "thời gian thực" cho MVP;
// sau này có thể đổi sang SSE để server tự đẩy dữ liệu xuống.
export function useRiskDecisions(live: boolean) {
  return useQuery({
    queryKey: ["console", "risk", "decisions"],
    queryFn: () =>
      apiFetch<RiskDecision[]>("/api/console/risk/decisions?limit=100"),
    refetchInterval: live ? 2000 : false,
  })
}
