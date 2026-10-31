import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

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
  user_id: number
  user_email: string // đã che sẵn ở backend, ví dụ mi***@gmail.com
  user_name: string
  order_code: string | null
  hits: RuleHit[]
  trust: Trust | null // điểm tin cậy tài khoản lúc quyết định (bộ luật v3); null với quyết định cũ
  restriction: Restriction | null // quyết định này kích hoạt, hoặc bị chặn vì khóa mua hàng (ADR-010)
}

export type TrustTier = "normal" | "watch" | "restricted" | "review" | "critical"

export interface Trust {
  score: number
  tier: TrustTier
  deductions: { rule_code: string; rule_name: string; points: number }[]
}

export const TRUST_TIER_LABELS: Record<TrustTier, string> = {
  normal: "Bình thường",
  watch: "Theo dõi",
  restricted: "Hạn chế",
  review: "Xem xét",
  critical: "Rất thấp",
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
  restrict_account: "Khóa mua hàng",
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

// ---------- Quản lý luật ----------

export interface RuleVersion {
  version: number
  params: Record<string, unknown>
  contexts: RiskContext[]
  enabled: boolean
  reason_template: string
  change_note: string
  created_by_name: string | null
  created_at: string
}

export interface Rule {
  code: string
  name: string
  rule_type: "count_threshold_tiers" | "rate_threshold_tiers" | "compound"
  strength: RuleHit["strength"]
  policies: ("voucher" | "cod")[]
  hit_count_7d: number
  active: RuleVersion
}

export function useRules() {
  return useQuery({
    queryKey: ["console", "rules"],
    queryFn: () => apiFetch<Rule[]>("/api/console/risk/rules"),
  })
}

export function useRuleVersions(code: string, enabled: boolean) {
  return useQuery({
    queryKey: ["console", "rules", code, "versions"],
    queryFn: () =>
      apiFetch<RuleVersion[]>(`/api/console/risk/rules/${code}/versions`),
    enabled,
  })
}

export function useCreateRuleVersion() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      code,
      ...body
    }: {
      code: string
      params: Record<string, unknown>
      enabled: boolean
      change_note: string
    }) =>
      apiFetch<Rule>(`/api/console/risk/rules/${code}/versions`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["console", "rules"] }),
  })
}

// ---------- Đồ thị liên kết tài khoản ----------
export interface GraphNode {
  id: string
  type: "account" | "device" | "ip" | "address"
  label: string // email đã che / IP đã che / "phường, quận"
  // Chỉ có ở nút tài khoản
  user_id?: number
  root?: boolean
  age_days?: number
  is_new?: boolean
  worst_decision?: Decision | null
  max_score?: number
  confirmed_abuse?: boolean
  banned?: boolean // đang bị khóa mua hàng vô thời hạn (ADR-010/011)
  // Chỉ có ở nút điểm chung: số tài khoản nối tới
  accounts?: number
}

export interface LinkGraph {
  root: string
  nodes: GraphNode[]
  edges: { source: string; target: string }[]
  truncated: boolean
  summary: {
    accounts: number
    new_accounts: number
    restricted_accounts: number
    confirmed_abuse: number
    banned: number
    shared_points: number
    window_days: number
  }
}

export function useLinkGraph(userId: number | undefined) {
  return useQuery({
    queryKey: ["console", "risk", "graph", userId],
    queryFn: () => apiFetch<LinkGraph>(`/api/console/risk/graph/${userId}`),
    enabled: userId !== undefined,
  })
}

// ---------- Khóa quyền mua hàng (ADR-010) ----------

export type RestrictionKind = "purchase_cooldown" | "purchase_ban" | "purchase_linked"

export interface Restriction {
  kind: RestrictionKind
  since: string
  until: string | null // null: vô thời hạn
  reason: string
}

export const RESTRICTION_LABELS: Record<RestrictionKind, string> = {
  purchase_cooldown: "Tạm khóa mua hàng",
  purchase_ban: "Khóa mua hàng vô thời hạn",
  purchase_linked: "Khóa thanh toán do liên kết với tài khoản bị khóa",
}

export function useRestriction(userId: number) {
  return useQuery({
    queryKey: ["console", "risk", "restriction", userId],
    queryFn: () => apiFetch<Restriction | null>(`/api/console/risk/users/${userId}/restriction`),
  })
}

export function useLiftRestriction(userId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (reason: string) =>
      apiFetch<null>(`/api/console/risk/users/${userId}/restriction/lift`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["console", "risk", "restriction", userId] }),
  })
}

export function useBanUser(userId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (reason: string) =>
      apiFetch<Restriction>(`/api/console/risk/users/${userId}/restriction/ban`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["console", "risk", "restriction", userId] }),
  })
}
