from filterbot.apps.bot.callback_data.chat_filters_callback import promocode_cd
from filterbot.apps.bot.markups.utils import get_inline_keyboard
from filterbot.db.models import PromoCode


def create_promocode_name():
    keyword = [
        # (("Без ограничений", "nolimit"),),
        # (("Ограничение на количество чатов", "chat_limit"),),
        (("Ограничение на количество чатов по админам", "admin_limit"),),
    ]

    return get_inline_keyboard(keyword)


def current_promocodes(prcodes: list[PromoCode]):
    keyboard = [
        ((f"[#{num}] {prcode.title}", promocode_cd.new(id=prcode.pk, action="get")) for num, prcode in
         enumerate(prcodes))
    ]
    return get_inline_keyboard(keyboard)
