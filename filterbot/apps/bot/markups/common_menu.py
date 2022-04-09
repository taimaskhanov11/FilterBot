from filterbot.apps.bot.markups.utils import get_inline_keyboard


def start_menu():
    keyboard = [
        (("Мой профиль", "profile"),),
        (("Привязать аккаунт", "link_account"),),
        (("Отвязать аккаунт", "unlink_account"),),
        (("Настройки фильтров", "chat_filters"),),
        (("Язык (language)", "language"), ("Поддержка", "support")),
    ]
    return get_inline_keyboard(keyboard)


def language(lang):
    keyboard = [
        (("Русский", "ru"),) if lang == "en" else (("English", "en"),),
        (("Главное меню", "start"),),
    ]
    get_inline_keyboard(keyboard)
