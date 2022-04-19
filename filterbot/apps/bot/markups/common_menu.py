from filterbot.apps.bot import temp
from filterbot.apps.bot.markups.utils import get_inline_keyboard
from filterbot.loader import _


def start_menu(user_id):
    if controller := temp.controllers.get(user_id):
        controller_status = ((_("❌ Отвязать аккаунт"), "unlink_account"),)
        client_status = (
            ((_("⏸ Приостановить бота"), "pause_client"),)
            if controller.client.is_connected()
            else ((_("🔄 Возобновить бота"), "run_client"),)
        )
    else:
        controller_status = ((_("➕ Привязать аккаунт"), "link_account"),)
        client_status = ()
    keyboard = [
        ((_("👤 Мой профиль"), "profile"),),
        controller_status,
        client_status,
        ((_("⚙️ Настройки фильтров"), "chat_filters"),),
        ((_("📈 Статистика"), "statistic"),),
        ((_("🔖 Ввести промокод"), "input_promocode"),),
        ((_("🇷🇺  Язык(🇺🇸 language)"), "language"), (_("💬 Поддержка"), "support")),
    ]
    return get_inline_keyboard(keyboard)


def language(lang):
    keyboard = [
        (("🇷🇺 Русский", "ru"),) if lang == "en" else (("🇺🇸 English", "en"),),
        ((_("Главное меню"), "start"),),
    ]
    return get_inline_keyboard(keyboard)


def menu_button():
    keyboard = [
        ((_("Главное меню"), "start"),),
    ]
    return get_inline_keyboard(keyboard)


def choice():
    keyboard = [
        ((_("Да"), "yes"),),
        ((_("Нет"), "no"),),
    ]
    return get_inline_keyboard(keyboard)
