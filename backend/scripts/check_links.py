"""Kiểm tra link hỏng trong tài liệu của repo (chạy sau mỗi lần đổi tên / chuyển chỗ file).

    .venv/Scripts/python scripts/check_links.py

Quét mọi file .md đang được git theo dõi:
- link Markdown [chữ](đường/dẫn) trỏ tới file trong repo (bỏ qua http, mailto, #neo);
- đường dẫn trong dấu `...` bắt đầu bằng docs/, backend/, frontend/ hoặc .claude/.
Đường dẫn tương đối tính từ thư mục chứa file .md, rồi thử thêm từ gốc repo. Có chỗ hỏng thì trả mã lỗi 1.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD_LINK = re.compile(r"\]\(([^)\s]+)\)")
CODE_PATH = re.compile(r"`((?:docs|backend|frontend|\.claude)/[^`*<>\s]+)`")
SKIP = ("http://", "https://", "mailto:", "#")
# File được nhắc tới nhưng chỉ tạo khi cần (không tính là link hỏng)
PLANNED = {"docs/KIEM_TRA_BAO_MAT.md", "docs/tu_van/LUYEN_BAO_VE.md"}


def exists(md: Path, target: str) -> bool:
    target = target.split("#", 1)[0].rstrip("/")
    if not target or target in PLANNED:
        return True
    return (md.parent / target).exists() or (ROOT / target).exists()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    files = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True,
                           encoding="utf8", check=True).stdout.split()
    broken = []
    for rel in files:
        md = ROOT / rel
        for n, line in enumerate(md.read_text(encoding="utf8").splitlines(), 1):
            targets = [t for t in MD_LINK.findall(line) if not t.startswith(SKIP)] + CODE_PATH.findall(line)
            broken += [(rel, n, t) for t in targets if not exists(md, t)]
    for rel, n, t in broken:
        print(f"{rel}:{n}: {t}")
    print(f"{len(files)} file .md, {len(broken)} link hỏng")
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
