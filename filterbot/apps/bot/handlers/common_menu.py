from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils import markdown
from loguru import logger

from filterbot.apps.bot import markups
from filterbot.apps.bot.filters.base_filters import UserFilter
from filterbot.apps.bot.markups import common_menu
from filterbot.apps.bot.temp import users_locales
from filterbot.apps.bot.utils.statistic import statistic_storage
from filterbot.db.models import User, PromoCode
from filterbot.loader import _


class LanguageChoice(StatesGroup):
    choice = State()


class InputPromocode(StatesGroup):
    input = State()


async def start(message: types.Message | types.CallbackQuery, user: User, state: FSMContext):
    if isinstance(message, types.CallbackQuery):
        message = message.message
    await state.finish()
    await message.answer(_("Главное меню:"), "html", reply_markup=common_menu.start_menu(user.user_id))


async def profile(call: types.CallbackQuery, user: User, state: FSMContext):
    await state.finish()
    await call.message.answer(
        f"🔑 ID: {user.user_id}\n" f"👤 Username: @{user.username}\n\n" f"{markdown.hbold(_('🛠 В разработке...'))}" f"",
        "html",
    )


async def support(call: types.CallbackQuery, user: User, state: FSMContext):
    await state.finish()
    await call.message.answer(markdown.hbold(_("По всем вопросам пишите: @Les0k")), "html")


async def language(call: types.CallbackQuery, user: User):
    await call.message.answer(
        _("Выберите язык интерфейса:"),
        reply_markup=markups.common_menu.language(user.language),
    )
    await LanguageChoice.choice.set()


async def language_choice(call: types.CallbackQuery, user: User):
    await user.set_language(call.data)
    await user.set_language(call.data)
    users_locales[user.user_id] = user.language
    await call.message.answer(_("Язык интерфейса изменен"), reply_markup=markups.common_menu.language(user.language))


async def statistic(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    try:
        await call.message.answer(await statistic_storage.get_by_user_stats(call.from_user.id))
    except Exception as e:
        logger.critical(e)
        await call.message.answer(_("Фильтры не подключены"))


async def current_promocode(call: types.CallbackQuery, user: User, state: FSMContext):
    try:
        await state.finish()
        promocode = await PromoCode.get(user=user).select_related("user")
        await call.message.answer(str(promocode), reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logger.warning(e)
        await call.message.answer(_("Нет активного промокода\nПо всем вопросам пишите: @Les0k"))


async def input_promocode(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer(_(f"Введите промокод\nНапример:\npromocode1234"), reply_markup=ReplyKeyboardRemove())
    await InputPromocode.input.set()


async def input_promocode_done(message: types.Message, user: User, state: FSMContext):
    promo_code = await PromoCode.filter(code=message.text).select_related("user").first()
    if promo_code:
        if not promo_code.user:
            old_promo_code = await user.promocode
            old_promo_code.user = None
            await old_promo_code.save()
            promo_code.user = user
            await promo_code.save()
            await message.answer(
                _(
                    "✅ Промокод {promocode} успешно активирован.\n"
                    "Количество привязок по админам: {admin}\n"
                    "Количество фильтров {filter}"
                ).format(promocode=promo_code.title, admin=promo_code.admin_limit, filter=promo_code.admin_limit),
                reply_markup=common_menu.start_menu(user.user_id),
            )

            await state.finish()
        else:
            await message.answer(_("Уже использован"))
    else:
        await message.answer(_("Неправильный ввод"), reply_markup=common_menu.start_menu(user.user_id))
    await state.finish()


def register_common_handlers(dp: Dispatcher):
    callback = dp.register_callback_query_handler
    message = dp.register_message_handler
    message(start, UserFilter(), commands="start", state="*")
    callback(start, UserFilter(), text="start", state="*")
    callback(profile, UserFilter(), text="profile", state="*")
    callback(support, UserFilter(), text="support", state="*")
    callback(statistic, text="statistic", state="*")
    callback(input_promocode, text="input_promocode", state="*")
    callback(current_promocode, UserFilter(), text="current_promocode", state="*")

    message(input_promocode_done, UserFilter(), state=InputPromocode.input)

    callback(language, UserFilter(), text="language", state="*")
    callback(language_choice, UserFilter(), state=LanguageChoice.choice)
