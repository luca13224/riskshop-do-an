import { Minus, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"

// Nút chọn số lượng [-] 2 [+], dùng ở trang chi tiết và trang giỏ hàng
interface QuantityStepperProps {
  value: number
  max: number
  onChange: (value: number) => void
  disabled?: boolean
  label?: string
}

export function QuantityStepper({
  value,
  max,
  onChange,
  disabled,
  label = "Số lượng",
}: QuantityStepperProps) {
  return (
    <div
      className="inline-flex items-center rounded-lg border"
      role="group"
      aria-label={label}
    >
      <Button
        type="button"
        variant="ghost"
        size="icon"
        aria-label="Giảm"
        disabled={disabled || value <= 1}
        onClick={() => onChange(value - 1)}
      >
        <Minus />
      </Button>
      <span
        className="w-10 text-center text-sm tabular-nums"
        aria-live="polite"
      >
        {value}
      </span>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        aria-label="Tăng"
        disabled={disabled || value >= max}
        onClick={() => onChange(value + 1)}
      >
        <Plus />
      </Button>
    </div>
  )
}
