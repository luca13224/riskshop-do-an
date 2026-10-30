// Định dạng hiển thị dùng chung. Backend lưu tiền VND bằng số nguyên; chỉ định dạng khi hiển thị.

const vnd = new Intl.NumberFormat("vi-VN", {
  style: "currency",
  currency: "VND",
  maximumFractionDigits: 0,
})

export function formatVND(amount: number): string {
  return vnd.format(amount) // 590000 -> "590.000 ₫"
}

const dateTime = new Intl.DateTimeFormat("vi-VN", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "Asia/Ho_Chi_Minh",
})

// Backend lưu và trả thời gian theo UTC nhưng không kèm múi giờ ("2026-10-30T11:24:54").
// Thêm "Z" để trình duyệt hiểu đó là UTC, rồi hiển thị theo giờ Việt Nam.
export function formatDateTime(iso: string): string {
  const hasZone = /[zZ]|[+-]\d\d:?\d\d$/.test(iso)
  return dateTime.format(new Date(hasZone ? iso : `${iso}Z`))
}
