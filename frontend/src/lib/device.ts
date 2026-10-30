// Mã thiết bị: một ID ngẫu nhiên lưu trong trình duyệt, gửi kèm mọi request (header X-Device-Id).
// Backend dùng nó để đếm "bao nhiêu tài khoản trên cùng một thiết bị" (luật R02).
// Đây không phải fingerprint thật: xóa dữ liệu trình duyệt hoặc mở tab ẩn danh là có ID mới.

const KEY = "rs_device_id"
let memoryFallback: string | null = null

export function getDeviceId(): string {
  try {
    let id = localStorage.getItem(KEY)
    if (!id) {
      id = crypto.randomUUID()
      localStorage.setItem(KEY, id)
    }
    return id
  } catch {
    // localStorage có thể bị chặn (chế độ riêng tư, chính sách trình duyệt): dùng ID tạm trong bộ nhớ
    memoryFallback ??= crypto.randomUUID()
    return memoryFallback
  }
}
