from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from loguru import logger

from filterbot.apps.bot import markups
from filterbot.apps.bot.callback_data.chat_filters_callback import user_cd
from filterbot.apps.bot.utils.statistic import statistic_storage
from filterbot.config.config import config
from filterbot.db.models import User, Account, Chat, MessageFilter


async def admin_start(message: types.CallbackQuery | types.Message, state: FSMContext):
    await state.finish()

    if isinstance(message, types.CallbackQuery):
        message = message.message
    await message.answer(f"Выберите функцию", reply_markup=markups.admin_menu.admin_start())


async def current_users(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    users = await User.all()
    await call.message.answer(f"Текущие пользователи", reply_markup=markups.admin_menu.current_users(users))


async def user_statistics(call: types.CallbackQuery, state: FSMContext, callback_data: dict[str, str]):
    await state.finish()
    try:
        stats = await statistic_storage.get_by_user_stats(callback_data.get("id"))
        await call.message.answer(stats, reply_markup=markups.admin_menu.admin_button())
    except Exception as e:
        logger.critical(e)
        await call.message.answer(f"Пользователь не подключил фильтры")


async def admin_statistic(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    users = await User.all().count()
    accounts = await Account.all().count()
    chats = await Chat.all().count()
    filters = await MessageFilter.all().count()
    all_message = statistic_storage.get("all_message")
    filter_message = statistic_storage.get("filter_message")

    await call.message.answer(
        f"Всего пользователей: {users}\n"
        f"Всего аккаунтов: {accounts}\n"
        f"Всего чатов: {chats}\n"
        f"Всего фильтров: {filters}\n"
        f"Всего входящих сообщений: {all_message}\n"
        f"Всего отфильтрованных сообщений: {filter_message}\n"
    )


def register_admin_menu(dp: Dispatcher):
    callback = dp.register_callback_query_handler
    message = dp.register_message_handler
    message(admin_start, user_id=config.bot.admins, commands="admin", state="*")
    callback(admin_start, user_id=config.bot.admins, text="admin", state="*")

    callback(admin_statistic, user_id=config.bot.admins, text="admin_statistic", state="*")
    callback(current_users, user_id=config.bot.admins, text="current_users", state="*")
    # callback(admin_statistic, user_id=config.bot.admins, text="admin_statistic", state="*")

    callback(user_statistics, user_cd.filter(), user_id=config.bot.admins, state="*")
