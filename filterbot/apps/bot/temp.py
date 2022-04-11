from asyncio import Queue
from typing import Literal

users_locales: dict[int, Literal["ru", "en"]] = {}
controller_codes_queue: dict[int, Queue] = {}
# controller_clients: dict[int, TelegramClient] = {}
controllers: dict[int] = {}
