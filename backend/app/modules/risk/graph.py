"""Đồ thị liên kết tài khoản (link analysis) cho Risk Console.

Ý tưởng: từng tín hiệu riêng lẻ (cùng thiết bị, cùng IP, cùng địa chỉ giao hàng) có thể yếu, nhưng
nhìn cả MẠNG LƯỚI thì thấy được một cụm tài khoản cùng hội tụ về vài điểm chung. Ví dụ farm "phân tán"
đổi thiết bị và IP cho từng tài khoản nhưng vẫn giao về một địa chỉ (docs/TEST_PLAN.md mục 3).

Đồ thị hai loại nút: TÀI KHOẢN và ĐIỂM CHUNG (thiết bị, IP, địa chỉ). Cạnh = tài khoản đã dùng điểm chung đó.
Từ một tài khoản gốc, đi tối đa 2 bước "tài khoản -> điểm chung -> tài khoản khác".

Giống feature store (ADR-004): chỉ ĐỌC bảng của module khác bằng SQL. Dữ liệu cá nhân luôn che:
email che, IP chỉ hiện bản che, địa chỉ chỉ hiện phường/quận (không số nhà).
"""

from datetime import timedelta

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.privacy import mask_email
from app.core.time import utcnow

WINDOW_DAYS = 30  # chỉ xét liên kết còn hoạt động trong 30 ngày
MAX_ACCOUNTS = 40  # chặn đồ thị phình to khi gặp "điểm chung" rất đông (ví dụ IP văn phòng)
DEPTH = 2
SEVERITY = {"ALLOW": 0, "ALLOW_WITH_RESTRICTION": 1, "REVIEW": 2, "BLOCK": 3}


def _rows(db: Session, sql: str, **params):
    stmt = text(sql)
    for k, v in params.items():
        if isinstance(v, (list, set, tuple)):
            stmt = stmt.bindparams(bindparam(k, expanding=True))
    return db.execute(stmt, {k: list(v) if isinstance(v, (set, tuple)) else v for k, v in params.items()}).all()


