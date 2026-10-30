import { keepPreviousData, useQuery } from "@tanstack/react-query"

import { apiFetch } from "./client"
import type { Decision, RiskContext } from "./risk"

// Khớp với reports.service.dashboard bên backend
export interface PeriodStats {
  orders: number
  gmv: number
  cod_orders: number
  voucher_orders: number
  new_customers: number
  decisions: number
  intervened: number
}

export type DayPoint = { date: string; orders: number; gmv: number } & Record<
  Decision,
  number
>

export interface Dashboard {
  days: number
  generated_at: string
  current: PeriodStats
  previous: PeriodStats
  series: DayPoint[]
  latency_p95_ms: number | null
  top_rules: { code: string; name: string | null; hits: number }[]
  attention: {
    open_cases: number
    in_review_cases: number
    stale_cases: number
    pending_orders: number
    failed_jobs: number
    risk_errors: number
  }
  recent_interventions: {
    public_id: string
    created_at: string
    context: RiskContext
    decision: Decision
    score: number
    user_email: string // đã che ở backend
    order_code: string | null
    case_code: string | null
  }[]
}

export function useDashboard(days: number) {
  return useQuery({
    queryKey: ["dashboard", days],
    queryFn: () => apiFetch<Dashboard>(`/api/console/dashboard?days=${days}`),
    refetchInterval: 30_000, // tự làm mới mỗi 30 giây
    placeholderData: keepPreviousData,
  })
}
