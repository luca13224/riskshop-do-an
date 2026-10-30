"""Module risk: Risk Engine (đặc trưng -> luật -> điểm theo chính sách -> ma trận quyết định).

Xem docs/RULES_V0.md. Module này KHÔNG import code của cart/order (ADR-003, ADR-004):
bên gọi truyền vào một EvaluationRequest; đặc trưng được đọc từ CSDL ở chế độ chỉ đọc (features.py).
"""
