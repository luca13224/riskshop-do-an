import { Eye, Lock } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CONTACT_ROLES, useMe, useRevealContact } from "@/lib/api/auth"

// Thông tin liên hệ của khách trong case. Mặc định chỉ thấy email đã che;
// Risk Manager/Admin ghi lý do để xem đầy đủ, mỗi lần xem được ghi vào audit log.
export function ContactPanel({
  userId,
  maskedEmail,
}: {
  userId: number
  maskedEmail: string
}) {
  const { data: me } = useMe()
  const reveal = useRevealContact()
  const [reason, setReason] = useState("")
  const canReveal = !!me && CONTACT_ROLES.includes(me.role)
  const contact = reveal.data

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lock className="size-4" /> Liên hệ khách hàng
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 text-sm">
        {contact ? (
          <>
            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
              <dt className="text-muted-foreground">Họ tên</dt>
              <dd>{contact.full_name}</dd>
              <dt className="text-muted-foreground">Email</dt>
              <dd className="break-all">{contact.email}</dd>
              <dt className="text-muted-foreground">SĐT</dt>
              <dd>{contact.phone ?? "Chưa có"}</dd>
            </dl>
            <p className="text-muted-foreground">
              Lần xem này đã được ghi vào audit log. Tải lại trang thì thông tin
              sẽ bị che lại.
            </p>
          </>
        ) : (
          <>
            <p>
              Email: <span className="font-mono">{maskedEmail}</span>
            </p>
            {canReveal ? (
              <form
                className="grid gap-2"
                onSubmit={(e) => {
                  e.preventDefault()
                  reveal.mutate({ userId, reason })
                }}
              >
                <Label htmlFor="reveal-reason">
                  Lý do xem thông tin đầy đủ (bắt buộc)
                </Label>
                <Input
                  id="reveal-reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Ví dụ: Gọi xác minh đơn COD giá trị cao"
                />
                <Button
                  type="submit"
                  variant="outline"
                  disabled={reveal.isPending || reason.trim().length < 10}
                >
                  <Eye /> Xem email và SĐT
                </Button>
              </form>
            ) : (
              <p className="text-muted-foreground">
                Chỉ Risk Manager hoặc Admin được xem thông tin liên hệ đầy đủ.
              </p>
            )}
            {reveal.error && (
              <p className="text-destructive" role="alert">
                {reveal.error.message}
              </p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
