from filterbot.apps.bot import temp
from filterbot.apps.bot.markups.utils import get_inline_keyboard


def start_menu(user_id):
    if controller := temp.controllers.get(user_id):
        controller_status = (("❌ Отвязать аккаунт", "unlink_account"),)
        client_status = (
            (("⏸ Приостановить бота", "pause_client"),)
            if controller.client.is_connected()
            else (("🔄 Возобновить бота", "run_client"),)
        )
    else:
        controller_status = (("➕ Привязать аккаунт", "link_account"),)
        client_status = ()
    keyboard = [
        (("👤 Мой профиль", "profile"),),
        controller_status,
        client_status,
        (("⚙ Настройки фильтров чатов", "chat_filters"),),
        (("🇷🇺Язык (🇺🇸 language)", "language"), ("💬 Поддержка", "support")),
    ]
    return get_inline_keyboard(keyboard)


def language(lang):
    keyboard = [
        (("🇷🇺 Русский", "ru"),) if lang == "en" else (("🇺🇸 English", "en"),),
        (("Главное меню", "start"),),
    ]
    return get_inline_keyboard(keyboard)


def menu():
    keyboard = [
        (("Главное меню", "start"),),
    ]
    return get_inline_keyboard(keyboard)


def choice():
    keyboard = [
        (("Да", "yes"),),
        (("Нет", "no"),),
    ]
    return get_inline_keyboard(keyboard)
