from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from loguru import logger

from filterbot.config.config import config


class Ban(StatesGroup):
    add = State()
    delete = State()


async def ban_list(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.answer(config.bot.block_list)


async def delete_ban(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await Ban.delete.set()
    await call.message.answer("Введите id для удаления из бан листа")


async def delete_ban_done(message: types.Message, state: FSMContext):
    await state.finish()
    try:
        user_id = int(message.text)
        config.bot.block_list.remove(user_id)
        await message.answer(f"{user_id} успешно удален {config.bot.block_list}")
    except Exception as e:
        logger.critical(e)
        await message.answer(f"Не удалось удалить\n{config.bot.block_list}")


async def add_ban(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await Ban.add.set()
    await call.message.answer("Введите id для добавления в бан лист")


async def add_ban_done(message: types.Message, state: FSMContext):
    await state.finish()
    try:
        user_id = int(message.text)
        config.bot.block_list.append(user_id)
        await message.answer(f"{user_id} успешно добавлен {config.bot.block_list}")
    except Exception as e:
        logger.critical(e)
        await message.answer(f"Не удалось добавить\n{config.bot.block_list}")


def register_ban_menu(dp: Dispatcher):
    callback = dp.register_callback_query_handler
    message = dp.register_message_handler
    callback(ban_list, text="ban_list", state="*")
    callback(add_ban, text="add_ban", state="*")
    message(add_ban_done, state=Ban.add)
    callback(delete_ban, text="delete_ban", state="*")
    message(delete_ban_done, state=Ban.delete)
