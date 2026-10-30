"""Worker xử lý việc nền (bảng jobs).

Chạy (trong thư mục backend, đã có .venv):
    .venv/Scripts/python -m worker.main

Dừng: Ctrl+C. Có thể chạy nhiều worker cùng lúc (SKIP LOCKED đảm bảo không lấy trùng việc).
"""

import logging
import sys
import time

import app.models  # noqa: F401  (nạp đủ model)
from app.core import jobs
from app.core.db import SessionLocal
from app.modules.cases import service as cases
from app.modules.lab import service as lab
from app.modules.risk.service import OPEN_CASE_JOB

POLL_SECONDS = 1.0


def register_handlers() -> None:
    jobs.HANDLERS[OPEN_CASE_JOB] = cases.open_from_decision
    jobs.HANDLERS[lab.LAB_RUN_JOB] = lab.execute


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")  # log của logging đi qua stderr
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s worker %(message)s")
    register_handlers()
    logging.info("Worker bắt đầu, kiểm tra hàng đợi mỗi %.0f giây", POLL_SECONDS)
    while True:
        with SessionLocal() as db:
            processed = jobs.run_all(db, limit=100)
        if processed:
            logging.info("Đã xử lý %d việc", processed)
        else:
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Worker dừng")
