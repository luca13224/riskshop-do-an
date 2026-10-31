import { Ban, ShieldCheck } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CONTACT_ROLES, useMe } from "@/lib/api/auth"
import { RESTRICTION_LABELS, useLiftRestriction, useRestriction } from "@/lib/api/risk"
import { formatDateTime } from "@/lib/format"

// Trạng thái khóa quyền mua hàng của khách trong case (ADR-010).
// Khóa do hệ thống tự đặt; chỉ Risk Manager / Admin gỡ được, bắt buộc ghi lý do (vào audit log).
export function RestrictionPanel({ userId }: { userId: number }) {
  const { data: me } = useMe()
  const restriction = useRestriction(userId)
  const lift = useLiftRestriction(userId)
  const [reason, setReason] = useState("")
  const canLift = !!me && CONTACT_ROLES.includes(me.role)
  const r = restriction.data

  if (restriction.isPending) return null
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {r ? <Ban className="size-4 text-destructive" /> : <ShieldCheck className="size-4" />}
          Quyền mua hàng
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        {!r ? (
          <p className="text-muted-foreground">Không bị khóa. Khách đặt hàng bình thường.</p>
        ) : (
          <>
            <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3">
              <p className="font-medium">{RESTRICTION_LABELS[r.kind]}</p>
              <p className="mt-1 text-muted-foreground">
                Từ {formatDateTime(r.since)} · {r.until ? `đến ${formatDateTime(r.until)}` : "vô thời hạn"}
              </p>
              <p className="mt-1">{r.reason}</p>
            </div>
            {canLift ? (
              <form
                className="grid gap-2"
                onSubmit={(e) => {
                  e.preventDefault()
                  lift.mutate(reason, { onSuccess: () => setReason("") })
                }}
              >
                <Label htmlFor="lift-reason">Lý do gỡ khóa (ghi vào audit log)</Label>
                <Input
                  id="lift-reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Ví dụ: đã gọi điện xác minh, khách bấm lặp do mạng chậm"
                  minLength={10}
                  maxLength={255}
                  required
                />
                <Button type="submit" variant="outline" disabled={lift.isPending || reason.trim().length < 10}>
                  Gỡ khóa
                </Button>
                {lift.isError && (
                  <p className="text-destructive" role="alert">
                    {lift.error.message}
                  </p>
                )}
              </form>
            ) : (
              <p className="text-muted-foreground">Chỉ Risk Manager hoặc Admin được gỡ khóa.</p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
