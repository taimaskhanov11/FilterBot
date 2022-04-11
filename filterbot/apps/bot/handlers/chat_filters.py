import pprint

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from loguru import logger
from telethon import tl
from telethon.tl import functions
from telethon.tl.types import messages

from filterbot.apps.bot import markups, temp
from filterbot.apps.bot.callback_data.chat_filters_callback import chat_cb, filter_cb
from filterbot.apps.bot.filters.base_filters import UserFilter
from filterbot.apps.bot.temp import controllers
from filterbot.apps.controller.controller import Controller
from filterbot.db.models import User, MessageFilter, Chat, ChatStorage
from filterbot.loader import _


class CreateChat(StatesGroup):
    filter_type = State()
    filter_input = State()
    filter_additional = State()
    filter_finish = State()


class DeleteChat(StatesGroup):
    delete = State()


async def chat_filters_menu(call: types.CallbackQuery, state: FSMContext):
    """Меню для настройки фильтрации чатов"""
    controller: Controller = controllers.get(call.from_user.id)

    if not controller.client.is_connected():
        await call.message.answer(_("Для настройки фильтров возобновите работу бота"))
        return
    await state.finish()
    await call.message.answer(_("Выберите функцию"), reply_markup=markups.filter_menu.filter_menu())


async def current_chat_filters(call: types.CallbackQuery, state: FSMContext):
    """Получить список чатов с фильтрами"""
    await state.finish()
    user = await User.get(user_id=call.from_user.id).prefetch_related("account__chats")
    await call.message.answer(
        _("Текущие чаты с фильтрами"), reply_markup=markups.filter_menu.current_chat_filters(user.account.chats)
    )


async def get_chat(call: types.CallbackQuery, callback_data: dict[str, str], state: FSMContext):
    """Получить основные данные по чату. Какие чаты подключены. Фильтрации и тд"""
    chat_pk = callback_data.get("chat_id")
    chat = await Chat.get(pk=chat_pk).prefetch_related(
        "chat_storage",
        "message_filter__user_filter",
        "message_filter__word_filter",
    )
    await call.message.answer(chat.pretty(), "HTML", reply_markup=markups.filter_menu.get_chat(chat.pk))


async def delete_chat(call: types.CallbackQuery, callback_data: dict[str, str], state: FSMContext):
    await state.update_data(delete_chat_id=callback_data.get("chat_id"))
    await call.message.answer(
        _("Вы действительно хотите удалить фильтр чата?"), reply_markup=markups.common_menu.choice()
    )
    await DeleteChat.delete.set()


async def delete_chat_finish(call: types.CallbackQuery, state: FSMContext):
    if call.data == "yes":
        data = await state.get_data()
        chat = await Chat.delete_chat(data["delete_chat_id"])
        answer = _("Чат {title} успешно удален").format(title=chat.title)
    else:
        answer = _("Удаление отменено")
    await call.message.answer(answer, reply_markup=markups.filter_menu.filter_menu())
    await state.finish()


async def create_chat_choice(call: types.CallbackQuery, user: User, state: FSMContext):
    """Начало для создания фильтра для чата"""
    await state.finish()
    controller: Controller = temp.controllers.get(user.user_id)
    chats = await controller.client.get_dialogs()
    # chats: messages.Chats = await controller.client(functions.messages.GetAllChatsRequest(except_ids=[]))
    # chats = chats.chats
    await call.message.answer(
        _(f"Ваши текущие чаты без фильтров. Выберите чат из списка для создания фильтра:\n"),
        reply_markup=markups.filter_menu.create_chat_choice(chats),
    )


async def create_chat_storage(call: types.CallbackQuery, state: FSMContext, callback_data: dict[str, str]):
    await state.update_data(
        filter_chat={
            "chat_id": callback_data["chat_id"],
            # "title": callback_data["title"]
        }
    )
    controller: Controller = temp.controllers.get(call.from_user.id)
    storage_chats: messages.Chats = await controller.client(functions.messages.GetAllChatsRequest(except_ids=[]))
    await call.message.answer(
        _("Выберите хранилище, куда будут пересылаться сообщения"),
        reply_markup=markups.filter_menu.create_chat_storage(storage_chats.chats),
    )
    await CreateChat.filter_type.set()


async def create_chat_filter_type(call: types.CallbackQuery, state: FSMContext, callback_data: dict[str, str]):
    await state.update_data(
        chat_storage={
            "chat_id": callback_data["chat_id"],
            # "title": callback_data["title"]
        }
    )
    await call.message.answer(_("Выберите тип фильтра"), reply_markup=markups.filter_menu.create_chat_filter())
    await state.update_data(filters=[])
    await CreateChat.filter_input.set()


