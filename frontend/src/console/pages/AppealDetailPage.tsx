import { ArrowLeft, ShieldCheck, ShieldX } from "lucide-react"
import { useState } from "react"
import { Link, useParams } from "react-router"

import { AppealStatusBadge } from "@/components/appeal-status-badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { ContactPanel } from "@/console/components/ContactPanel"
import { DecisionBadge, ScoreBar } from "@/console/components/DecisionBadge"
import { DecisionDetail } from "@/console/components/DecisionDetail"
import {
  POLICY_LABELS,
  useResolveAppeal,
  useStaffAppeal,
  type StaffAppealDetail,
} from "@/lib/api/appeals"
import { useMe } from "@/lib/api/auth"
import { CONTEXT_LABELS } from "@/lib/api/risk"
import { formatDateTime } from "@/lib/format"

const REVIEWER_ROLES = ["risk_manager", "admin"]

export function AppealDetailPage() {
  const { code = "" } = useParams()
  const appeal = useStaffAppeal(code)

  if (appeal.isPending) return <Skeleton className="h-96 w-full rounded-xl" />
  if (appeal.isError) {
    return (
      <div className="grid gap-4">
        <BackLink />
        <p className="text-destructive">{appeal.error.message}</p>
      </div>
    )
  }
  const a = appeal.data
  const d = a.decision

  return (
    <div className="grid gap-6">
      <BackLink />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-mono text-2xl font-semibold tracking-tight">
            {a.appeal_code}
          </h1>
          <p className="text-sm text-muted-foreground">
            {POLICY_LABELS[a.policy]} · gửi lúc {formatDateTime(a.created_at)}
            {a.order_code && ` · Đơn ${a.order_code}`}
          </p>
        </div>
        <AppealStatusBadge status={a.status} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_22rem]">
        <div className="grid content-start gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Khách viết</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2 text-sm">
              <p className="text-muted-foreground">
                {a.user_name} · {a.user_email} · bị hạn chế:{" "}
                <b className="text-foreground">{a.label}</b>
              </p>
              <blockquote className="rounded-lg border-l-4 bg-muted/40 p-4 whitespace-pre-line">
                {a.message}
              </blockquote>
              {a.other_appeals > 0 && (
                <p className="text-amber-700 dark:text-amber-300">
                  Khách này đã gửi {a.other_appeals} khiếu nại khác. Cân nhắc
                  khả năng lạm dụng kênh khiếu nại.
                </p>
              )}
            </CardContent>
          </Card>

          {d && (
            <Card>
              <CardHeader>
                <CardTitle className="flex flex-wrap items-center gap-3">
                  Quyết định bị khiếu nại
                  <DecisionBadge decision={d.decision} />
                </CardTitle>
                <p className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                  {CONTEXT_LABELS[d.context]} · {formatDateTime(d.created_at)}
                  <ScoreBar score={d.score} />
                </p>
              </CardHeader>
              <CardContent>
                <DecisionDetail decision={d} />
              </CardContent>
            </Card>
          )}
        </div>

        <div className="grid content-start gap-6">
          <ResolvePanel appeal={a} />
          <ContactPanel
            key={a.appeal_code}
            userId={a.user_id}
            maskedEmail={a.user_email}
          />
          {a.active_exemptions.length > 0 && (
            <p className="rounded-xl border p-4 text-sm">
              Khách đang được miễn trừ:{" "}
              <b>
                {a.active_exemptions.map((p) => POLICY_LABELS[p]).join(", ")}
              </b>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

function BackLink() {
  return (
    <Link
      to="/console/appeals"
      className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
    >
      <ArrowLeft className="size-4" /> Danh sách khiếu nại
    </Link>
  )
}

function ResolvePanel({ appeal: a }: { appeal: StaffAppealDetail }) {
  const { data: me } = useMe()
  const resolve = useResolveAppeal()
  const [response, setResponse] = useState("")
  const canResolve = !!me && REVIEWER_ROLES.includes(me.role)
  const tooShort = response.trim().length < 10

  return (
    <Card>
      <CardHeader>
        <CardTitle>Kết luận</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        {a.status !== "OPEN" ? (
          <div>
            <p className="font-medium">
              {a.status === "ACCEPTED" ? "Đã chấp nhận" : "Đã từ chối"}
              {a.handled_by_name && ` · ${a.handled_by_name}`}
              {a.resolved_at && ` · ${formatDateTime(a.resolved_at)}`}
            </p>
            <p className="mt-2 text-muted-foreground">Đã trả lời khách:</p>
            <p className="mt-1 whitespace-pre-line">{a.response}</p>
          </div>
        ) : !canResolve ? (
          <p className="text-muted-foreground">
            Chỉ Risk Manager hoặc Admin được kết luận khiếu nại (người xét lại
            khác người xử lý ban đầu).
          </p>
        ) : (
          <>
            <div className="grid gap-2">
              <Label htmlFor="appeal-response">
                Trả lời khách (bắt buộc, khách sẽ đọc được)
              </Label>
              <textarea
                id="appeal-response"
                value={response}
                onChange={(e) => setResponse(e.target.value)}
                rows={4}
                maxLength={1000}
                placeholder="Ví dụ: Chúng tôi đã xác minh qua điện thoại, đơn của bạn đã được duyệt."
                className="rounded-md border bg-transparent px-3 py-2 outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            <p className="text-muted-foreground">
              "Chấp nhận" sẽ miễn trừ chính sách{" "}
              {POLICY_LABELS[a.policy].toLowerCase()} cho khách trong 30 ngày
              {a.order_code ? " và duyệt đơn nếu đơn đang bị giữ" : ""}.
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              <Button
                variant="outline"
                disabled={tooShort || resolve.isPending}
                onClick={() =>
                  resolve.mutate({
                    code: a.appeal_code,
                    outcome: "REJECTED",
                    response,
                  })
                }
              >
                <ShieldX /> Từ chối
              </Button>
              <Button
                disabled={tooShort || resolve.isPending}
                onClick={() =>
                  resolve.mutate({
                    code: a.appeal_code,
                    outcome: "ACCEPTED",
                    response,
                  })
                }
              >
                <ShieldCheck /> Chấp nhận
              </Button>
            </div>
            {resolve.isError && (
              <p className="text-destructive" role="alert">
                {resolve.error.message}
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
