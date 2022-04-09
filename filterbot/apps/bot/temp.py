from asyncio import Queue
from typing import Literal

from telethon import TelegramClient

users_locales: dict[int, Literal["ru", "en"]] = {}
controller_codes_queue: dict[int, Queue] = {}
controller_clients: dict[int, TelegramClient] = {}
