import asyncio
from asyncio import Task

from loguru import logger

from telethoncontrollerbot.apps.controller.controller import Controller
from telethoncontrollerbot.db.models import Account

SESSION_TASKS: dict[int, Task] = {}


async def start_session(acc):  # todo 3/6/2022 9:14 PM taima:
    controller = Controller(
        user_id=acc.db_user.user_id,
        username=acc.db_user.username,
        number=acc.number,
        api_id=acc.api_id,
        api_hash=acc.api_hash,
    )
    task = asyncio.create_task(controller.start())
    SESSION_TASKS[acc.db_user.user_id] = task
    logger.info(f"Сессия {acc.db_user.user_id} запущена")


async def init_sessions():
    logger.debug("Initializing session")
    for acc in await Account.all().select_related("db_user"):
        await start_session(acc)
    logger.info("Session initialized")
