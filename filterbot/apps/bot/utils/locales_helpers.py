from filterbot.apps.bot.temp import users_locales
from filterbot.db.models import User


async def update_users_locales():
    for u in await User.all():
        users_locales[u.user_id] = u.language
