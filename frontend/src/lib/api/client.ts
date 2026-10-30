import { getDeviceId } from "@/lib/device"

// Hàm gọi API dùng chung cho cả Shop và Console.
// Backend luôn trả lỗi theo dạng { error: { code, message, request_id } },
// nên ở đây ta biến nó thành một ApiError có đủ thông tin để hiển thị và debug.

export interface ApiErrorBody {
  code: string
  message: string
  request_id: string
  fields?: { field: string; message: string }[]
}

export class ApiError extends Error {
  status: number
  code: string
  requestId?: string
  fields?: ApiErrorBody["fields"]

  constructor(status: number, body: Partial<ApiErrorBody>) {
    super(body.message ?? "Có lỗi xảy ra, vui lòng thử lại.")
    this.status = status
    this.code = body.code ?? "UNKNOWN_ERROR"
    this.requestId = body.request_id
    this.fields = body.fields
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, {
      ...init,
      // Gửi kèm cookie phiên đăng nhập (cùng domain nhờ proxy của Vite)
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-Device-Id": getDeviceId(),
        ...init?.headers,
      },
    })
  } catch {
    // Không tới được server: backend chưa chạy hoặc mất mạng
    throw new ApiError(0, { code: "NETWORK_ERROR", message: "Không kết nối được máy chủ." })
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    if (!body.error) {
      // Lỗi không theo định dạng của backend, thường do proxy hoặc backend chưa chạy
      throw new ApiError(response.status, {
        code: "SERVER_UNAVAILABLE",
        message: "Máy chủ chưa sẵn sàng.",
      })
    }
    throw new ApiError(response.status, body.error)
  }
  if (response.status === 204) {
    return undefined as T // "204 No Content": thành công nhưng không có dữ liệu trả về
  }
  return (await response.json()) as T
}
