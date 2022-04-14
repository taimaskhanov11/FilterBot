from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from loguru import logger

from filterbot.apps.bot import markups
from filterbot.apps.bot.callback_data.chat_filters_callback import promocode_cd
from filterbot.db.models import PromoCode


class CreatePromoCode(StatesGroup):
    name = State()
    limit = State()
    finish = State()


async def current_promocodes(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    promocodes = await PromoCode.all()
    await call.message.answer("Текущие промокоды",
                              reply_markup=markups.promocode_menu.current_promocodes(promocodes))
    # await CreatePromoCode.name.set()


async def get_promocode(call: types.CallbackQuery, state: FSMContext, callback_data: dict[str, str]):
    pk = callback_data.get("id")
    promocode = await PromoCode.get(pk=pk).select_related("user")
    await call.message.answer(f"{promocode}")
    await state.finish()


async def create_promocode(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer("Введите название для промокода", reply_markup=ReplyKeyboardRemove())
    await CreatePromoCode.name.set()


async def create_promocode_name(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Выберите количество чатов для парса по админам"
                         # ,reply_markup= markups.promocode_menu.create_promocode_name()
                         )
    await CreatePromoCode.limit.set()


async def create_promocode_limit(message: types.Message, state: FSMContext):
    await state.update_data(limit=message.text)
    await message.answer(f"Введите промокод", reply_markup=ReplyKeyboardRemove())
    await CreatePromoCode.finish.set()


async def create_promocode_finish(message: types.Message, state: FSMContext):
    try:
        await state.update_data(code=message.text)
        data = await state.get_data()
        await PromoCode.create(
            **data
        )
        await message.answer(f"Промоко успешно создан", reply_markup=markups.admin_menu.admin_start())
    except Exception as e:
        logger.critical(e)
        await message.answer(f"Ошибка при создании")
    await state.finish()


def register_promocode_menu(dp: Dispatcher):
    callback = dp.register_callback_query_handler
    message = dp.register_message_handler
    callback(current_promocodes, text="current_promocodes")
    callback(get_promocode, promocode_cd.filter(action="get"))

    callback(create_promocode, text="create_promocode")
    message(create_promocode_name, state=CreatePromoCode.name)
    message(create_promocode_limit, state=CreatePromoCode.limit)
    message(create_promocode_finish, state=CreatePromoCode.finish)
