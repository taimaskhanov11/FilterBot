import asyncio
from asyncio import Queue
from pathlib import Path
from typing import Optional

from aiogram.utils import markdown
from loguru import logger
from pydantic import BaseModel
from telethon import TelegramClient, events
from telethon.tl import patched, types

from filterbot.apps.bot import temp, markups
from filterbot.apps.bot.markups import common_menu
from filterbot.apps.bot.temp import controller_codes_queue, controllers
from filterbot.apps.bot.utils.statistic import statistic_storage
from filterbot.db.models import User, Account, Chat, DummyFilter
from filterbot.loader import bot, storage, _

SESSION_PATH = Path(Path(__file__).parent, "sessions")


class MethodController(BaseModel):
    user_id: int
    username: Optional[str]
    client: Optional[TelegramClient]
    chats: Optional[dict[int, Chat]]

    class Config:
        arbitrary_types_allowed = True

    async def get_users_ids(self, text: str) -> dict[str, int]:

        ids: dict[str, int] = {}
        user_info = map(lambda x: x.strip(), text.split(","))

        for user_field in user_info:
            user_field: str
            if user_field[0].isdigit():
                user_field: int = int(user_field)
            try:
                user: types.User = await self.client.get_entity(user_field)
                ids[user.username] = user.id
            except Exception as e:
                logger.warning(e)

        return ids

    async def get_admins_ids(self, chat_id: int) -> dict[str, int]:
        ids: dict[str, int] = {}
        async for user in self.client.iter_participants(chat_id, filter=types.ChannelParticipantsAdmins()):
            ids[user.username] = user.id
        return ids

    async def message_prepare(self, chat_title, message: patched.Message):
        user: types.User = await self.client.get_entity(message.from_id.user_id)
        message.text = (f"#@{user.username}\n"
                        f"{message.text}\n"
                        f"/{markdown.hlink(chat_title, f'https://t.me/c/{message.peer_id.channel_id}/{message.id}')}")
        return message

    async def listening(self):
        """Прослушка входящих сообщений"""
        logger.success(f"Прослушивание сообщений {self} запущено")

        # @self.client.on(events.NewMessage(incoming=True))
        @self.client.on(events.NewMessage())
        async def message_handler(event: events.NewMessage.Event):
            # async def message_handler(message: patched.Message):
            message: patched.Message = event.message

            statistic_storage.incr(f"{self.user_id}_all_message")
            statistic_storage.incr("all_message")

            logger.debug(f"{self}|Новое сообщение {message.text}|{message.chat_id=}|{message.from_id=}.")
            chat = self.chats.get(message.chat_id, DummyFilter())
            if await chat.message_check(message):
                logger.success(f"{self}|{message} прошел проверку")

                statistic_storage.incr(f"{self.user_id}_filter_message")
                statistic_storage.incr("filter_message")

                try:
                    await self.message_prepare(chat.title, message)
                    await self.client.send_message(chat.chat_storage.chat_id, message.text, parse_mode='html')
                    # await self.client.forward_messages(
                    #     chat.chat_storage.chat_id,
                    #     message,
                    #     # with_my_score=True,
                    #     # background=True,
                    # )
                except Exception as e:
                    logger.warning(e)
                    await self.client.send_message(chat.chat_storage.chat_id, message)

        await self.client.run_until_disconnected()


class Controller(MethodController):
    phone: str
    api_id: int
    api_hash: str
    path: Optional[Path]

    def __str__(self):
        return f"{self.username}[{self.user_id}][app{self.api_id}]"

    def _init(self):
        logger.debug(f"Инициализация клиента {self}")
        self.path = Path(SESSION_PATH, f"{self.api_id}_{self.user_id}.session")
        self.client = TelegramClient(str(self.path), self.api_id, self.api_hash)
        controllers[self.user_id] = self

    async def run(self):
        """Возобновить client"""
        logger.debug(f"Возобновление Client {self}")
        await self.client.connect()
        asyncio.create_task(self.listening())

    async def pause(self):
        """Приостановит client"""
        await self.client.disconnect()
        logger.debug(f"Client {self} приостановлен")

    async def start(self):
        """Создать новый client и запустить"""
        self._init()
        logger.debug(f"Контроллер создан")
        await self.client.connect()
        await self.listening()

    async def stop(self):
        """Приостановить client и удалить"""
        await self.client.disconnect()
        del temp.controllers[self.user_id]
        logger.info(f"Контроллер {self} приостановлен и удален")


