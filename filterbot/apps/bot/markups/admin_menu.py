from filterbot.apps.bot.callback_data.chat_filters_callback import user_cd
from filterbot.apps.bot.markups.utils import get_inline_keyboard
from filterbot.db.models import User


def admin_start():
    keyword = [
        (("👥 Все пользователи", "current_users"),),
        (("📈 Общая статистика", "admin_statistic"),),
        # (("👤 Мой профиль", "profile"),),
    ]

    return get_inline_keyboard(keyword)

def user_statistics():
    keyword = [
        (("👥 Все пользователи", "current_users"),),
        (("📈 Общая статистика", "admin_statistic"),),
        # (("👤 Мой профиль", "profile"),),
    ]

    return get_inline_keyboard(keyword)


def current_users(users: list[User]):
    # users.sort(key=lambda x: x.title)
    # chats = [chat for chat in users if not chat.is_user]
    new_users = [users[i:i + 2] for i in range(0, len(users), 2)]
    keyboard = []
    for add_users in new_users:
        keyboard.append(
            (user.username, user_cd.new(id=user.user_id)) for user in add_users
        )
    # keyboard = [([chat.title, chat_cb.new(chat_id=chat.id, action="create")],) for chat in chats if not chat.is_user]
    # keyboard = (((chat.title, chat_cb.new(id=chat.id, action="create"),),) for chat in chats)
    keyboard.append(
        (("Назад", "admin"),),
    )

    return get_inline_keyboard(keyboard)

def admin_button():
    keyboard = [
        (("Админ меню", "admin"),),
    ]
    return get_inline_keyboard(keyboard)
