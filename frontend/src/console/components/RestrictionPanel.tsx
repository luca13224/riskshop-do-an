import { Ban, ShieldCheck } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CONTACT_ROLES, useMe } from "@/lib/api/auth"
import { RESTRICTION_LABELS, useBanUser, useLiftRestriction, useRestriction } from "@/lib/api/risk"
import { formatDateTime } from "@/lib/format"

// Quyền mua hàng của khách trong case (ADR-010, ADR-011).
// Hệ thống tự khóa khi cố đặt lặp hoặc né lệnh khóa; Risk Manager / Admin khóa vô thời hạn hoặc gỡ khóa,
// lần nào cũng bắt buộc ghi lý do (vào audit log).
export function RestrictionPanel({ userId }: { userId: number }) {
  const { data: me } = useMe()
  const restriction = useRestriction(userId)
  const lift = useLiftRestriction(userId)
  const ban = useBanUser(userId)
  const [reason, setReason] = useState("")
  const canManage = !!me && CONTACT_ROLES.includes(me.role)
  const r = restriction.data
  const busy = lift.isPending || ban.isPending
  const error = lift.error ?? ban.error

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
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3">
            <p className="font-medium">{RESTRICTION_LABELS[r.kind]}</p>
            <p className="mt-1 text-muted-foreground">
              Từ {formatDateTime(r.since)} · {r.until ? `đến ${formatDateTime(r.until)}` : "vô thời hạn"}
            </p>
            <p className="mt-1">{r.reason}</p>
          </div>
        )}
        {canManage ? (
          <form className="grid gap-2" onSubmit={(e) => e.preventDefault()}>
            <Label htmlFor="restriction-reason">Lý do (ghi vào audit log)</Label>
            <Input
              id="restriction-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={r ? "Ví dụ: đã gọi điện xác minh, khách bấm lặp do mạng chậm" : "Ví dụ: cùng người với cụm farm đã kết luận"}
              minLength={10}
              maxLength={255}
            />
            <div className="flex flex-wrap gap-2">
              {r && (
                <Button
                  type="button"
                  variant="outline"
                  disabled={busy || reason.trim().length < 10}
                  onClick={() => lift.mutate(reason, { onSuccess: () => setReason("") })}
                >
                  Gỡ khóa
                </Button>
              )}
              {r?.kind !== "purchase_ban" && (
                <Button
                  type="button"
                  variant="destructive"
                  disabled={busy || reason.trim().length < 10}
                  onClick={() => ban.mutate(reason, { onSuccess: () => setReason("") })}
                >
                  Khóa vô thời hạn
                </Button>
              )}
            </div>
            {error && (
              <p className="text-destructive" role="alert">
                {error.message}
              </p>
            )}
          </form>
        ) : (
          r && <p className="text-muted-foreground">Chỉ Risk Manager hoặc Admin được khóa hoặc gỡ khóa.</p>
        )}
      </CardContent>
    </Card>
  )
}
