import { CASE_STATUS_LABELS, type CaseStatus } from "@/lib/api/cases"
import { cn } from "@/lib/utils"

const TONES: Record<CaseStatus, string> = {
  OPEN: "bg-sky-500/15 text-sky-700 dark:text-sky-300",
  IN_REVIEW: "bg-violet-500/15 text-violet-700 dark:text-violet-300",
  CONFIRMED_ABUSE: "bg-rose-500/15 text-rose-700 dark:text-rose-300",
  CLEARED: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300",
}

export function CaseStatusBadge({ status }: { status: CaseStatus }) {
  return (
    <span
      className={cn(
        "inline-flex rounded-md px-2 py-0.5 text-xs font-medium",
        TONES[status]
      )}
    >
      {CASE_STATUS_LABELS[status]}
    </span>
  )
}
