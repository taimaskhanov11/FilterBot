from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from filterbot.apps.bot import markups
from filterbot.apps.bot.filters.base_filters import UserFilter
from filterbot.apps.bot.markups import common_menu
from filterbot.db.models import User
from filterbot.loader import _


class LanguageChoice(StatesGroup):
    choice = State()


async def start(message: types.Message | types.CallbackQuery, state: FSMContext):
    if isinstance(message, types.CallbackQuery):
        message = message.message
    await state.finish()

    await message.answer("Главное меню", reply_markup=common_menu.start_menu(message.from_user.id))


async def language(call: types.CallbackQuery, user: User):
    await call.message.answer(
        _("Выберите язык интерфейса"),
        reply_markup=markups.common_menu.language(user.language),
    )
    await LanguageChoice.choice.set()


async def language_choice(call: types.CallbackQuery, user: User):
    await user.set_language(call.data)
    await call.message.answer(_("Язык интерфейса изменен"), reply_markup=markups.common_menu.language(user.language))


def register_common_handlers(dp: Dispatcher):
    callback = dp.register_callback_query_handler
    message = dp.register_message_handler
    message(start, UserFilter(), commands="start", state="*")
    callback(start, text="start", state="*")
    message(language, UserFilter(), text="language")
    callback(language_choice, UserFilter(), state=LanguageChoice.choice)