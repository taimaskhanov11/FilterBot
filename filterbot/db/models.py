from typing import Literal

from aiogram.utils import markdown as mk
from loguru import logger
from telethon.tl import patched
from tortoise import fields, models

from filterbot.loader import _


class Account(models.Model):
    api_id = fields.BigIntField(unique=True)
    api_hash = fields.CharField(max_length=50)
    phone = fields.CharField(max_length=20)
    user: fields.OneToOneRelation["User"] = fields.OneToOneField("models.User", index=True)
    chats: fields.ReverseRelation["Chat"]


class User(models.Model):
    user_id = fields.BigIntField(unique=True)
    username = fields.CharField(max_length=255, null=True)
    registered_at = fields.DatetimeField(auto_now_add=True, description="Registration date")
    language = fields.CharField(max_length=5, description="Language code")
    account: fields.OneToOneNullableRelation["Account"]

    async def set_language(self, language: Literal["ru", "en"]):
        self.language = language
        await self.save(update_fields=["language"])

    @classmethod
    async def connect_account(cls, controller):
        user = await cls.get(user_id=controller.user_id)
        acc, is_create = await Account.get_or_create(
            user=user, defaults={**controller.dict(exclude={"chats", "user_id"})}
        )
        if not is_create:
            logger.info(f"{acc} уже существует")
        # await user.save()


class ChatStorage(models.Model):
    chat_id = fields.BigIntField(index=True)
    title = fields.CharField(max_length=100)
    chat: fields.OneToOneNullableRelation["Chat"]

    class Meta:
        table_description = "Chat storage for forwarding messages"

    def __str__(self):
        return f"{self.title}[ID {self.chat_id}]"


class Chat(models.Model):
    chat_id = fields.BigIntField(index=True)
    title = fields.CharField(max_length=100)
    message_filter: fields.OneToOneRelation["MessageFilter"] = fields.OneToOneField(
        "models.MessageFilter", on_delete=fields.CASCADE
    )
    account: fields.ForeignKeyRelation["Account"] = fields.ForeignKeyField("models.Account")
    chat_storage: fields.OneToOneRelation["ChatStorage"] = fields.OneToOneField("models.ChatStorage")

    def __str__(self):
        return f"{self.title}[ID {self.chat_id}]"

    def pretty(self) -> str:
        return "{chat}\n{chat_storage}\n\n{filters}\n{message_filter}\n".format(
            chat=mk.text(mk.hitalic(_("Чат: ")), mk.hpre(self)),
            chat_storage=mk.text(mk.hitalic(_("Хранилище: ")), mk.hpre(self.chat_storage)),
            filters=mk.hbold(_("Фильтры:")),
            message_filter=self.message_filter,
        )

    class Meta:
        table_description = "Filter for chats"

    async def message_check(self, message: patched.Message) -> bool:
        return await self.message_filter.message_check(message)

    @classmethod
    async def delete_chat(cls, pk) -> "Chat":
        chat = await Chat.get(pk=pk)
        await chat.delete()
        return chat


class MessageFilter(models.Model):
    # chat_filter: fields.OneToOneNullableRelation['ChatFilter'] = fields.OneToOneField("models.ChatFilter", null=True,
    #                                                                                   on_delete=fields.SET_NULL)
    user_filter: fields.OneToOneNullableRelation["UserFilter"] = fields.OneToOneField(
        "models.UserFilter", null=True, on_delete=fields.CASCADE
    )
    word_filter: fields.OneToOneNullableRelation["WordFilter"] = fields.OneToOneField(
        "models.WordFilter", null=True, on_delete=fields.CASCADE
    )

    def __str__(self):
        # return f"{self.user_filter}\n{self.word_filter}"
        return "\n\n".join(map(str, filter(bool, (self.user_filter, self.word_filter))))

    class Meta:
        table_description = "Filter collections"

    # {'filter_chat': {'chat_id': '-761192931'},
    #  'filter_type': 'complete',
    #  'filters': [{'data': 'saefsdaf', 'type': 'word'}],
    #  'storage_chat': {'chat_id': '735095975'}}
    #  type: Literal["word", "id", "username", "admin"]

    @classmethod
    async def create_filter(
            cls,
            filters: list[dict[str, str]],
    ) -> "MessageFilter":
        filters_data = {}
        for _filter in filters:
            if _filter["type"] == "word":
                word_filter = await WordFilter.create_filter(_filter["data"])
                filters_data.update(word_filter=word_filter)
            else:
                # user_filter = await UserFilter.create_filter(_filter["type"], _filter["data"])
                user_filter = await UserFilter.create(filter_type=_filter["type"], ids=_filter["data"])
                filters_data.update(user_filter=user_filter)

        message_filter = await cls.create(**filters_data)
        return message_filter

    async def message_check(self, message) -> bool:
        for _filter in filter(bool, (self.user_filter, self.word_filter)):  # self.chat_filter,
            if not await _filter.message_check(message):
                return False
        return True


class UserFilter(models.Model):
    ids = fields.JSONField()
    filter_type: Literal["admin", "user"] = fields.CharField(max_length=10)
    message_filter: fields.OneToOneNullableRelation["MessageFilter"]

    class Meta:
        table_description = "Filter for users"

    def __str__(self):
        ids = ""
        for key, val in self.ids.items():
            ids += f"{key}[{val}],"
        return f"{mk.hunderline(_('Тип фильтра: '))}{self.filter_type}\n{mk.hpre(ids)}"

    @classmethod
    async def create_filter(cls, filter_type, ids: dict[int, str]):
        pass

    async def message_check(self, message: patched.Message) -> bool:
        logger.trace(f"Проверка фильтра по пользователям")
        if message.from_id.user_id in self.ids.values():
            return True
        return False


class WordFilter(models.Model):
    words = fields.JSONField()
    filter: fields.OneToOneNullableRelation["MessageFilter"]

    class Meta:
        table_description = "Filter for words"

    def __str__(self):
        return f"{mk.hunderline(_('Тип фильтра: '))}{_('Ключевые слова')}\n{mk.hpre(self.words)}"
        # return _("Тип фильтра: Ключевые слова\nКлючевые слова: {words}").format(
        #     filter_type =
        #     words=self.words,
        # )

    @classmethod
    async def create_filter(cls, words: str):
        words = list(map(lambda x: x.strip(), words.split(",")))
        return await cls.create(words=words)

    async def message_check(self, message: patched.Message) -> bool:
        logger.trace(f"Проверка фильтра по ключевым словам {message.text}")
        if any(filter(lambda x: x in message.text, self.words)):
            return True
        return False


class DummyFilter(models.Model):
    @staticmethod
    async def message_check(message: patched.Message) -> bool:
        return False
