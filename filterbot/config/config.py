import argparse
import typing
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger
from pydantic import BaseModel
from telethon import TelegramClient

BASE_DIR = Path(__file__).parent.parent.parent


def load_yaml(file) -> dict:
    file = file if Path(file).suffix else f"{file}.yml"
    with open(Path(BASE_DIR, file), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_config():
    parser = argparse.ArgumentParser(description="config_file")
    parser.add_argument("-f", type=str)
    args = parser.parse_args()
    if args.f:
        logger.success(f"Выгрузка конфига из файла {args.f}")
    return args.f


class Bot(BaseModel):
    token: str
    # id: int
    admins: Optional[list[int]]
    block_list: Optional[list[int]]
    # vip: Optional[list[int]]
    # chat: Optional[int]


class ControllerConfig(BaseModel):
    api_id: int
    api_hash: str
    controller: Optional[TelegramClient]

    class Config:
        arbitrary_types_allowed = True


class Settings(BaseModel):
    check_type: typing.Literal["like", "comment", "like_comment"]
    queue_length: int
    dd_messages: int


class Database(BaseModel):
    username: str
    password: str
    host: str
    port: int
    db_name: str


class Config(BaseModel):
    bot: Bot
    db: Database
    # controller: Controller
    # settings: Settings


I18N_DOMAIN = "filterbot"
LOCALES_DIR = BASE_DIR / "filterbot/apps/bot/locales"

config_file = parse_config()
config = Config(**load_yaml(config_file or "config.yml"))
