import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { ApiError } from "@/lib/api/client"
import { useHealth } from "@/lib/api/health"

// Trang tổng quan tạm của Console: hiện trạng thái hệ thống. Live Monitor sẽ thay thế sau.
export function ConsoleHomePage() {
  const health = useHealth()

  let status: { label: string; tone: string }
  if (health.isPending) {
    status = { label: "Đang kiểm tra…", tone: "text-muted-foreground" }
  } else if (health.isError) {
    const err = health.error
    status = {
      label:
        err instanceof ApiError
          ? `${err.code}: ${err.message}`
          : "Lỗi không xác định",
      tone: "text-destructive",
    }
  } else {
    status = {
      label: "Backend và cơ sở dữ liệu hoạt động bình thường",
      tone: "text-emerald-600 dark:text-emerald-400",
    }
  }

  return (
    <div className="grid max-w-3xl gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Tổng quan</h1>
        <p className="text-sm text-muted-foreground">
          Các màn hình Live Monitor, Case, Luật… sẽ lần lượt được thêm vào.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Trạng thái hệ thống</CardTitle>
          <CardDescription>
            Kiểm tra API và kết nối cơ sở dữ liệu.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className={`text-sm font-medium ${status.tone}`} role="status">
            {status.label}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
