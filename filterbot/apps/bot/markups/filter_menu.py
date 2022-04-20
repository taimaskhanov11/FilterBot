from aiogram.utils import markdown
from telethon.tl.custom import dialog

from filterbot.apps.bot.callback_data.chat_filters_callback import chat_cb, filter_cb
from filterbot.apps.bot.markups.utils import get_inline_keyboard
from filterbot.db.models import Chat, User, PromoCode
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
    new_chats = [chats[i:i + 2] for i in range(0, len(chats), 2)]
    keyboard = []
    for add_chats in new_chats:
        keyboard.append(
            # (chat.title, chat_cb.new(chat_id=chat.id, action="create")) for chat in add_chats
            # (f"[#{num}] {chat.title}", chat_cb.new(chat_id=chat.pk, action="get")) for num, chat in enumerate(add_chats)
            (f"{chat.title}", chat_cb.new(chat_id=chat.pk, action="get")) for chat in add_chats
        )

    # keyboard = [
    #     ((f"[#{num}] {chat.title}", chat_cb.new(chat_id=chat.pk, action="get")) for num, chat in enumerate(chats))
    # ]
    keyboard.append(
        (("Назад", "chat_filters"),),
    )
    return get_inline_keyboard(keyboard)


def get_chat(chat: Chat):
    keyboard = [
        ((_("❌ Удалить фильтр"), chat_cb.new(chat_id=chat.pk, action="delete"),),),
        ((_("Назад"), "current_chat_filters"),),
    ]
    if chat.message_filter.user_filters:
        keyboard.append(((_("👥 Добавить пользователя"), chat_cb.new(chat_id=chat.pk, action="add_user"),),
                         (_("👥 Удалить пользователя"), chat_cb.new(chat_id=chat.pk, action="delete_user"),),))
    if chat.message_filter.word_filter:
        keyboard.append(((_("✍ Удалить ключевое слово"), chat_cb.new(chat_id=chat.pk, action="delete_word"),),
                         (_("✍ Добавить ключевое слово"), chat_cb.new(chat_id=chat.pk, action="add_word"),),))
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
    )
    return len(user.account.chats)


async def create_chat_filter(promocode: PromoCode, again=False):
    # keyboard = [
    #     (("По ключевым словам", filter_cb.new(type="word")),),
    #     (("По ID пользователей", filter_cb.new(type="user_id")),),
    #     (("По Имени пользователей", filter_cb.new(type="username")),),
    #     (("Только от админов", filter_cb.new(type="admin")),),
    #     (("Главное меню", "main_menu"),),
    #     (("Завершить", filter_cb.new(type="complete")),) if again else (),
    # ]
    admin_filter = ()
    if promocode:
        # print(pr)
        # todo 4/19/2022 12:14 PM taima: большая нагрузка
        # print(current_limit)
        if promocode.admin_limit > 0:
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
