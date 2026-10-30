import { CircleCheck, CircleX, FlaskConical, Loader2, Play } from "lucide-react"
import { Link } from "react-router"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useMe } from "@/lib/api/auth"
import { ApiError } from "@/lib/api/client"
import {
  useLabRuns,
  useLabScenarios,
  useStartLabRun,
  type LabRun,
} from "@/lib/api/lab"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const STATUS_TEXT: Record<LabRun["status"], string> = {
  queued: "Đang chờ worker",
  running: "Đang chạy",
  done: "Hoàn tất",
  failed: "Lỗi",
}

export function AttackLabPage() {
  const { data: me } = useMe()
  const scenarios = useLabScenarios()
  const runs = useLabRuns()
  const start = useStartLabRun()
  const busy =
    runs.data?.some((r) => r.status === "queued" || r.status === "running") ??
    false

  if (me && me.role !== "admin") {
    return (
      <p className="text-muted-foreground">Attack Lab chỉ dành cho Admin.</p>
    )
  }
  if (scenarios.error instanceof ApiError && scenarios.error.status === 404) {
    return (
      <p className="text-muted-foreground">
        Attack Lab đang tắt (chỉ bật ở môi trường demo, DEMO_MODE=true).
      </p>
    )
  }

  const titles = Object.fromEntries(
    (scenarios.data ?? []).map((s) => [s.code, s.title])
  )

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
            <FlaskConical className="size-6" /> Attack Lab
          </h1>
          <p className="text-sm text-muted-foreground">
            Chạy kịch bản tấn công và kịch bản người dùng hợp lệ qua API thật.
            Mở Live Monitor ở tab khác để xem Risk Engine phản ứng.
          </p>
        </div>
        <Button variant="outline" size="sm" asChild>
          <Link to="/console/monitor">Mở Live Monitor</Link>
        </Button>
      </div>

      <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm">
        Chế độ demo: tính năng này tạo tài khoản giả hàng loạt nên chỉ tồn tại
        khi bật cấu hình demo, và chỉ Admin dùng được. Mọi lần chạy đều được ghi
        audit log.
      </p>

      {scenarios.isPending ? (
        <Skeleton className="h-40 w-full rounded-xl" />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {scenarios.data?.map((s) => (
            <Card key={s.code}>
              <CardHeader>
                <p className="text-xs font-medium text-muted-foreground">
                  {s.scene}
                </p>
                <CardTitle>{s.title}</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm">
                <p>{s.description}</p>
                <p className="text-muted-foreground">
                  <span className="font-medium text-foreground">Kỳ vọng: </span>
                  {s.expected}
                </p>
                <Button
                  onClick={() => start.mutate(s.code)}
                  disabled={busy || start.isPending}
                  className="w-fit"
                >
                  <Play /> Chạy kịch bản
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      {start.isError && (
        <p className="text-sm text-destructive">{start.error.message}</p>
      )}

      <div className="grid gap-4">
        <h2 className="text-lg font-semibold">Các lần chạy gần đây</h2>
        {runs.data?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Chưa chạy kịch bản nào.
          </p>
        )}
        {runs.data?.map((run) => (
          <RunCard
            key={run.id}
            run={run}
            title={titles[run.scenario] ?? run.scenario}
          />
        ))}
      </div>
    </div>
  )
}

function RunCard({ run, title }: { run: LabRun; title: string }) {
  const active = run.status === "queued" || run.status === "running"
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="text-base">
            {title}{" "}
            <span className="font-mono text-xs text-muted-foreground">
              #{run.run_tag}
            </span>
          </CardTitle>
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium",
              active && "bg-sky-500/15 text-sky-700 dark:text-sky-300",
              run.status === "done" &&
                run.passed &&
                "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
              (run.status === "failed" ||
                (run.status === "done" && !run.passed)) &&
                "bg-rose-500/15 text-rose-700 dark:text-rose-300"
            )}
          >
            {active && <Loader2 className="size-3.5 animate-spin" />}
            {STATUS_TEXT[run.status]}
            {run.status === "done" &&
              (run.passed ? " · đúng kỳ vọng" : " · có bước lệch kỳ vọng")}
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          {formatDateTime(run.created_at)}
        </p>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm">
        {run.steps.map((s, i) => (
          <div key={i} className="flex animate-in items-start gap-2 fade-in">
            {s.ok === true && (
              <CircleCheck className="mt-0.5 size-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
            )}
            {s.ok === false && (
              <CircleX className="mt-0.5 size-4 shrink-0 text-rose-600 dark:text-rose-400" />
            )}
            {s.ok === null && <span className="mt-0.5 size-4 shrink-0" />}
            <span className="flex-1">
              <span className="font-mono text-xs text-muted-foreground">
                {s.actor}
              </span>{" "}
              {s.action}: <span className="font-medium">{s.result}</span>
              {s.ok === false && s.expected && (
                <span className="text-muted-foreground">
                  {" "}
                  (kỳ vọng: {s.expected})
                </span>
              )}
            </span>
          </div>
        ))}
        {run.summary && (
          <p className="mt-2 rounded-md bg-muted/50 p-2">{run.summary}</p>
        )}
      </CardContent>
    </Card>
  )
}
