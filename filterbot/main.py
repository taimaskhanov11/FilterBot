import asyncio
import logging

from aiogram import Bot
from aiogram.types import BotCommand
from loguru import logger

from filterbot.apps.bot.handlers.admin_handlers.admin_menu import register_admin_menu
from filterbot.apps.bot.handlers.admin_handlers.ban_menu import register_ban_menu
from filterbot.apps.bot.handlers.admin_handlers.promocode_menu import register_promocode_menu
from filterbot.apps.bot.handlers.chat_filters import register_chat_filter_handlers
from filterbot.apps.bot.handlers.common_menu import register_common_handlers
from filterbot.apps.bot.handlers.connect_account import register_connect_account_handlers
from filterbot.apps.bot.handlers.edit_chat_filters import register_edit_chat_filter_handlers
from filterbot.apps.bot.handlers.errors_handlers import register_error_handlers
from filterbot.apps.bot.utils.locales_helpers import update_users_locales
from filterbot.apps.controller.controller import init_controllers
from filterbot.config.config import config, config_file
from filterbot.config.setting_logging import init_logging
from filterbot.db.db_main import init_tortoise
from filterbot.loader import bot, dp


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Главное меню"),
        BotCommand(command="/admin", description="Админ меню"),
    ]
    await bot.set_my_commands(commands)


# todo 01.04.2022 1:08 taima:  tzlocal, scheduler
# todo 01.04.2022 15:29 taima: F, Q tortoise;atomic;
async def main():
    # Настройка логирования
    init_logging(
        filename=config_file or "",
        old_logger=True,
        level="TRACE",
        # old_level=logging.DEBUG,
        old_level=logging.INFO,
        steaming=True,
        write=True,
    )

    logger.success(f"Starting bot {(await bot.get_me()).username}")

    # Установка команд бота
    await set_commands(bot)

    # Инициализация бд
    await init_tortoise(**config.db.dict())

    # Меню админа
    # register_admin_commands_handlers(dp)

    # Регистрация хэндлеров
    register_common_handlers(dp)

    # admin
    register_admin_menu(dp)
    register_promocode_menu(dp)
    register_ban_menu(dp)

    # common
    register_connect_account_handlers(dp)
    register_chat_filter_handlers(dp)
    register_edit_chat_filter_handlers(dp)
    register_error_handlers(dp)
    # Регистрация middleware

    # Регистрация фильтров

    # Инициализация контроллеров
    await init_controllers()

    await update_users_locales()
    # Запуск поллинга
    # updates()  # пропуск накопившихся апдейтов (необязательно)
    # controller = Controller(**config.controller.dict())
    # config.controller.controller = controller
    # asyncio.create_task(controller.start())
    # scheduler.start()
    await dp.skip_updates()
    await dp.start_polling()


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.get_event_loop()
