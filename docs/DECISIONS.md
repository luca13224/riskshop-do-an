# DECISIONS (Architecture Decision Records)

Mỗi quyết định quan trọng ghi theo mẫu bên dưới. Không xóa quyết định cũ; nếu thay đổi thì tạo ADR mới và đánh dấu ADR cũ là "Superseded".

## Mẫu
```
## ADR-XXX: <Tiêu đề>
- Ngày:
- Trạng thái: Proposed | Accepted | Superseded by ADR-YYY
- Bối cảnh: vấn đề cần quyết định
- Các phương án: A, B, C (ưu/nhược)
- Quyết định: chọn gì
- Lý do:
- Hệ quả / rủi ro:
```

---

## ADR-001: Lưu tài liệu dự án dạng Markdown trong thư mục docs/
- Ngày: 2026-10-30
- Trạng thái: Accepted
- Bối cảnh: Cần một hệ thống tài liệu dài hạn, theo dõi được thay đổi.
- Các phương án: (A) Markdown trong repo; (B) Word/Google Docs rời rạc.
- Quyết định: A.
- Lý do: Dễ quản lý phiên bản bằng Git, đặt cạnh mã nguồn, dễ chuyển thành báo cáo sau.
- Hệ quả: Báo cáo đồ án chính thức (Word/PDF) sẽ được soạn riêng, dựa trên nội dung các file này.
