from aiogram import Dispatcher
from loguru import logger


async def error_handler(update, exception):
    logger.exception(f"{exception}|{update}")
    return True


def register_error_handlers(dp: Dispatcher):
    dp.register_errors_handler(error_handler)
