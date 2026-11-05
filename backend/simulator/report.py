"""Xuất kết quả mô phỏng thành báo cáo Markdown (dùng cho chương thực nghiệm)."""

from app.core.time import utcnow

PERSONA_LABELS = {
    "normal_new": "Khách mới bình thường",
    "loyal": "Khách quen",
    "family": "Gia đình chung Wi-Fi/địa chỉ",
    "new_high_value": "Khách mới mua hàng giá trị cao (COD)",
    "repeat_buyer": "Khách quen đặt nhiều đơn liên tiếp",
    "farm": "Farm voucher",
    "cod_bomber": "Bùng hàng COD",
    "farm_spread": "Farm phân tán (mỗi tài khoản một máy, đổi IP)",
    "cod_hoarder": "Tài khoản mới treo nhiều đơn COD",
    "roommates_4g": "Nhóm ở trọ chung nhà, mỗi người 4G riêng",
    "farm_multi_drop": "Farm phân tán gom hàng về 2–3 điểm nhận",
    "ban_evader": "Né lệnh khóa: tài khoản mới chung ≥ 2 điểm với tài khoản bị khóa",
    "ban_evader_spam": "Né lệnh khóa: nhiều tài khoản mới cùng máy, gom mã người mới",
    "ban_evader_one_link": "Né lệnh khóa: chỉ giữ SĐT nhận hàng cũ",
    "banned_relative": "Người nhà dùng chung máy với tài khoản bị khóa",
    "new_multi_cod": "Khách mới đặt nhiều đơn COD liền nhau",
}

LOCK_LABELS = {"purchase_linked": "khóa do liên kết", "purchase_cooldown": "khóa 24 giờ", "purchase_ban": "khóa vô thời hạn"}


def _r(rate: dict) -> str:
    if rate["value"] is None:
        return "—"
    ci = rate["ci95"]
    return f"{rate['value']:.1%} ({rate['k']}/{rate['n']}; KTC 95%: {ci[0]:.1%}–{ci[1]:.1%})"


def _v(x) -> str:
    return "—" if x is None else f"{x:.1%}"


BASELINE_LABELS = [
    ("engine", "Risk Engine (lần chạy này)"),
    ("no_control", "B0 · Không kiểm soát"),
    ("manual_rules", "B1 · Luật thủ công (2 luật cứng)"),
    ("random_same_rate", "B2 · Ngẫu nhiên, cùng tỷ lệ gắn cờ (kỳ vọng)"),
]


def _baselines(m: dict) -> list[str]:
    b = m.get("baselines")
    if not b:
        return []
    lines = ["", "## So với baseline (cùng tài khoản, cùng nhãn)",
             f"Tỷ lệ kẻ lạm dụng trong dân số: {_v(b['abuse_rate'])}; Risk Engine gắn cờ {_v(b['engine_flag_rate'])} tài khoản. "
             "B1 được chấm bằng cách phát lại trên ảnh chụp đặc trưng của từng lần chấm điểm (xem `simulator/baselines.py`).",
             "", "| Cách làm | Precision | Recall | F1 | FPR | Accuracy | TP / FP / FN |", "|---|---|---|---|---|---|---|"]
    for key, label in BASELINE_LABELS:
        r = b[key]
        c = r["confusion"]
        lines.append(f"| {label} | {_v(r['precision'])} | {_v(r['recall'])} | {_v(r['f1'])} | {_v(r['fpr'])} | "
                     f"{_v(r['accuracy'])} | {c['TP']:g} / {c['FP']:g} / {c['FN']:g} |")
    by = {k: v for k, v in b.get("manual_by_persona", {}).items() if v}
    if by:
        lines += ["", "B1 gắn cờ theo persona: " + ", ".join(
            f"{PERSONA_LABELS.get(k, k)} {v}/{m['per_persona'][k]['n']}" for k, v in by.items() if k in m["per_persona"]) + "."]
    return lines


