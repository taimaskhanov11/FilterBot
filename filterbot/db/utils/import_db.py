import asyncio
import json

from filterbot.config.config import config
from filterbot.db.db_main import init_tortoise
from filterbot.db.models import User


def write_bc(data):
    with open(f"bc.json", "w", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=True, default=str, indent=4, ensure_ascii=False)


async def import_data():
    await init_tortoise(password="123123", host="157.230.122.80")
    users = await DbUser.filter(subscription__is_subscribe=True).select_related("account")
    for u in users:
        print(u.account)


async def text_data():
    await init_tortoise(**config.db.dict())
    user = await User.first()
    print(await user.promocode)
    print(await user.promocode)


if __name__ == "__main__":
    asyncio.run(text_data())