class ConnectAccountController(Controller):
    async def _get_code(self):
        logger.info(f"Ожидание кода {self}")
        queue: Queue = controller_codes_queue.get(self.user_id)
        code = await queue.get()
        queue.task_done()
        del queue
        return code

    async def clearing(self):
        await bot.send_message(self.user_id,
                               _("🚫 Ошибка, отмена привязки ... Попробуйте отключить Двухэтапную аутентификацию"))
        await self.client.disconnect()
        del controllers[self.user_id]
        self.path.unlink()
        del controller_codes_queue[self.user_id]
        logger.info(f"Временные файлы очищены {self}")

    async def get_code(self):
        try:
            return await asyncio.wait_for(self._get_code(), timeout=30)
        except Exception as e:
            logger.warning(f"Не удалось получить код для подключения {self} {e}")
            await storage.finish(user=self.user_id)
            await bot.send_message(self.user_id, "🚫 Ошибка, отмена привязки ...\nПовторите попытку",
                                   reply_markup=markups.common_menu.start_menu(self.user_id))
            await self.client.disconnect()
            del controllers[self.user_id]
            self.path.unlink()
            del controller_codes_queue[self.user_id]
            logger.info(f"Временные файлы очищены {self}")

    async def connect_finished_message(self):
        await self.client.send_message("me", "✅ Бот успешно подключен")
        await bot.send_message(
            self.user_id, "✅ Бот успешно подключен", reply_markup=common_menu.start_menu(self.user_id)
        )
        logger.success(f"Аккаунт пользователя {self} успешно подключен")

    async def try_connect(self):
        await self.client.sign_in()
        await self.client.start(lambda: self.phone, code_callback=lambda: self._get_code())

    async def connect_account(self):
        """Подключение аккаунта и создание сессии"""
        logger.debug(f"Подключение аккаунта {self}")
        try:
            await asyncio.wait_for(self.try_connect(), timeout=30)
        except Exception as e:
            logger.warning(f"Не удалось получить код для подключения {self} {e}")
            await self.clearing()
            raise e

        await storage.finish(user=self.user_id)
        await self.connect_finished_message()
        await User.connect_account(self)
        logger.success(f"Аккаунт пользователя {self} успешно подключен")

    async def start(self):
        self._init()
        logger.debug(f"Контроллер создан")
        await self.connect_account()
        await self.listening()


async def start_controller(acc: Account):
    acc_data = dict(acc)
    del acc_data["user_id"]
    controller = Controller(
        user_id=acc.user.user_id,
        username=acc.user.username,
        **acc_data,
        chats={chat.chat_id: chat for chat in acc.chats} or {},
    )
    asyncio.create_task(controller.start())
    logger.info(f"Контроллер {controller} запущен")


async def restart_controller(user):
    account = await Account.get(user=user).prefetch_related(
        "chats__message_filter__user_filters",
        "chats__message_filter__word_filter",
        "chats__chat_storage",
        "user",
    )
    await start_controller(account)
    # await controller.client.send_message("me", _("✅ Бот успешно подключен"))


async def init_controllers():
    logger.debug("Инициализация контролеров")
    # return
    for acc in await Account.all().prefetch_related(
            # for acc in await Account.filter(api_id=16629671).prefetch_related(
            "chats__message_filter__user_filters",
            "chats__message_filter__word_filter",
            "chats__chat_storage",
            "user",
    ):
        await start_controller(acc)
    logger.info("Контроллеры проинициализированы")


if __name__ == "__main__":
    pass
