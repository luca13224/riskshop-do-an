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
}


def _r(rate: dict) -> str:
    if rate["value"] is None:
        return "—"
    ci = rate["ci95"]
    return f"{rate['value']:.1%} ({rate['k']}/{rate['n']}; KTC 95%: {ci[0]:.1%}–{ci[1]:.1%})"


def render_markdown(m: dict) -> str:
    c = m["confusion"]
    lines = [
        f"# Kết quả mô phỏng: tập {m['dataset']} (seed {m['seed']}, scale {m['scale']:g})",
        "",
        f"> Tạo lúc {utcnow():%Y-%m-%d %H:%M} UTC · Lần chạy #{m['run_id']} · "
        f"Dấu vân tay bộ luật: `{m['rules_fingerprint'][:16]}…`",
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
        "",
        "## Theo persona",
        "| Persona | Loại | Số tài khoản | Bị gắn cờ | Tỷ lệ |",
        "|---|---|---|---|---|",
    ]
    for key, p in m["per_persona"].items():
        kind = ("Lạm dụng (chưa biết)" if p["unseen"] else "Lạm dụng") if p["is_abuse"] else (
            "Hard negative" if p["hard_negative"] else "Hợp lệ")
        lines.append(f"| {PERSONA_LABELS.get(key, key)} | {kind} | {p['n']} | {p['flagged']} | {p['rate']:.0%} |")

    lines += ["", "## Phát hiện theo nhóm (một farm bị phát hiện nếu ít nhất một tài khoản bị gắn cờ)",
              "| Kiểu lạm dụng | Nhóm bị phát hiện / tổng |", "|---|---|"]
    for key, g in m["group_recall"].items():
        lines.append(f"| {PERSONA_LABELS.get(key, key)} | {g['caught']}/{g['groups']} |")

    b = m["business"]
    lines += [
        "", "## Tác động nghiệp vụ trong lần chạy",
        f"- Voucher tân thủ bị kẻ lạm dụng dùng thành công: **{b['vouchers_redeemed_by_abuse']}** lượt; "
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
