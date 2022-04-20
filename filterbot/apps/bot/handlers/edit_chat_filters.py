from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from loguru import logger

from filterbot.apps.bot import markups
from filterbot.apps.bot.callback_data.chat_filters_callback import chat_cb
from filterbot.apps.bot.temp import controllers
from filterbot.apps.controller.controller import Controller
from filterbot.db.models import Chat
from filterbot.loader import _


class EditFilter(StatesGroup):
    delete_user = State()
    add_user = State()
    delete_word = State()
    add_word = State()


async def delete_user(call: types.CallbackQuery, callback_data: dict[str, str], state: FSMContext):
    await state.finish()
    await state.update_data(delete_user_chat_id=callback_data.get("chat_id"))
    await call.message.answer(_("Введите id пользователя для удаления"))
    await EditFilter.delete_user.set()


async def delete_user_complete(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        chat_pk = data["delete_user_chat_id"]
        controller: Controller = controllers.get(message.from_user.id)
        chat: Chat = await Chat.get(pk=chat_pk)
        chat = controller.chats.get(chat.chat_id)
        ids = await controller.get_users_ids(message.text)

        for _filter in chat.message_filter.user_filters:
            for user_username in ids.keys():
                if user_username in _filter.ids:
                    del _filter.ids[user_username]
                    await _filter.save()

        await chat.save()
        await message.answer(
            f"{_('ID успешно добавлено')}\n{chat.pretty()}", "html", reply_markup=markups.filter_menu.get_chat(chat)
        )

    except Exception as e:
        logger.critical(e)
        await message.answer(_("Не удалось удалить пользователя"))
    await state.finish()


async def add_user(call: types.CallbackQuery, callback_data: dict[str, str], state: FSMContext):
    await state.finish()
    await state.update_data(add_user_chat_id=callback_data.get("chat_id"))
    await call.message.answer(_("Введите id пользователя для добавления"))
    await EditFilter.add_user.set()


async def add_user_complete(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        chat_pk = data["add_user_chat_id"]
        controller: Controller = controllers.get(message.from_user.id)
        chat: Chat = await Chat.get(pk=chat_pk)
        chat = controller.chats.get(chat.chat_id)
        ids = await controller.get_users_ids(message.text)

        for _filter in chat.message_filter.user_filters:
            if _filter.filter_type == "user":
                _filter.ids.update(ids)
                await _filter.save()

        await chat.save()
        await message.answer(
            f"{_('ID успешно добавлено')}\n{chat.pretty()}", "html", reply_markup=markups.filter_menu.get_chat(chat)
        )

    except Exception as e:
        logger.critical(e)
        await message.answer(_("Не удалось добавить пользователя"))
    await state.finish()


async def delete_word(call: types.CallbackQuery, callback_data: dict[str, str], state: FSMContext):
    await state.finish()
    await state.update_data(delete_word_chat_id=callback_data.get("chat_id"))
    await call.message.answer(_("Введите слово для удаления"))
    await EditFilter.delete_word.set()


async def delete_word_complete(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        chat_pk = data["delete_word_chat_id"]
        controller: Controller = controllers.get(message.from_user.id)
        chat: Chat = await Chat.get(pk=chat_pk)
        chat = controller.chats.get(chat.chat_id)
        words_lst = list(map(lambda x: x.strip(), message.text.split(",")))
        word_filter = chat.message_filter.word_filter
        for word in words_lst:
            if word in word_filter.words:
                word_filter.words.remove(word)
                await word_filter.save()
        await chat.save()
        await message.answer(
            f"{_('Слово успешно удалено')}\n{chat.pretty()}", "html", reply_markup=markups.filter_menu.get_chat(chat)
        )

    except Exception as e:
        logger.critical(e)
        await message.answer(_("Не удалось удалить слово"))
    await state.finish()


async def add_word(call: types.CallbackQuery, callback_data: dict[str, str], state: FSMContext):
    await state.finish()
    await state.update_data(add_word_chat_id=callback_data.get("chat_id"))
    await call.message.answer(_("Введите слово для добавления"))
    await EditFilter.add_word.set()


async def add_word_complete(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        chat_pk = data["add_word_chat_id"]
        controller: Controller = controllers.get(message.from_user.id)
        chat: Chat = await Chat.get(pk=chat_pk)
        chat = controller.chats.get(chat.chat_id)
        words_lst = list(map(lambda x: x.strip(), message.text.split(",")))
        word_filter = chat.message_filter.word_filter
        word_filter.words.extend(words_lst)
        await word_filter.save()
        await chat.save()
        await message.answer(
            f"{_('Слово успешно добавлено')}\n{chat.pretty()}",
            "html",
            reply_markup=markups.filter_menu.get_chat(chat),
        )

    except Exception as e:
        logger.critical(e)
        await message.answer(_("Не удалось добавить слово"))
    await state.finish()


def register_edit_chat_filter_handlers(dp: Dispatcher):
    callback = dp.register_callback_query_handler
    message = dp.register_message_handler
    callback(delete_user, chat_cb.filter(action="delete_user"), state="*")
    message(delete_user_complete, state=EditFilter.delete_user)

    callback(add_user, chat_cb.filter(action="add_user"), state="*")
    message(add_user_complete, state=EditFilter.add_user)

    callback(delete_word, chat_cb.filter(action="delete_word"), state="*")
    message(delete_word_complete, state=EditFilter.delete_word)

    callback(add_word, chat_cb.filter(action="add_word"), state="*")
    message(add_word_complete, state=EditFilter.add_word)
