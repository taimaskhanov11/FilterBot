import asyncio
from asyncio import Queue

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loguru import logger

from filterbot.apps.bot.filters.base_filters import UserFilter
from filterbot.apps.bot.temp import controller_codes_queue
from filterbot.apps.controller.controller import ConnectAccountController
from filterbot.db.models import User
from filterbot.loader import _


class ConnectAccount(StatesGroup):
    api = State()
    code = State()


async def connect_account(call: types.CallbackQuery):
    await call.message.answer(
        _("Для подключения аккаунта создайте приложение"
          " по ссылке https://my.telegram.org/auth?to=apps и сохраните api_id, api_hash.\n"
          "Отправьте сюда ваши данные в формате api_id:api_hash:номер_телефона. Пример\n"
          "123445:asdf31234fads:+79749599419")
    )
    await ConnectAccount.first()


async def connect_account_phone(message: types.Message, user: User, state: FSMContext):
    try:
        api_id, api_hash, phone = tuple(map(lambda x: x.strip(), message.text.split(":")))
        logger.info(f"{user.username}| Полученные данные {api_id}|{api_hash}|{phone}")
        client = ConnectAccountController(
            user_id=user.user_id,
            username=user.username,
            phone=phone,
            api_id=api_id,
            api_hash=api_hash
        )
        queue = Queue(maxsize=1)
        controller_codes_queue[user.user_id] = queue

        asyncio.create_task(client.start())
        await ConnectAccount.next()
        await message.answer(
            _("Введите код подтверждения из сообщения Телеграмм с префиксом code,"
              " в таком виде code<ваш код>\nНапример:\ncode43123")
        )
    except Exception as e:
        logger.critical(e)
        await message.answer(_("Неправильный ввод"))


async def connect_account_code(message: types.Message, user: User, state: FSMContext):
    code = message.text.replace("code", "")
    queue = controller_codes_queue.get(user.user_id)
    queue.put_nowait(code)
    await message.answer(_("✅ Код получен, ожидайте завершения\n Вам придет сообщение в личный чат."))
    await state.finish()


async def unlink_account(call: types.CallbackQuery, user: User):
    # todo 09.04.2022 21:50 taima: реализовать
    await call.message.answer(
        "Аккаунт успешно отвязан",
        # reply_markup=trigger_menu.get_trigger_menu(user)
    )


def register_connect_account_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(connect_account, UserFilter(), text="link_account")
    dp.register_message_handler(connect_account_phone, UserFilter(), state=ConnectAccount.api)
    dp.register_message_handler(connect_account_code, UserFilter(), state=ConnectAccount.code)
    dp.register_callback_query_handler(unlink_account, UserFilter(), text="unlink_account")
