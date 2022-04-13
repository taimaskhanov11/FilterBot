import asyncio
import pprint
from asyncio import Queue

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loguru import logger

from filterbot.apps.bot import temp, markups
from filterbot.apps.bot.filters.base_filters import UserFilter
from filterbot.apps.bot.markups import common_menu
from filterbot.apps.bot.temp import controller_codes_queue
from filterbot.apps.controller.controller import ConnectAccountController, Controller, restart_controller
from filterbot.db.models import User
from filterbot.loader import _


class ConnectAccount(StatesGroup):
    api = State()
    code = State()


class UnlinkAccount(StatesGroup):
    unlink = State()


async def connect_account(call: types.CallbackQuery):
    if controller := temp.controllers.get(call.from_user.id):
        controller: Controller
        if controller.client.is_connected():
            await call.message.answer(_("Ваш аккаунт уже подключен и запущен"))
            return

    await call.message.answer(
        _(
            "Для подключения аккаунта отключите Двухэтапную аутентификацию. Cоздайте приложение"
            " по ссылке https://my.telegram.org/auth?to=apps и сохраните api_id, api_hash.\n"
            "Отправьте сюда ваши данные в формате api_id:api_hash:номер_телефона. Пример\n"
            "123445:asdf31234fads:+79749599419"
        ), reply_markup=markups.common_menu.menu_button()
    )
    await ConnectAccount.first()


async def connect_account_phone(message: types.Message, user: User, state: FSMContext):
    try:
        await ConnectAccount.next()
        api_id, api_hash, phone = tuple(map(lambda x: x.strip(), message.text.split(":")))
        logger.info(f"{user.username}| Полученные данные {api_id}|{api_hash}|{phone}")
        account = await user.account
        if account:
            if account.api_id == int(api_id):
                await restart_controller(user)
                await message.answer(
                    _("✅ Бот успешно подключен, ожидайте пару секунд и нажмите кнопку ниже"),
                    reply_markup=common_menu.menu_button(),
                )
                logger.success(f"Аккаунт пользователя {user.user_id} успешно переподключен")
                await state.finish()
                return

        client = ConnectAccountController(
            user_id=user.user_id,
            username=user.username,
            phone=phone,
            api_id=api_id,
            api_hash=api_hash,
            chats={}
        )
        queue = Queue(maxsize=1)
        controller_codes_queue[user.user_id] = queue
        asyncio.create_task(client.start())
        await message.answer(
            _(
                "Введите код подтверждения из сообщения Телеграмм с префиксом code,"
                " в только таком виде code<ваш код>. Если отправить просто цифры то тг обнулит код\nНапример:\ncode43123"
            )
        )
    except Exception as e:
        logger.critical(e)
        await message.answer(_("Неправильный ввод"))


async def connect_account_code(message: types.Message, user: User, state: FSMContext):
    code = message.text
    if code.isdigit():
        await message.answer(
            _(f"❌ Неправильный ввод код.\nПожалуйста повторите попытку создания с первого этапа и введите код с префиксом code как узказано в примере ниже \n"
              f"Например:\ncode43123"), reply_markup=common_menu.start_menu(user.user_id))
        await state.finish()
        return
    code = message.text.replace("code", "")
    queue = controller_codes_queue.get(user.user_id)
    queue.put_nowait(code)
    await message.answer(
        _("Код получен, ожидайте завершения\nЕсли все прошло успешно Вам придет сообщение в личный чат."))
    await state.finish()


async def unlink_account(call: types.CallbackQuery):
    await call.message.answer(_("Вы точно хотите отвязать аккаунт?"), reply_markup=markups.common_menu.choice())
    await UnlinkAccount.unlink.set()


async def unlink_account_done(call: types.CallbackQuery, state: FSMContext):
    # todo 09.04.2022 21:50 taima: реализовать
    logger.info(pprint.pformat(temp.controllers))

    if call.data == "yes":
        controller: Controller = temp.controllers[call.from_user.id]
        await controller.stop()
        answer = _("✅ Аккаунт успешно отвязан\nГлавное меню")
    else:
        answer = _("Отвязка аккаунта отменена\nГлавное меню")
    await call.message.edit_text(answer)
    await call.message.edit_reply_markup(common_menu.start_menu(call.from_user.id))
    logger.info(pprint.pformat(temp.controllers))
    await state.finish()


async def run_client(call: types.CallbackQuery, user: User):
    logger.info(pprint.pformat(temp.controllers))
    controller: Controller = temp.controllers[call.from_user.id]
    await controller.run()
    # await call.message.edit_text("✅ Аккаунт успешно возобновлен\nГлавное меню")
    await call.message.edit_reply_markup(common_menu.start_menu(call.from_user.id))
    logger.info(pprint.pformat(temp.controllers))


async def pause_client(call: types.CallbackQuery, user: User):
    logger.info(pprint.pformat(temp.controllers))
    controller: Controller = temp.controllers[call.from_user.id]
    await controller.pause()
    # await call.message.edit_text("✅ Аккаунт успешно приостановлен\nГлавное меню")
    await call.message.edit_reply_markup(
        common_menu.start_menu(call.from_user.id),
    )
    logger.info(pprint.pformat(temp.controllers))


def register_connect_account_handlers(dp: Dispatcher):
    callback = dp.register_callback_query_handler
    message = dp.register_message_handler
    callback(connect_account, UserFilter(), text="link_account")
    message(connect_account_phone, UserFilter(), state=ConnectAccount.api)
    message(connect_account_code, UserFilter(), state=ConnectAccount.code)
    callback(unlink_account, text="unlink_account")
    callback(unlink_account_done, UserFilter(), state=UnlinkAccount.unlink)

    callback(run_client, UserFilter(), text="run_client")
    callback(pause_client, UserFilter(), text="pause_client")
