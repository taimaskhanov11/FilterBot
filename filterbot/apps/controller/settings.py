import logging
import sys
from pathlib import Path

from loguru import logger as log

from telethoncontrollerbot.config.config import BASE_DIR

LOG_DIR = Path(Path(BASE_DIR, "logs"))
LOG_DIR.mkdir(exist_ok=True)


def init_logging(filename="", old_logger=True, level="TRACE", old_level=logging.INFO, steaming=True, write=False):
    log.remove()
    if steaming:
        log.add(sink=sys.stderr, level=level, enqueue=True, diagnose=True)
    if write:
        log.add(
            sink=Path(LOG_DIR, f"main{filename}.log"),
            level=level,
            enqueue=True,
            encoding="utf-8",
            diagnose=True,
            rotation="5MB",
            compression="zip",
        )
    if old_logger:
        handlers = []
        if steaming:
            handlers.append(logging.StreamHandler())
        if write:
            handlers.append(logging.FileHandler(filename=Path(LOG_DIR, f"aiogram{filename}.log"), encoding="utf-8"))

        logging.basicConfig(
            encoding="utf-8",
            level=old_level,
            format="{levelname} [{asctime}] {name}: {message}",
            style="{",
            handlers=handlers,
        )
