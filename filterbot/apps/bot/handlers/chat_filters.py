from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from filterbot.apps.bot import markups
from filterbot.apps.bot.callback_data.chat_filters_callback import chat_cb
from filterbot.loader import _


async def chat_filters_menu(call: types.CallbackQuery, state: FSMContext):
    """Меню для настройки фильтрации чатов"""
    await state.finish()
    await call.message.answer(_("Выберите функцию"), reply_markup=markups.filter_menu.filter_menu())


async def current_chats(call: types.CallbackQuery, state: FSMContext):
    """Получить список все чатов """
    await state.finish()
    pass


async def get_chat(call: types.CallbackQuery, callback_data: dict[str, str], state: FSMContext):
    """Получить основные данные по чату. Какие чаты подключены. Фильтрации и тд"""
    pass


def register_filter_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(chat_filters_menu, text="chat_filters")
    dp.register_callback_query_handler(current_chats, text="current_chats")
    dp.register_callback_query_handler(get_chat, chat_cb.filter(action="get"))
