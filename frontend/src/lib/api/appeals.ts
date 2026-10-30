import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { apiFetch } from "./client"
import type { RiskDecision } from "./risk"

// Khớp với app/modules/appeals/schemas.py
export type AppealPolicy = "voucher" | "cod"
export type AppealStatus = "OPEN" | "ACCEPTED" | "REJECTED"

export const APPEAL_STATUS_LABELS: Record<AppealStatus, string> = {
  OPEN: "Đang xem xét",
  ACCEPTED: "Được chấp nhận",
  REJECTED: "Không được chấp nhận",
}

export const POLICY_LABELS: Record<AppealPolicy, string> = {
  voucher: "Voucher",
  cod: "Thanh toán khi nhận hàng",
}

export interface Eligible {
  decision_id: string
  policy: AppealPolicy
  label: string
  context: string
  created_at: string
  order_code: string | null
  order_status: string | null
  open_appeal: string | null
}

export interface Appeal {
  appeal_code: string
  policy: AppealPolicy
  label: string
  status: AppealStatus
  message: string
  response: string | null
  order_code: string | null
  created_at: string
  resolved_at: string | null
}

export interface StaffAppeal extends Appeal {
  user_id: number
  user_email: string // đã che ở backend
  user_name: string
  handled_by_name: string | null
}

export interface StaffAppealDetail extends StaffAppeal {
  decision: RiskDecision | null
  active_exemptions: AppealPolicy[]
  other_appeals: number
}

// ---------- Khách hàng ----------
export const useEligible = () =>
  useQuery({
    queryKey: ["appeals", "eligible"],
    queryFn: () => apiFetch<Eligible[]>("/api/appeals/eligible"),
  })

export const useMyAppeals = () =>
  useQuery({
    queryKey: ["appeals", "mine"],
    queryFn: () => apiFetch<Appeal[]>("/api/appeals"),
  })

export function useCreateAppeal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: {
      decision_id: string
      policy: AppealPolicy
      message: string
    }) =>
      apiFetch<Appeal>("/api/appeals", {
        method: "POST",
        body: JSON.stringify(input),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["appeals"] }),
  })
}

// ---------- Nhân viên ----------
export const useStaffAppeals = (status: AppealStatus | "ALL") =>
  useQuery({
    queryKey: ["console", "appeals", status],
    queryFn: () =>
      apiFetch<StaffAppeal[]>(`/api/console/appeals?status=${status}`),
  })

export const useStaffAppeal = (code: string) =>
  useQuery({
    queryKey: ["console", "appeal", code],
    queryFn: () =>
      apiFetch<StaffAppealDetail>(
        `/api/console/appeals/${encodeURIComponent(code)}`
      ),
    retry: false,
  })

export function useResolveAppeal() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: {
      code: string
      outcome: "ACCEPTED" | "REJECTED"
      response: string
    }) =>
      apiFetch<StaffAppealDetail>(
        `/api/console/appeals/${encodeURIComponent(input.code)}/resolve`,
        {
          method: "POST",
          body: JSON.stringify({
            outcome: input.outcome,
            response: input.response,
          }),
        }
      ),
    onSuccess: (detail) => {
      queryClient.setQueryData(
        ["console", "appeal", detail.appeal_code],
        detail
      )
      queryClient.invalidateQueries({ queryKey: ["console", "appeals"] })
      queryClient.invalidateQueries({ queryKey: ["dashboard"] })
    },
  })
}