def link_graph(db: Session, root_user_id: int) -> dict | None:
    since = utcnow() - timedelta(days=WINDOW_DAYS)
    if not _rows(db, "SELECT 1 FROM users WHERE id = :u AND role = 'customer'", u=root_user_id):
        return None

    users: set[int] = {root_user_id}
    frontier = {root_user_id}
    edges: set[tuple[str, str]] = set()
    entities: dict[str, dict] = {}
    truncated = False

    for _ in range(DEPTH):
        if not frontier:
            break
        # 1) Điểm chung của các tài khoản ở biên hiện tại
        found: list[tuple[int, str, dict]] = []
        for uid, did in _rows(db, "SELECT user_id, device_id FROM user_devices WHERE user_id IN :us AND last_seen_at >= :s",
                              us=frontier, s=since):
            found.append((uid, f"d:{did}", {"type": "device", "label": f"Thiết bị #{did}"}))
        for uid, h, masked in _rows(db, "SELECT user_id, ip_hash, ip_masked FROM user_ips WHERE user_id IN :us AND last_seen_at >= :s",
                                    us=frontier, s=since):
            found.append((uid, f"ip:{h[:12]}", {"type": "ip", "label": masked, "_hash": h}))
        for uid, h, ward, district in _rows(
            db, "SELECT user_id, norm_hash, MAX(ward), MAX(district) FROM addresses WHERE user_id IN :us "
                "AND created_at >= :s GROUP BY user_id, norm_hash", us=frontier, s=since):
            found.append((uid, f"a:{h[:12]}", {"type": "address", "label": f"{ward}, {district}", "_hash": h}))
        new_entities = []
        for uid, eid, info in found:
            edges.add((f"u:{uid}", eid))
            if eid not in entities:
                entities[eid] = info
                new_entities.append(eid)

        # 2) Tài khoản khác cũng dùng các điểm chung đó
        dev_ids = [int(e[2:]) for e in new_entities if e.startswith("d:")]
        ip_hashes = [entities[e]["_hash"] for e in new_entities if e.startswith("ip:")]
        addr_hashes = [entities[e]["_hash"] for e in new_entities if e.startswith("a:")]
        neighbours: list[tuple[int, str]] = []
        if dev_ids:
            neighbours += [(u, f"d:{d}") for u, d in _rows(
                db, "SELECT user_id, device_id FROM user_devices WHERE device_id IN :ds AND last_seen_at >= :s",
                ds=dev_ids, s=since)]
        if ip_hashes:
            neighbours += [(u, f"ip:{h[:12]}") for u, h in _rows(
                db, "SELECT user_id, ip_hash FROM user_ips WHERE ip_hash IN :hs AND last_seen_at >= :s",
                hs=ip_hashes, s=since)]
        if addr_hashes:
            neighbours += [(u, f"a:{h[:12]}") for u, h in _rows(
                db, "SELECT DISTINCT user_id, norm_hash FROM addresses WHERE norm_hash IN :hs AND created_at >= :s",
                hs=addr_hashes, s=since)]
        frontier = set()
        for uid, eid in neighbours:
            if uid not in users:
                if len(users) >= MAX_ACCOUNTS:
                    truncated = True
                    continue
                users.add(uid)
                frontier.add(uid)
            edges.add((f"u:{uid}", eid))

    # Chỉ giữ điểm chung nối từ 2 tài khoản trở lên, hoặc thuộc tài khoản gốc (bỏ "lá" gây rối mắt)
    degree: dict[str, int] = {}
    for _, eid in edges:
        degree[eid] = degree.get(eid, 0) + 1
    keep = {eid for eid in entities if degree.get(eid, 0) >= 2 or (f"u:{root_user_id}", eid) in edges}
    edges = {(u, e) for u, e in edges if e in keep and int(u[2:]) in users}

    # Thông tin từng tài khoản: tuổi tài khoản, quyết định rủi ro nặng nhất trong 30 ngày, đã bị kết luận lạm dụng chưa
    now = utcnow()
    info = {uid: {"email": email, "created_at": created} for uid, email, created in _rows(
        db, "SELECT id, email, created_at FROM users WHERE id IN :us", us=users)}
    worst: dict[int, tuple[str, int]] = {}
    for uid, decision, score in _rows(
        db, "SELECT user_id, decision, MAX(score) FROM risk_decisions WHERE user_id IN :us AND created_at >= :s "
            "GROUP BY user_id, decision", us=users, s=since):
        cur = worst.get(uid)
        if cur is None or SEVERITY[decision] > SEVERITY[cur[0]] or (decision == cur[0] and score > cur[1]):
            worst[uid] = (decision, int(score))
    confirmed = {uid for (uid,) in _rows(
        db, "SELECT DISTINCT d.user_id FROM case_decisions cd JOIN risk_cases c ON c.id = cd.case_id "
            "JOIN risk_decisions d ON d.id = cd.decision_id WHERE c.status = 'CONFIRMED_ABUSE' AND d.user_id IN :us",
        us=users)}

    nodes = []
    for uid in sorted(users):
        age_days = (now - info[uid]["created_at"]).total_seconds() / 86400
        decision, score = worst.get(uid, ("ALLOW", 0))
        nodes.append({
            "id": f"u:{uid}", "type": "account", "label": mask_email(info[uid]["email"]), "user_id": uid,
            "root": uid == root_user_id, "age_days": round(age_days, 1), "is_new": age_days < 7,
            "worst_decision": decision if uid in worst else None, "max_score": score,
            "confirmed_abuse": uid in confirmed,
        })
    for eid in sorted(keep):
        e = entities[eid]
        nodes.append({"id": eid, "type": e["type"], "label": e["label"], "accounts": degree[eid]})

    accounts = [n for n in nodes if n["type"] == "account"]
    return {
        "root": f"u:{root_user_id}",
        "nodes": nodes,
        "edges": [{"source": u, "target": e} for u, e in sorted(edges)],
        "truncated": truncated,
        "summary": {
            "accounts": len(accounts),
            "new_accounts": sum(n["is_new"] for n in accounts),
            "restricted_accounts": sum(1 for n in accounts if n["worst_decision"] not in (None, "ALLOW")),
            "confirmed_abuse": sum(n["confirmed_abuse"] for n in accounts),
            "shared_points": sum(1 for eid in keep if degree[eid] >= 2),
            "window_days": WINDOW_DAYS,
        },
    }
