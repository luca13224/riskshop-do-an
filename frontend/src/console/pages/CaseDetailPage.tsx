import { ArrowLeft, Link2, ShieldCheck, ShieldX } from "lucide-react"
import { useState } from "react"
import { Link, useParams } from "react-router"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { CaseStatusBadge } from "@/console/components/CaseStatusBadge"
import { DecisionBadge, ScoreBar } from "@/console/components/DecisionBadge"
import { DecisionDetail } from "@/console/components/DecisionDetail"
import { useMe } from "@/lib/api/auth"
import {
  CASE_STATUS_LABELS,
  POLICY_LABELS,
  useCase,
  useClaimCase,
  useResolveCase,
  type CaseDetail,
  type CaseStatus,
} from "@/lib/api/cases"
import { STATUS_LABELS, type OrderStatus } from "@/lib/api/order"
import { CONTEXT_LABELS } from "@/lib/api/risk"
import { formatDateTime, formatVND } from "@/lib/format"
import { OrderStatusBadge } from "@/shop/components/OrderStatusBadge"

const ACTION_TEXT: Record<string, string> = {
  open: "Hệ thống mở case",
  claim: "Nhận xử lý",
  resolve: "Kết luận",
}

export function CaseDetailPage() {
  const { code = "" } = useParams()
  const kase = useCase(code)

  if (kase.isPending) return <Skeleton className="h-96 w-full rounded-xl" />
  if (kase.isError) {
    return (
      <div className="grid gap-4">
        <p className="text-destructive">{kase.error.message}</p>
        <Link to="/console/cases" className="text-sm underline">
          Về danh sách case
        </Link>
      </div>
    )
  }

  const c = kase.data
  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link
            to="/console/cases"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="size-4" /> Danh sách case
          </Link>
          <h1 className="mt-1 font-mono text-2xl font-semibold">
            {c.case_code}
          </h1>
          <p className="text-sm text-muted-foreground">
            {POLICY_LABELS[c.policy]} · {c.cluster_label} · mở lúc{" "}
            {formatDateTime(c.opened_at)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <ScoreBar score={c.max_score} />
          <CaseStatusBadge status={c.status} />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <div className="grid content-start gap-6">
          {c.order && (
            <Card>
              <CardHeader>
                <CardTitle>Đơn hàng đang chờ xác minh</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap items-center justify-between gap-3 text-sm">
                <div>
                  <p className="font-mono font-medium">{c.order.order_code}</p>
                  <p className="text-muted-foreground">
                    {c.order.payment_method} · {formatVND(c.order.total)} · giao
                    tới {c.order.area}
                  </p>
                </div>
                <OrderStatusBadge status={c.order.status as OrderStatus} />
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>
                Bằng chứng: các quyết định rủi ro ({c.decisions.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
              {c.decisions.map((d) => (
                <div key={d.id} className="grid gap-3 rounded-lg border p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                    <span>
                      <span className="font-medium">{d.user_name}</span>{" "}
                      <span className="text-muted-foreground">
                        · {CONTEXT_LABELS[d.context]} ·{" "}
                        {formatDateTime(d.created_at)}
                      </span>
                    </span>
                    <span className="flex items-center gap-3">
                      <ScoreBar score={d.score} />
                      <DecisionBadge decision={d.decision} />
                    </span>
                  </div>
                  <DecisionDetail decision={d} />
                </div>
              ))}
            </CardContent>
          </Card>

          {c.linked_accounts.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Link2 className="size-5" /> Tài khoản cùng thiết bị (
                  {c.linked_accounts.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="grid gap-2 text-sm">
                  {c.linked_accounts.map((a) => (
                    <li
                      key={a.user_id}
                      className="flex flex-wrap justify-between gap-2 border-b pb-2 last:border-0"
                    >
                      <span>
                        {a.full_name}{" "}
                        <span className="text-muted-foreground">
                          · {a.email}
                        </span>
                      </span>
                      <span className="text-muted-foreground">
                        tạo lúc {formatDateTime(a.created_at)}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="grid content-start gap-6">
          <ActionPanel kase={c} />
          <Card>
            <CardHeader>
              <CardTitle>Lịch sử xử lý</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="grid gap-3 border-l pl-4 text-sm">
                {c.actions.map((a, i) => (
                  <li key={i}>
                    <p className="font-medium">
                      {ACTION_TEXT[a.action] ?? a.action}
                      {a.action === "resolve" &&
                        `: ${CASE_STATUS_LABELS[a.to_status as CaseStatus]}`}
                    </p>
                    <p className="text-muted-foreground">
                      {a.staff_name ?? "Hệ thống"} ·{" "}
                      {formatDateTime(a.created_at)}
                    </p>
                    {a.note && <p className="mt-1">{a.note}</p>}
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

function ActionPanel({ kase: c }: { kase: CaseDetail }) {
  const { data: me } = useMe()
  const claim = useClaimCase()
  const resolve = useResolveCase()
  const [note, setNote] = useState("")
  const error = claim.error ?? resolve.error

  return (
    <Card>
      <CardHeader>
        <CardTitle>Xử lý</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        {c.status === "OPEN" && (
          <Button
            onClick={() => claim.mutate(c.case_code)}
            disabled={claim.isPending}
          >
            Nhận xử lý case này
          </Button>
        )}

        {c.status === "IN_REVIEW" && c.assigned_to_name !== me?.full_name && (
          <p className="text-muted-foreground">
            Case đang do {c.assigned_to_name} xử lý.
          </p>
        )}

        {c.status === "IN_REVIEW" && c.assigned_to_name === me?.full_name && (
          <>
            <div className="grid gap-2">
              <Label htmlFor="note">Lý do kết luận (bắt buộc)</Label>
              <textarea
                id="note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={3}
                placeholder="Ví dụ: 6 tài khoản mới cùng thiết bị, cùng địa chỉ, cùng dùng voucher tân thủ"
                className="rounded-md border bg-transparent px-3 py-2 outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            {c.order && (
              <p className="text-muted-foreground">
                "Không vi phạm" sẽ duyệt đơn {c.order.order_code}; "Xác nhận lạm
                dụng" sẽ từ chối đơn và hoàn hàng về kho.
              </p>
            )}
            <div className="grid gap-2 sm:grid-cols-2">
              <Button
                variant="outline"
                disabled={resolve.isPending || note.trim().length < 10}
                onClick={() =>
                  resolve.mutate({
                    code: c.case_code,
                    outcome: "CLEARED",
                    note,
                  })
                }
              >
                <ShieldCheck /> Không vi phạm
              </Button>
              <Button
                variant="destructive"
                disabled={resolve.isPending || note.trim().length < 10}
                onClick={() =>
                  resolve.mutate({
                    code: c.case_code,
                    outcome: "CONFIRMED_ABUSE",
                    note,
                  })
                }
              >
                <ShieldX /> Xác nhận lạm dụng
              </Button>
            </div>
          </>
        )}

        {(c.status === "CONFIRMED_ABUSE" || c.status === "CLEARED") && (
          <div>
            <p className="font-medium">
              Đã kết luận: {CASE_STATUS_LABELS[c.status]}
              {c.order &&
                ` · Đơn: ${STATUS_LABELS[c.order.status as OrderStatus]}`}
            </p>
            <p className="mt-1 text-muted-foreground">{c.outcome_reason}</p>
          </div>
        )}

        {error && (
          <p className="text-destructive" role="alert">
            {error.message}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
