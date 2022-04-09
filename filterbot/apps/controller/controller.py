import asyncio
from asyncio import Queue
from pathlib import Path
from typing import Optional

from loguru import logger
from pydantic import BaseModel
from telethon import TelegramClient, events

# client = TelegramClient(f'_session', api_id, api_hash)
from filterbot.apps.bot.temp import controller_codes_queue, controller_clients
from filterbot.db.models import User, Account, ChatStorage
from filterbot.loader import bot, storage

SESSION_PATH = Path(Path(__file__).parent, "sessions")


class Controller(BaseModel):
    user_id: int
    username: Optional[str]
    phone: str
    api_id: int
    api_hash: str
    client: Optional[TelegramClient]
    path: Optional[Path]
    chats: Optional[list[ChatStorage]]

    class Config:
        arbitrary_types_allowed = True

    def __str__(self):
        return f"{self.user_id}[{self.api_id}]"

    def _init(self):
        logger.info(f"Инициализация клиента {self}")
        self.path = Path(SESSION_PATH, f"{self.api_id}_{self.user_id}.session")
        self.client = TelegramClient(str(self.path), self.api_id, self.api_hash)
        controller_clients[self.user_id] = self.client

    async def start(self):
        self._init()
        await self.client.start()
        await self._start()

    async def _start(self):
        """Настройка ответов на сообщения"""
        logger.success(f"Контроллер {self} запущен")

        @self.client.on(events.NewMessage(incoming=True))
        async def message_handler(event: events.NewMessage.Event):
            pass

        await self.client.run_until_disconnected()


class ConnectAccountController(Controller):

    async def _get_code(self):
        queue: Queue = controller_codes_queue.get(self.user_id)
        code = await queue.get()
        queue.task_done()
        del queue
        return code

    async def get_code(self):
        try:
            return await asyncio.wait_for(self._get_code(), timeout=40)
        except asyncio.exceptions.TimeoutError as e:
            logger.warning(f"Не отправил код для подключения {self} {e}")
            await bot.send_message(self.user_id, "🚫 Код не получен отмена привязки ...")
            self.path.unlink()
            del controller_codes_queue[self.user_id]

    async def connect_account(self):
        """Подключение аккаунта и создание сессии"""
        logger.debug(f"Подключение аккаунта {self}")
        await self.client.start(lambda: self.phone, code_callback=lambda: self.get_code())
        logger.success(f"Аккаунт пользователя {self} успешно подключен")
        await storage.finish(user=self.user_id)
        await self.client.send_message("me", "✅ Бот успешно подключен")
        await bot.send_message(self.user_id, "✅ Бот успешно подключен")
        await User.connect_account(**self.dict())

    async def start(self):
        self._init()
        await self.connect_account()
        await self._start()


async def start_controller(acc: Account):
    controller = Controller(
        user_id=acc.user.user_id,
        username=acc.user.username,
        **dict(acc)
    )
    asyncio.create_task(controller.start())


async def init_controllers():
    logger.debug("Инициализация контролеров")
    for acc in await Account.all().select_related("user"):
        await start_controller(acc)
    logger.info("Контроллеры проинициализированы")


if __name__ == "__main__":
    pass
