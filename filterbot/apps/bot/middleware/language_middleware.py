from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from filterbot.apps.bot.temp import users_locales
from filterbot.config.config import I18N_DOMAIN, LOCALES_DIR


class ACLMiddleware(I18nMiddleware):
    # Каждый раз, когда нужно узнать язык пользователя - выполняется эта функция
    async def get_user_locale(self, action, args):
        user = types.User.get_current()
        # Возвращаем язык из базы ИЛИ (если не найден) - язык из Телеграма
        # return await get_lang(user.id) or user.locale
        return users_locales.get(user.id) or user.locale


def setup_lang_middleware(dp):
    # Устанавливаем миддлварь
    i18n = ACLMiddleware(I18N_DOMAIN, LOCALES_DIR)
    dp.middleware.setup(i18n)
    return i18n