async def create_chat_filter_input(
        call: types.CallbackQuery, user: User, state: FSMContext, callback_data: dict[str, str]
):
    filter_type = callback_data.get("type")
    await state.update_data(filter_type=filter_type)
    match filter_type:
        case "word":
            answer = _(
                "Ведите ключевые слова для фильтра через запятую. Например:\n"
                "подтвердить, забрать, вознаграждение, получить, claim, mint, rewards"
            )
        case "user":
            answer = _(
                "Ведите Имена пользователей или их ID для фильтра через запятую. Например:\n"
                "alisiya, 1985947355, vsl48, alena_helpchina, 5036099266, 1985947355"
            )
        case "admin":
            answer = _(
                "Ведите Имя пользователя админов для фильтра через запятую. Например:\n"
                "pallarisss, Tiamat_mag, Sstasicc"
            )
            # answer = _("")
            # pass
        case "complete":
            await create_chat_filter_finish(call, user, state)
            return
            # answer = _("")
            # todo 10.04.2022 23:07 taima:
        case _:
            answer = _("")

    await call.message.answer(answer, reply_markup=ReplyKeyboardRemove())
    # await state.update_data()
    await CreateChat.filter_additional.set()


async def create_chat_filter_additional(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        text = message.text
        _add_text = ""
        # if data["filter_type"] in ("user_id", "username", "admin"):
        if data["filter_type"] != "word":
            # todo 4/11/2022 5:08 PM taima: вынести в controller
            controller: Controller = controllers.get(message.from_user.id)
            ids = await controller.get_users_ids(text)
            _add_text = _(f"Полученные id по именам пользователя\n{ids}")
            text = ids

        _filter = {
            "type": data["filter_type"],
            "data": text,
        }

        data["filters"].append(_filter)
        await state.update_data(data)
        await message.answer(
            _(f"Фильтр добавлен.\n{_add_text}" f"{pprint.pformat(data['filters'])}\n" "Хотите добавить еще?"),
            reply_markup=markups.filter_menu.create_chat_filter(again=True),
        )

        await CreateChat.filter_input.set()
    except Exception as e:
        logger.warning(e)
        await message.answer(_("Ошибка. Проверьте правильность введенных данных."))


async def create_chat_filter_finish(call: types.CallbackQuery, user: User, state: FSMContext):
    await call.message.answer(
        _(f"Данные успешно получены. Идет создание фильтра..."),
        # reply_markup=markups.filter_menu.create_chat_filter_finish(), parse_mode="HTML"
    )

    data = await state.get_data()
    _chat_storage_id = data["chat_storage"]["chat_id"]
    _filter_chat_id = data["filter_chat"]["chat_id"]
    _filters = data["filters"]

    controller: Controller = controllers.get(call.from_user.id)

    chat_entity: tl.types.Chat = await controller.client.get_entity(int(_chat_storage_id))
    chat_storage = await ChatStorage.create(chat_id=_chat_storage_id, title=chat_entity.title)

    message_filter = await MessageFilter.create_filter(_filters)
    chat_entity: types.Chat = await controller.client.get_entity(int(_filter_chat_id))
    chat = await Chat.create(
        chat_id=_filter_chat_id,
        title=chat_entity.title,
        message_filter=message_filter,
        account=await user.account,
        chat_storage=chat_storage,
    )
    print(chat.message_filter.user_filter)
    print(chat.message_filter.word_filter)
    print(bool(chat.message_filter.user_filter))
    if not controller.chats:
        controller.chats = {}
    controller.chats[chat.chat_id] = chat

    await call.message.answer(_("Фильтр успешно создан"), reply_markup=markups.filter_menu.filter_menu())
    await call.message.answer(pprint.pformat(data))
    await state.finish()


def register_chat_filter_handlers(dp: Dispatcher):
    callback = dp.register_callback_query_handler
    message = dp.register_message_handler
    callback(chat_filters_menu, text="chat_filters")
    callback(current_chat_filters, UserFilter(), text="current_chat_filters")
    callback(get_chat, chat_cb.filter(action="get"))
    callback(delete_chat, chat_cb.filter(action="delete"))
    callback(delete_chat_finish, state=DeleteChat.delete)

    # create chat filter
    callback(create_chat_choice, UserFilter(), text="create_chat_choice")
    callback(create_chat_storage, chat_cb.filter(action="create"))
    callback(create_chat_filter_type, chat_cb.filter(action="create"), state=CreateChat.filter_type)
    callback(create_chat_filter_input, UserFilter(), filter_cb.filter(), state=CreateChat.filter_input)
    message(create_chat_filter_additional, state=CreateChat.filter_additional)
    # message(create_chat_filter_finish, UserFilter(), state=CreateChat.filter_finish)
