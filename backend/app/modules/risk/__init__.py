"""Module risk: Risk Engine (đặc trưng -> luật -> điểm theo chính sách -> ma trận quyết định).

Xem docs/BO_LUAT_RUI_RO.md. Module này KHÔNG import code của cart/order (ADR-003, ADR-004):
bên gọi truyền vào một EvaluationRequest; đặc trưng được đọc từ CSDL ở chế độ chỉ đọc (features.py).
"""
