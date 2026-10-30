import { MessageSquareWarning } from "lucide-react"
import { useState, type FormEvent } from "react"
import { Link, Navigate } from "react-router"

import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  useCreateAppeal,
  useEligible,
  useMyAppeals,
  type Eligible,
} from "@/lib/api/appeals"
import { useMe } from "@/lib/api/auth"
import { formatDateTime } from "@/lib/format"
import { AppealStatusBadge } from "@/components/appeal-status-badge"

// Khiếu nại (ADR-006): khách bị hạn chế nhầm có thể gửi khiếu nại cho từng lần bị hạn chế.
// Trang chỉ nói KẾT QUẢ ("Mã giảm giá không được áp dụng"), không nói luật nào đã khớp.
export function AppealsPage() {
  const { data: user, isPending } = useMe()
  const eligible = useEligible()
  const mine = useMyAppeals()

  if (isPending) return null
  if (!user) return <Navigate to="/login?next=/appeals" replace />

  return (
    <div className="mx-auto grid max-w-3xl gap-10 py-10">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Khiếu nại</h1>
        <p className="mt-2 text-muted-foreground">
          Hệ thống tự kiểm tra rủi ro để bảo vệ ưu đãi và đơn hàng. Nếu bạn nghĩ
          mình bị hạn chế nhầm, hãy cho chúng tôi biết. Nhân viên sẽ xem xét và
          trả lời bạn tại đây.
        </p>
      </div>

      <section aria-labelledby="co-the">
        <h2 id="co-the" className="text-xl font-semibold">
          Những lần bạn bị hạn chế (30 ngày gần nhất)
        </h2>
        <div className="mt-4 grid gap-3">
          {eligible.isPending ? (
            <Skeleton className="h-24 rounded-3xl" />
          ) : eligible.isError ? (
            <p className="text-destructive">{eligible.error.message}</p>
          ) : eligible.data.length === 0 ? (
            <p className="rounded-3xl bg-secondary p-6 text-sm text-muted-foreground">
              Không có lần nào cần khiếu nại. Mọi thứ đều ổn!
            </p>
          ) : (
            eligible.data.map((e) => (
              <EligibleItem key={`${e.decision_id}-${e.policy}`} item={e} />
            ))
          )}
        </div>
      </section>

      <section aria-labelledby="da-gui">
        <h2 id="da-gui" className="text-xl font-semibold">
          Khiếu nại đã gửi
        </h2>
        <div className="mt-4 grid gap-3">
          {mine.isPending ? (
            <Skeleton className="h-24 rounded-3xl" />
          ) : mine.isError ? (
            <p className="text-destructive">{mine.error.message}</p>
          ) : mine.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              Bạn chưa gửi khiếu nại nào.
            </p>
          ) : (
            mine.data.map((a) => (
              <article key={a.appeal_code} className="rounded-3xl border p-5">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="font-medium">{a.label}</p>
                  <AppealStatusBadge status={a.status} />
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  Mã {a.appeal_code} · gửi lúc {formatDateTime(a.created_at)}
                  {a.order_code && (
                    <>
                      {" · "}
                      <Link
                        to={`/orders/${a.order_code}`}
                        className="underline-offset-4 hover:underline"
                      >
                        Đơn {a.order_code}
                      </Link>
                    </>
                  )}
                </p>
                <p className="mt-3 text-sm whitespace-pre-line">{a.message}</p>
                {a.response && (
                  <div className="mt-3 rounded-2xl bg-secondary p-4 text-sm">
                    <p className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
                      Phản hồi của RiskShop
                    </p>
                    <p className="mt-1 whitespace-pre-line">{a.response}</p>
                  </div>
                )}
              </article>
            ))
          )}
        </div>
      </section>
    </div>
  )
}

function EligibleItem({ item }: { item: Eligible }) {
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState("")
  const create = useCreateAppeal()
  const tooShort = message.trim().length < 20

  function submit(e: FormEvent) {
    e.preventDefault()
    create.mutate({
      decision_id: item.decision_id,
      policy: item.policy,
      message,
    })
  }

  return (
    <article className="rounded-3xl bg-secondary p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="flex size-10 shrink-0 items-center justify-center rounded-full bg-background">
            <MessageSquareWarning className="size-5" />
          </span>
          <div>
            <p className="font-medium">{item.label}</p>
            <p className="text-xs text-muted-foreground">
              {formatDateTime(item.created_at)}
              {item.order_code && ` · Đơn ${item.order_code}`}
            </p>
          </div>
        </div>
        {item.open_appeal ? (
          <span className="text-sm text-muted-foreground">
            Đang có khiếu nại {item.open_appeal} chờ xử lý
          </span>
        ) : (
          !open && (
            <Button
              variant="buy"
              className="rounded-full"
              onClick={() => setOpen(true)}
            >
              Gửi khiếu nại
            </Button>
          )
        )}
      </div>

      {open && !item.open_appeal && (
        <form onSubmit={submit} className="mt-4 grid gap-3">
          <label
            htmlFor={`msg-${item.decision_id}-${item.policy}`}
            className="text-sm font-medium"
          >
            Vì sao bạn nghĩ đây là nhầm lẫn?
          </label>
          <textarea
            id={`msg-${item.decision_id}-${item.policy}`}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={4}
            maxLength={1000}
            placeholder="Ví dụ: Cả nhà dùng chung một máy tính, tôi là khách mới thật và chưa từng dùng mã này."
            className="rounded-2xl border bg-background px-4 py-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <p className="text-xs text-muted-foreground">
            Tối thiểu 20 ký tự ({message.trim().length}/1000). Không ghi mật
            khẩu hay số thẻ.
          </p>
          {create.isError && (
            <p className="text-sm text-destructive" role="alert">
              {create.error.message}
            </p>
          )}
          <div className="flex gap-2">
            <Button
              type="submit"
              variant="buy"
              className="rounded-full"
              disabled={tooShort || create.isPending}
            >
              {create.isPending ? "Đang gửi…" : "Gửi khiếu nại"}
            </Button>
            <Button
              type="button"
              variant="ghost"
              className="rounded-full"
              onClick={() => setOpen(false)}
            >
              Hủy
            </Button>
          </div>
        </form>
      )}
    </article>
  )
}
