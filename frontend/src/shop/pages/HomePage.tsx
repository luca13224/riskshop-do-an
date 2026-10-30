import { Link } from "react-router"

import { Button } from "@/components/ui/button"
import { useMe } from "@/lib/api/auth"

// Trang chủ tạm. Danh sách sản phẩm sẽ thêm ở module catalog.
export function HomePage() {
  const { data: user } = useMe()

  return (
    <section className="py-16">
      <p className="text-sm font-medium text-muted-foreground">Chào mừng tới RiskShop</p>
      <h1 className="mt-2 max-w-xl text-3xl font-semibold tracking-tight sm:text-4xl">
        {user ? `Xin chào, ${user.full_name}!` : "Mua sắm an tâm, ưu đãi thật cho người dùng thật."}
      </h1>
      <p className="mt-4 max-w-xl text-muted-foreground">
        Danh sách sản phẩm sẽ có ở bước tiếp theo. Hiện bạn có thể thử đăng ký, đăng nhập và vào Risk Console bằng
        tài khoản nhân viên.
      </p>
      {!user && (
        <div className="mt-6 flex gap-3">
          <Button asChild>
            <Link to="/register">Tạo tài khoản</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to="/login">Đăng nhập</Link>
          </Button>
        </div>
      )}
    </section>
  )
}
