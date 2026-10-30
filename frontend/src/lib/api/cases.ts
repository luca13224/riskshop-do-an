import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { apiFetch } from "./client"
import type { RiskDecision } from "./risk"

// Khớp với schema bên backend (app/modules/cases/schemas.py)
export type CaseStatus = "OPEN" | "IN_REVIEW" | "CONFIRMED_ABUSE" | "CLEARED"
export type CaseFilter = "ACTIVE" | "CLOSED" | "ALL"

export interface CaseSummary {
  case_code: string
  policy: "voucher" | "cod"
  status: CaseStatus
  cluster_label: string
  primary_user_email: string
  decision_count: number
  max_score: number
  assigned_to_name: string | null
  opened_at: string
  closed_at: string | null
}

export interface CaseDetail extends CaseSummary {
  outcome_reason: string | null
  linked_accounts: {
    user_id: number
    email: string
    full_name: string
    created_at: string
    last_seen_at: string
  }[]
  decisions: RiskDecision[]
  actions: {
    action: string
    from_status: string | null
    to_status: string
    note: string
    staff_name: string | null
    created_at: string
  }[]
  order: {
    order_code: string
    status: string
    payment_method: string
    total: number
    created_at: string
    area: string
  } | null
}

export const CASE_STATUS_LABELS: Record<CaseStatus, string> = {
  OPEN: "Chờ nhận",
  IN_REVIEW: "Đang xử lý",
  CONFIRMED_ABUSE: "Xác nhận lạm dụng",
  CLEARED: "Không vi phạm",
}

export const POLICY_LABELS = { voucher: "Voucher", cod: "COD" }

export function useCases(filter: CaseFilter) {
  return useQuery({
    queryKey: ["console", "cases", filter],
    queryFn: () =>
      apiFetch<CaseSummary[]>(`/api/console/cases?status=${filter}`),
    refetchInterval: 5000, // case mới do worker mở sẽ tự hiện ra
  })
}

export function useCase(code: string) {
  return useQuery({
    queryKey: ["console", "case", code],
    queryFn: () =>
      apiFetch<CaseDetail>(`/api/console/cases/${encodeURIComponent(code)}`),
    retry: false,
  })
}

function useCaseMutation<TInput>(
  request: (input: TInput) => Promise<CaseDetail>
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: request,
    onSuccess: (detail) => {
      queryClient.setQueryData(["console", "case", detail.case_code], detail)
      queryClient.invalidateQueries({ queryKey: ["console", "cases"] })
    },
  })
}

export const useClaimCase = () =>
  useCaseMutation((code: string) =>
    apiFetch<CaseDetail>(
      `/api/console/cases/${encodeURIComponent(code)}/claim`,
      { method: "POST" }
    )
  )

export const useResolveCase = () =>
  useCaseMutation(
    ({
      code,
      outcome,
      note,
    }: {
      code: string
      outcome: "CONFIRMED_ABUSE" | "CLEARED"
      note: string
    }) =>
      apiFetch<CaseDetail>(
        `/api/console/cases/${encodeURIComponent(code)}/resolve`,
        {
          method: "POST",
          body: JSON.stringify({ outcome, note }),
        }
      )
  )
