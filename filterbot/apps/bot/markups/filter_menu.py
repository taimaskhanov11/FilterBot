from filterbot.apps.bot.markups.utils import get_inline_keyboard


def filter_menu():
    keyboard = [
        (("Текущие чаты", "current_chats"),),
        (("Главное меню", "main_menu"),),
    ]
    return get_inline_keyboard(keyboard)


def current_chats(chats: list):
    keyboard = [
        ((chat,) for chat in chats)
    ]
    return get_inline_keyboard(keyboard)

if __name__ == '__main__':
    current_chats([1, 2, 3, 4, 5, 6, 7])