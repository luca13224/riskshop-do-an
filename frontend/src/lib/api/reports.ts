import { useQuery } from "@tanstack/react-query"

import { apiFetch } from "./client"
import type { Decision } from "./risk"

export interface Kpi {
  days: number
  decisions: {
    total: number
    by_decision: Record<Decision, number>
    by_context: Record<string, number>
    engine_errors: number
  }
  latency_ms: {
    samples: number
    p50: number | null
    p95: number | null
    p99: number | null
  }
  cases: {
    by_status: Record<
      "OPEN" | "IN_REVIEW" | "CONFIRMED_ABUSE" | "CLEARED",
      number
    >
    avg_resolve_minutes: number | null
  }
  impact: {
    voucher_saved_vnd: number
    voucher_blocked_accounts: number
    cod_restricted_customers: number
    orders_held: number
    orders_rejected_after_review: number
    cod_cost_avoided_vnd: number
    legit_customers_held_by_mistake: number
  }
  rules: {
    code: string
    name: string
    hits: number
    cases_confirmed: number
    cases_cleared: number
    precision: number | null
  }[]
  assumptions: string[]
}

export interface AuditEntry {
  id: number
  created_at: string
  action: string
  entity_type: string
  entity_id: string
  before_data: Record<string, unknown> | null
  after_data: Record<string, unknown> | null
  note: string | null
  actor_name: string | null
  actor_role: string | null
}

export function useKpi(days: number) {
  return useQuery({
    queryKey: ["console", "kpi", days],
    queryFn: () => apiFetch<Kpi>(`/api/console/reports/kpi?days=${days}`),
    refetchInterval: 10_000,
  })
}

export function useAuditLogs(entityType: string) {
  return useQuery({
    queryKey: ["console", "audit", entityType],
    queryFn: () =>
      apiFetch<AuditEntry[]>(
        `/api/console/audit?limit=200${entityType ? `&entity_type=${entityType}` : ""}`
      ),
  })
}
