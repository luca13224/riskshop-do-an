import type { ComponentProps } from "react"

import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

// Một ô nhập có nhãn và dòng báo lỗi bên dưới. Dùng chung cho mọi form.
interface FormFieldProps extends ComponentProps<typeof Input> {
  id: string
  label: string
  error?: string
}

export function FormField({ id, label, error, ...inputProps }: FormFieldProps) {
  const errorId = `${id}-error`
  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        {...inputProps}
      />
      {error && (
        <p id={errorId} className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}
