import { Button } from "@/components/ui/button"
import { ApiError } from "@/lib/api/client"
import { useHealth } from "@/lib/api/health"

// Trang tạm để kiểm tra khung dự án: frontend gọi được backend, backend nối được CSDL.
// Sẽ được thay bằng router với hai khu vực Shop (/) và Risk Console (/console).
export function App() {
  const health = useHealth()

  let status: { label: string; tone: string }
  if (health.isPending) {
    status = { label: "Đang kiểm tra kết nối…", tone: "text-muted-foreground" }
  } else if (health.isError) {
    const err = health.error
    const detail = err instanceof ApiError ? `${err.code}: ${err.message}` : "Lỗi không xác định"
    status = { label: `Chưa kết nối được backend (${detail})`, tone: "text-destructive" }
  } else {
    status = { label: "Backend và cơ sở dữ liệu đã sẵn sàng", tone: "text-emerald-600 dark:text-emerald-400" }
  }

  return (
    <main className="flex min-h-svh items-center justify-center p-6">
      <div className="flex w-full max-w-md flex-col gap-4 rounded-xl border p-6">
        <div>
          <h1 className="text-xl font-semibold">RiskShop</h1>
          <p className="text-sm text-muted-foreground">Khung dự án đồ án tốt nghiệp</p>
        </div>
        <p className={`text-sm font-medium ${status.tone}`} role="status">
          {status.label}
        </p>
        <Button variant="outline" onClick={() => health.refetch()} disabled={health.isFetching}>
          Kiểm tra lại
        </Button>
        <p className="font-mono text-xs text-muted-foreground">Nhấn phím d để đổi giao diện sáng / tối</p>
      </div>
    </main>
  )
}

export default App