def render_markdown(m: dict) -> str:
    c = m["confusion"]
    lines = [
        f"# Kết quả mô phỏng: tập {m['dataset']} (seed {m['seed']}, scale {m['scale']:g})",
        "",
        f"> Tạo lúc {utcnow():%Y-%m-%d %H:%M} UTC · Lần chạy #{m['run_id']} · "
        f"Dấu vân tay bộ luật: `{m['rules_fingerprint'][:16]}…`"
        + (" · **B0 không kiểm soát**: tắt mọi luật, lớp điểm tin cậy và khóa kẻ né lệnh khóa" if m.get("no_control")
           else f" · Luật bị tắt: {', '.join(m['disabled_rules'])}" if m.get("disabled_rules") else "")
        + (" · Tắt lớp điểm tin cậy" if m.get("no_trust") and not m.get("no_control") else ""),
        "> **Toàn bộ dữ liệu là mô phỏng.** Kết quả phản ánh giả định của bộ mô phỏng (`backend/simulator/personas.py`),"
        " không chứng minh hiệu quả trên sàn thật.",
        "",
        "## Chỉ số chính (đơn vị: tài khoản)",
        "Một tài khoản bị coi là **bị gắn cờ** nếu có ít nhất một quyết định khác ALLOW (gỡ voucher, tắt COD, giữ đơn, chặn).",
        "",
        "| | Bị gắn cờ | Không bị gắn cờ |",
        "|---|---|---|",
        f"| **Lạm dụng (nhãn thật)** | TP = {c['TP']} | FN = {c['FN']} |",
        f"| **Hợp lệ (nhãn thật)** | FP = {c['FP']} | TN = {c['TN']} |",
        "",
        "| Chỉ số | Giá trị |",
        "|---|---|",
        f"| Precision | {_r(m['precision'])} |",
        f"| Recall (tất cả kiểu lạm dụng) | {_r(m['recall'])} |",
        f"| Recall: kiểu đã biết | {_r(m['recall_seen_variants'])} |",
        f"| Recall: biến thể chưa biết | {_r(m['recall_unseen_variants'])} |",
        f"| FPR (tất cả khách hợp lệ) | {_r(m['fpr'])} |",
        f"| FPR: khách hợp lệ thông thường | {_r(m['fpr_normal'])} |",
        f"| FPR: hard negative | {_r(m['fpr_hard_negative'])} |",
        f"| F1 | {_v(m.get('f1'))} |",
        f"| Accuracy | {_v(m.get('accuracy'))} |",
        "",
        "## Theo persona",
        "| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ | Bị khóa tài khoản | Voucher đã dùng |",
        "|---|---|---|---|---|---|---|",
    ]
    for key, p in m["per_persona"].items():
        kind = ("Lạm dụng (chưa biết)" if p["unseen"] else "Lạm dụng") if p["is_abuse"] else (
            "Hard negative" if p["hard_negative"] else "Hợp lệ")
        locked = ", ".join(f"{c} {LOCK_LABELS.get(k, k)}" for k, c in sorted(p.get("locked", {}).items())) or "—"
        lines.append(f"| {PERSONA_LABELS.get(key, key)} | {kind} | {p['n']} | {p['flagged']} | {p['rate']:.0%} | {locked} | {p.get('vouchers', 0)} |")

    lines += ["", "## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)",
              "| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |", "|---|---|"]
    for key, g in m["group_recall"].items():
        lines.append(f"| {PERSONA_LABELS.get(key, key)} | {g['caught']}/{g['groups']} |")

    lines += _baselines(m)

    b = m["business"]
    lines += [
        "", "## Tác động nghiệp vụ trong lần chạy",
        f"- Mã người mới bị kẻ lạm dụng dùng thành công: **{b['vouchers_redeemed_by_abuse']}** lượt; "
        f"khách hợp lệ dùng: {b['vouchers_redeemed_by_legit']} lượt.",
        "- Đơn COD theo persona và trạng thái: "
        + ", ".join(f"{PERSONA_LABELS.get(k.split(':')[0], k.split(':')[0])} {k.split(':')[1]} = {v}"
                    for k, v in sorted(b["cod_orders_by_persona"].items())),
        "",
        "## Độ trễ",
        f"- Thời gian chấm điểm rủi ro (đo ở server, {m['risk_latency_ms']['n']} lượt): "
        f"p50 {m['risk_latency_ms']['p50']} ms · p95 {m['risk_latency_ms']['p95']} ms · p99 {m['risk_latency_ms']['p99']} ms",
    ]
    for kind, r in m["request_ms"].items():
        lines.append(f"- Toàn bộ request `{kind}` ({r['n']} lượt, trong cùng tiến trình, không qua mạng): "
                     f"p50 {r['p50']} ms · p95 {r['p95']} ms · p99 {r['p99']} ms")
    lines += [
        f"- Thời gian chạy: {m['runtime']['seconds']} giây cho {m['runtime']['steps']} bước; lỗi server: "
        f"{len(m['runtime']['server_errors'])}",
        "",
        "## Giới hạn",
        "- Thời gian bị nén: lịch sử quá khứ được tạo sẵn, còn mọi hành vi hiện tại diễn ra trong vài phút chạy.",
        "- Chạy tuần tự trong một tiến trình: đây KHÔNG phải đo tải; độ trễ dưới tải đồng thời cần đo riêng.",
        "- Hành vi, tỷ lệ và tham số persona là giả định; kết quả không khái quát cho dữ liệu thật.",
        "- Chỉ số tính theo tài khoản: một tài khoản bị gắn cờ một lần là tính, bất kể mức hạn chế.",
    ]
    return "\n".join(lines) + "\n"
