import { ChevronDown, FlaskConical, History, Pencil } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Skeleton } from "@/components/ui/skeleton"
import { BacktestPanel } from "@/console/components/BacktestPanel"
import { RuleParamsEditor } from "@/console/components/RuleParamsEditor"
import { useMe } from "@/lib/api/auth"
import {
  CONTEXT_LABELS,
  useCreateRuleVersion,
  useRules,
  useRuleVersions,
  type Rule,
} from "@/lib/api/risk"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const STRENGTH = {
  strong: {
    label: "Mạnh",
    tone: "bg-rose-500/15 text-rose-700 dark:text-rose-300",
  },
  medium: {
    label: "Vừa",
    tone: "bg-amber-500/15 text-amber-700 dark:text-amber-300",
  },
  weak: { label: "Yếu", tone: "bg-muted text-muted-foreground" },
  positive: {
    label: "Tích cực",
    tone: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
  },
}

export function RulesPage() {
  const { data: me } = useMe()
  const rules = useRules()
  const canEdit = me?.role === "risk_manager" || me?.role === "admin"

  return (
    <div className="grid gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Luật rủi ro</h1>
        <p className="text-sm text-muted-foreground">
          Mỗi lần sửa tạo một phiên bản mới; quyết định cũ vẫn trỏ đúng phiên
          bản đã dùng lúc đó.
          {canEdit
            ? " Chỉ được sửa con số, cấu trúc luật được giữ nguyên. Nên chạy thử trên dữ liệu cũ trước khi lưu."
            : " Vai trò của bạn được chạy thử tham số khác nhưng không được lưu."}
        </p>
      </div>
      {rules.isPending ? (
        <Skeleton className="h-64 w-full rounded-xl" />
      ) : rules.isError ? (
        <p className="text-destructive">{rules.error.message}</p>
      ) : (
        <div className="grid gap-3">
          {rules.data.map((r) => (
            <RuleCard key={r.code} rule={r} canEdit={canEdit} />
          ))}
        </div>
      )}
    </div>
  )
}

function RuleCard({ rule, canEdit }: { rule: Rule; canEdit: boolean }) {
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(rule.active.params)
  const [enabled, setEnabled] = useState(rule.active.enabled)
  const [note, setNote] = useState("")
  const save = useCreateRuleVersion()
  const versions = useRuleVersions(rule.code, open)
  const strength = STRENGTH[rule.strength]

  function startEdit() {
    setDraft(structuredClone(rule.active.params))
    setEnabled(rule.active.enabled)
    setNote("")
    save.reset()
    setEditing(true)
  }

  function submit() {
    save.mutate(
      { code: rule.code, params: draft, enabled, change_note: note },
      { onSuccess: () => setEditing(false) }
    )
  }

  return (
    <Card className={cn(!rule.active.enabled && "opacity-60")}>
      <CardHeader className="cursor-pointer" onClick={() => setOpen((v) => !v)}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium">{rule.name}</p>
            <p className="font-mono text-xs text-muted-foreground">
              {rule.code} · v{rule.active.version}
              {!rule.active.enabled && " · ĐANG TẮT"}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span
              className={cn(
                "rounded-md px-2 py-0.5 font-medium",
                strength.tone
              )}
            >
              {strength.label}
            </span>
            {rule.policies.map((p) => (
              <span key={p} className="rounded-md border px-2 py-0.5">
                {p === "cod" ? "COD" : "Voucher"}
              </span>
            ))}
            <span className="text-muted-foreground">
              {rule.hit_count_7d} lần khớp / 7 ngày
            </span>
            <ChevronDown
              className={cn(
                "size-4 transition-transform",
                open && "rotate-180"
              )}
              aria-hidden
            />
          </div>
        </div>
      </CardHeader>

      {open && (
        <CardContent className="grid gap-4 text-sm">
          <p className="text-xs text-muted-foreground">
            Áp dụng ở:{" "}
            {rule.active.contexts.map((c) => CONTEXT_LABELS[c]).join(", ") || "chỉ điểm tin cậy tài khoản"} ·
            Câu giải thích: "{rule.active.reason_template}"
          </p>

          <RuleParamsEditor
            rule={rule}
            params={editing ? draft : rule.active.params}
            editable={editing}
            onChange={setDraft}
          />

          {!editing && (
            <Button variant="outline" size="sm" className="w-fit" onClick={startEdit}>
              {canEdit ? <Pencil /> : <FlaskConical />}
              {canEdit ? "Sửa (tạo phiên bản mới)" : "Thử tham số khác"}
            </Button>
          )}

          {editing && <BacktestPanel rule={rule} params={draft} enabled={enabled} />}

          {editing && !canEdit && (
            <Button size="sm" variant="ghost" className="w-fit" onClick={() => setEditing(false)}>
              Đóng
            </Button>
          )}

          {editing && canEdit && (
            <div className="grid gap-3 rounded-lg border p-3">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={enabled}
                  onChange={(e) => setEnabled(e.target.checked)}
                />
                Luật đang bật
              </label>
              <div className="grid gap-2">
                <Label htmlFor={`note-${rule.code}`}>
                  Lý do thay đổi (bắt buộc)
                </Label>
                <textarea
                  id={`note-${rule.code}`}
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={2}
                  placeholder="Ví dụ: farm mới dùng ít tài khoản hơn, hạ ngưỡng xuống 2"
                  className="rounded-md border bg-transparent px-3 py-2 outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
              </div>
              {save.isError && (
                <p className="text-destructive" role="alert">
                  {save.error.message}
                </p>
              )}
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={submit}
                  disabled={save.isPending || note.trim().length < 10}
                >
                  Lưu thành v{rule.active.version + 1}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setEditing(false)}
                >
                  Hủy
                </Button>
              </div>
            </div>
          )}

          <div className="grid gap-2">
            <p className="flex items-center gap-1 font-medium">
              <History className="size-4" /> Lịch sử phiên bản
            </p>
            <ol className="grid gap-2 border-l pl-4">
              {versions.data?.map((v) => (
                <li key={v.version}>
                  <span className="font-mono font-medium">v{v.version}</span>
                  {!v.enabled && (
                    <span className="text-muted-foreground"> (tắt)</span>
                  )}
                  <span className="text-muted-foreground">
                    {" "}
                    · {v.created_by_name ?? "Hệ thống"} ·{" "}
                    {formatDateTime(v.created_at)}
                  </span>
                  <p>{v.change_note}</p>
                </li>
              ))}
            </ol>
          </div>
        </CardContent>
      )}
    </Card>
  )
}
