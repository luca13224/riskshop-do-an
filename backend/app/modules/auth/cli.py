"""Tạo tài khoản nhân viên (analyst, risk_manager, admin) từ dòng lệnh.

API đăng ký chỉ tạo được khách hàng; tài khoản nhân viên chỉ tạo được bằng lệnh này.

    python -m app.modules.auth.cli --email analyst@riskshop.test --name "Analyst Demo" --role analyst

Mật khẩu: nhập khi được hỏi (không hiện trên màn hình), hoặc đặt sẵn biến môi trường RS_NEW_PASSWORD.
"""

import argparse
import getpass
import os
import sys

from app.core.db import SessionLocal
from app.modules.auth import service
from app.modules.auth.models import ALL_ROLES
from app.modules.auth.schemas import LoginIn


def main() -> int:
    # Cửa sổ dòng lệnh Windows mặc định không phải UTF-8 nên in tiếng Việt bị lỗi
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Tạo tài khoản RiskShop")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", required=True, choices=ALL_ROLES)
    args = parser.parse_args()

    password = os.environ.get("RS_NEW_PASSWORD") or getpass.getpass("Mật khẩu (tối thiểu 8 ký tự): ")
    if len(password) < 8:
        print("Mật khẩu quá ngắn.", file=sys.stderr)
        return 1
    email = LoginIn(email=args.email, password=password).email  # dùng lại bước chuẩn hóa email

    with SessionLocal() as db:
        user = service.create_user(db, email=email, password=password, full_name=args.name, role=args.role)
        print(f"Đã tạo user id={user.id} email={user.email} role={user.role}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
