from aiogram.utils import markdown
from telethon.tl.custom import dialog

from filterbot.apps.bot.callback_data.chat_filters_callback import chat_cb, filter_cb
from filterbot.apps.bot.markups.utils import get_inline_keyboard
from filterbot.db.models import Chat


def filter_menu():
    keyboard = [
        (("Текущие фильтры", "current_chat_filters"),),
        (("Выбрать чат для фильтра", "create_chat_choice"),),
        (("Главное меню", "main_menu"),),
    ]
    return get_inline_keyboard(keyboard)


def current_chat_filters(chats: list[Chat]):
    keyboard = [
        ((f"[#{num}] {chat.title}", chat_cb.new(chat_id=chat.pk, action="get")) for num, chat in enumerate(chats))
    ]
    return get_inline_keyboard(keyboard)


def get_chat(chat_pk):
    chat_cb.filter(action="create")
    keyboard = [
        (
            (
                "Удалить",
                chat_cb.new(chat_id=chat_pk, action="delete"),
            ),
        )
    ]
    return get_inline_keyboard(keyboard)


def create_chat_choice(chats: list[dialog.Dialog]):
    # keyboard = (((chat.title, chat_cb.new(id=chat.id, action="create"),),) for chat in chats if not chat.creator)
    # keyboard = (((chat.title, chat_cb.new(id=chat.id, action="create"),),) for chat in chats)
    keyboard = (([chat.title, chat_cb.new(chat_id=chat.id, action="create")],) for chat in chats if not chat.is_user)
    # keyboard = (((chat.title, chat_cb.new(id=chat.id, action="create"),),) for chat in chats)
    return get_inline_keyboard(keyboard)


def create_chat_storage(storage_chats: list):
    keyboard = (
        (
            (
                chat.title,
                chat_cb.new(chat_id=chat.id, action="create"),
            ),
        )
        for chat in storage_chats
        if chat.creator
    )
    return get_inline_keyboard(keyboard)


def create_chat_filter(again=False):
    # keyboard = [
    #     (("По ключевым словам", filter_cb.new(type="word")),),
    #     (("По ID пользователей", filter_cb.new(type="user_id")),),
    #     (("По Имени пользователей", filter_cb.new(type="username")),),
    #     (("Только от админов", filter_cb.new(type="admin")),),
    #     (("Главное меню", "main_menu"),),
    #     (("Завершить", filter_cb.new(type="complete")),) if again else (),
    # ]
    keyboard = [
        (("По ключевым словам", filter_cb.new(type="word")),),
        (("Фильтр по пользователям", filter_cb.new(type="user")),),
        (("Фильтр по админам", filter_cb.new(type="admin")),),
        (("Главное меню", "main_menu"),),
        (("Завершить", filter_cb.new(type="complete")),) if again else (),
    ]

    return get_inline_keyboard(keyboard)


def create_chat_filter_finish(count=1):
    statusbar = [
        ((markdown.italic("HAU HA") * count, "statusbar"),),
    ]
    return get_inline_keyboard(statusbar)


