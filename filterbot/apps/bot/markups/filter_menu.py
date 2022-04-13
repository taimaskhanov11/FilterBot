from aiogram.utils import markdown
from telethon.tl.custom import dialog

from filterbot.apps.bot.callback_data.chat_filters_callback import chat_cb, filter_cb
from filterbot.apps.bot.markups.utils import get_inline_keyboard
from filterbot.db.models import Chat, User
from filterbot.loader import _


def filter_menu():
    keyboard = [
        ((_("📄 Текущие фильтры"), "current_chat_filters"), (_("🔧 Выбрать чат для фильтра"), "create_chat_choice"),),
        ((_("↩ Главное меню"), "start"),),
    ]
    return get_inline_keyboard(keyboard)


def current_chat_filters(chats: list[Chat]):
    chats = [chat for chat in chats]
    chats.sort(key=lambda x: x.title)
    keyboard = [
        ((f"[#{num}] {chat.title}", chat_cb.new(chat_id=chat.pk, action="get")) for num, chat in enumerate(chats))
    ]
    keyboard.append(
        (("Назад", "chat_filters"),),
    )
    return get_inline_keyboard(keyboard)


def get_chat(chat_pk):
    keyboard = [
        ((_("Удалить"), chat_cb.new(chat_id=chat_pk, action="delete"),),),
        ((_("Назад"), "current_chat_filters"),),
    ]
    return get_inline_keyboard(keyboard)


def create_chat_choice(chats: list[dialog.Dialog]):
    chats.sort(key=lambda x: x.title)
    chats = [chat for chat in chats if not chat.is_user]
    new_chats = [chats[i:i + 2] for i in range(0, len(chats), 2)]
    keyboard = []
    for add_chats in new_chats:
        keyboard.append(
            (chat.title, chat_cb.new(chat_id=chat.id, action="create")) for chat in add_chats
        )
    # keyboard = [([chat.title, chat_cb.new(chat_id=chat.id, action="create")],) for chat in chats if not chat.is_user]
    # keyboard = (((chat.title, chat_cb.new(id=chat.id, action="create"),),) for chat in chats)
    keyboard.append(
        ((_("Назад"), "chat_filters"),),
    )
    return get_inline_keyboard(keyboard)


def create_chat_storage(storage_chats: list):
    storage_chats = [chat for chat in storage_chats if chat.creator]
    new_chats = [storage_chats[i:i + 2] for i in range(0, len(storage_chats), 2)]
    keyboard = []

    for add_chats in new_chats:
        keyboard.append(
            (chat.title, chat_cb.new(chat_id=chat.id, action="create"))
            for chat in add_chats
        )

    keyboard.append(
        ((_("Назад"), "chat_filters"),),
    )
    return get_inline_keyboard(keyboard)


async def get_admin_filters_count(user_id) -> int:
    user = await User.get(user_id=user_id).prefetch_related(
        "account__chats__message_filter__user_filters",
        "account__chats__message_filter__word_filter",
        "account__chats__chat_storage",
    ).annotate()
    admin_filter = 0
    for chat in user.account.chats:
        for user_filter in chat.message_filter.user_filters:
            if user_filter.filter_type == "admin":
                admin_filter += 1

    return admin_filter


async def create_chat_filter(user: User, again=False):
    # keyboard = [
    #     (("По ключевым словам", filter_cb.new(type="word")),),
    #     (("По ID пользователей", filter_cb.new(type="user_id")),),
    #     (("По Имени пользователей", filter_cb.new(type="username")),),
    #     (("Только от админов", filter_cb.new(type="admin")),),
    #     (("Главное меню", "main_menu"),),
    #     (("Завершить", filter_cb.new(type="complete")),) if again else (),
    # ]
    pr = await user.promocodes
    admin_filter = ()
    if pr:
        pr = pr[0]
        print(pr)
        current_limit = await get_admin_filters_count(user.user_id)
        print(current_limit)
        if current_limit < pr.limit:
            admin_filter = ((_("👤 Добавить Фильтр по админам"), filter_cb.new(type="admin")),)

    keyboard = [
        ((_("✍ Добавить По ключевым словам"), filter_cb.new(type="word")),),
        ((_("👥 Добавить Фильтр по пользователям"), filter_cb.new(type="user")),),
        admin_filter,
        ((_("Главное меню"), "start"),),
        ((_("✅ Завершить создание"), filter_cb.new(type="complete")),) if again else (),
    ]

    return get_inline_keyboard(keyboard)


def create_chat_filter_finish(count=1):
    statusbar = [
        ((markdown.italic("HAU HA") * count, "statusbar"),),
    ]
    return get_inline_keyboard(statusbar)
