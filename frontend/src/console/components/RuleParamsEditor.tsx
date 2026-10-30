import { Input } from "@/components/ui/input"
import type { Rule } from "@/lib/api/risk"

// Hiển thị / sửa tham số của luật thành câu dễ đọc, ví dụ "Từ 3 trở lên → +35 điểm".
// Chỉ cho sửa CON SỐ; cấu trúc (đặc trưng, phép so sánh, số bậc) giữ nguyên, backend cũng kiểm tra lại.

type Params = Record<string, unknown>
type Tier = { gte: number; points: number; strength?: string }
type Condition = { feature: string; op: string; value: number | boolean }

const FEATURE_LABELS: Record<string, string> = {
  new_accounts_on_device_30d: "Số tài khoản mới trên cùng thiết bị (30 ngày)",
  accounts_on_address_30d: "Số tài khoản dùng chung địa chỉ (30 ngày)",
  new_accounts_on_ip_24h: "Số tài khoản mới cùng IP (24 giờ)",
  voucher_attempts_device_10m: "Số lần thử mã từ cùng thiết bị (10 phút)",
  open_cod_orders: "Số đơn COD đang chờ giao",
  cod_fail_rate_smoothed: "Tỷ lệ giao COD thất bại (đã làm mượt)",
  cod_finished: "Số đơn COD đã kết thúc",
  account_age_hours: "Tuổi tài khoản (giờ)",
  voucher_new_user: "Dùng voucher tân thủ",
  signup_to_checkout_sec: "Thời gian từ đăng ký đến đặt hàng (giây)",
  product_views_24h: "Số lượt xem sản phẩm (24 giờ)",
  payment_cod: "Thanh toán COD",
  delivered_orders: "Số đơn đã giao thành công",
  fail_rate_raw: "Tỷ lệ giao thất bại",
  order_value: "Giá trị đơn (VND)",
}
const OP_LABELS: Record<string, string> = {
  lt: "<",
  lte: "≤",
  gt: ">",
  gte: "≥",
  eq: "=",
}

const label = (feature: unknown) =>
  FEATURE_LABELS[String(feature)] ?? String(feature)

interface EditorProps {
  rule: Rule
  params: Params
  editable: boolean
  onChange: (params: Params) => void
}

function NumberField({
  value,
  editable,
  onChange,
  ariaLabel,
}: {
  value: number
  editable: boolean
  onChange: (v: number) => void
  ariaLabel: string
}) {
  if (!editable)
    return (
      <span className="font-semibold tabular-nums">
        {value.toLocaleString("vi-VN")}
      </span>
    )
  return (
    <Input
      type="number"
      step="any"
      value={Number.isNaN(value) ? "" : value}
      aria-label={ariaLabel}
      onChange={(e) =>
        onChange(e.target.value === "" ? Number.NaN : Number(e.target.value))
      }
      className="inline-flex h-8 w-28 tabular-nums"
    />
  )
}

function TierRows({
  feature,
  tiers,
  editable,
  onChange,
}: {
  feature: string
  tiers: Tier[]
  editable: boolean
  onChange: (tiers: Tier[]) => void
}) {
  const update = (i: number, key: "gte" | "points", v: number) =>
    onChange(tiers.map((t, j) => (j === i ? { ...t, [key]: v } : t)))
  return (
    <ul className="grid gap-2">
      {tiers.map((t, i) => (
        <li key={i} className="flex flex-wrap items-center gap-2">
          <span className="text-muted-foreground">
            Khi {label(feature).toLowerCase()} ≥
          </span>
          <NumberField
            value={t.gte}
            editable={editable}
            onChange={(v) => update(i, "gte", v)}
            ariaLabel="Ngưỡng"
          />
          <span className="text-muted-foreground">thì cộng</span>
          <NumberField
            value={t.points}
            editable={editable}
            onChange={(v) => update(i, "points", v)}
            ariaLabel="Điểm"
          />
          <span className="text-muted-foreground">điểm</span>
          {t.strength && (
            <span className="rounded bg-muted px-1.5 text-xs">bậc mạnh</span>
          )}
        </li>
      ))}
    </ul>
  )
}

export function RuleParamsEditor({
  rule,
  params,
  editable,
  onChange,
}: EditorProps) {
  if (rule.rule_type === "count_threshold_tiers") {
    return (
      <TierRows
        feature={String(params.feature)}
        tiers={params.tiers as Tier[]}
        editable={editable}
        onChange={(tiers) => onChange({ ...params, tiers })}
      />
    )
  }

  if (rule.rule_type === "rate_threshold_tiers") {
    return (
      <div className="grid gap-2">
        <p className="flex flex-wrap items-center gap-2">
          <span className="text-muted-foreground">
            Chỉ xét khi {label(params.count_feature).toLowerCase()} ≥
          </span>
          <NumberField
            value={params.min_count as number}
            editable={editable}
            onChange={(v) => onChange({ ...params, min_count: v })}
            ariaLabel="Số mẫu tối thiểu"
          />
        </p>
        <TierRows
          feature={String(params.rate_feature)}
          tiers={params.tiers as Tier[]}
          editable={editable}
          onChange={(tiers) => onChange({ ...params, tiers })}
        />
      </div>
    )
  }

  // compound: nhiều điều kiện AND, cộng điểm cố định hoặc theo bậc
  const conditions = params.conditions as Condition[]
  const tiers = params.tiers as { feature: string; levels: Tier[] } | undefined
  const setCondition = (i: number, value: number | boolean) =>
    onChange({
      ...params,
      conditions: conditions.map((c, j) => (j === i ? { ...c, value } : c)),
    })

  return (
    <div className="grid gap-2">
      <p className="text-muted-foreground">
        Khi TẤT CẢ điều kiện sau cùng đúng:
      </p>
      <ul className="grid gap-2 pl-3">
        {conditions.map((c, i) => (
          <li key={i} className="flex flex-wrap items-center gap-2">
            <span>{label(c.feature)}</span>
            <span className="font-mono">{OP_LABELS[c.op] ?? c.op}</span>
            {typeof c.value === "boolean" ? (
              <span className="font-semibold">{c.value ? "có" : "không"}</span>
            ) : (
              <NumberField
                value={c.value}
                editable={editable}
                onChange={(v) => setCondition(i, v)}
                ariaLabel={`Giá trị điều kiện ${i + 1}`}
              />
            )}
          </li>
        ))}
      </ul>
      {tiers ? (
        <TierRows
          feature={tiers.feature}
          tiers={tiers.levels}
          editable={editable}
          onChange={(levels) =>
            onChange({ ...params, tiers: { ...tiers, levels } })
          }
        />
      ) : (
        <p className="flex flex-wrap items-center gap-2">
          <span className="text-muted-foreground">thì cộng</span>
          <NumberField
            value={params.points as number}
            editable={editable}
            onChange={(v) => onChange({ ...params, points: v })}
            ariaLabel="Điểm"
          />
          <span className="text-muted-foreground">điểm</span>
        </p>
      )}
    </div>
  )
}
