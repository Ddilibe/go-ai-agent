#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

os.makedirs("logs", exist_ok=True)


def setup_logger() -> logging.Logger:

    class CustomFormatter(logging.Formatter):
        def format(self, record):
            record.name = record.name.ljust(20)
            return super().format(record)

    logger = logging.getLogger("go_agent")
    logger.setLevel(logging.DEBUG)

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    console_formatter = CustomFormatter(
        fmt=log_format,
        datefmt=date_format,
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        filename=f"logs/gosifu_{datetime.now(timezone.utc).day:02d}_{datetime.now().month:02d}_{datetime.now().year}.log",
        maxBytes=10_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    file_formatter = CustomFormatter(
        fmt=log_format,
        datefmt=date_format,
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)

    return logger
