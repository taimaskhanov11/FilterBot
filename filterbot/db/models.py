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
    promocodes: fields.ReverseRelation["PromoCode"]

    def __str__(self):
        return f"{self.username}[{self.user_id}]"

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


class PromoCode(models.Model):
    title = fields.CharField(max_length=255)
    limit = fields.IntField()
    code = fields.CharField(max_length=255, index=True)
    user = fields.ForeignKeyField("models.User", null=True)

    def __str__(self):
        return (
            f"Название: {self.title}\n"
            f"Лимит: {self.limit}\n"
            f"Промокод: {self.code}\n"
            f"Привязка: {self.user or 'Не привязан'}\n"
        )


class ChatStorage(models.Model):
    chat_id = fields.BigIntField(index=True)
    title = fields.CharField(max_length=100)
    chats: fields.ReverseRelation["Chat"]

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
    chat_storage: fields.ForeignKeyRelation["ChatStorage"] = fields.ForeignKeyField("models.ChatStorage")

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
        chat = await Chat.get(pk=pk).prefetch_related(
            "message_filter__user_filters",
            "message_filter__word_filter", )
        await chat.message_filter.delete_filter()
        await chat.delete()
        return chat


class MessageFilter(models.Model):
    # chat_filter: fields.OneToOneNullableRelation['ChatFilter'] = fields.OneToOneField("models.ChatFilter", null=True,
    #                                                                                   on_delete=fields.SET_NULL)
    user_filters: fields.ReverseRelation["UserFilter"]
    word_filter: fields.OneToOneNullableRelation["WordFilter"] = fields.OneToOneField(
        "models.WordFilter", null=True, on_delete=fields.CASCADE
    )

    def __str__(self):
        # return f"{self.user_filter}\n{self.word_filter}"
        return "\n\n".join(map(str, filter(bool, (*self.user_filters, self.word_filter))))

    class Meta:
        table_description = "Filter collections"

    # {'filter_chat': {'chat_id': '-761192931'},
    #  'filter_type': 'complete',
    #  'filters': [{'data': 'saefsdaf', 'type': 'word'}],
    #  'storage_chat': {'chat_id': '735095975'}}
    #  type: Literal["word", "id", "username", "admin"]

    async def delete_filter(self):
        if self.user_filters:
            for _filter in self.user_filters:
                await _filter.delete()
        if self.word_filter:
            await self.word_filter.delete()
        await self.delete()

    @classmethod
    async def create_filter(
            cls,
            filters: dict[dict[str, str]],
    ) -> "MessageFilter":
        message_filter = await cls.create()
        for _type, _filter in filters.items():
            data = _filter["data"]
            if _type == "word":
                word_filter = await WordFilter.create(words=data)
                message_filter.word_filter = word_filter
            else:
                # user_filter = await UserFilter.create_filter(_filter["type"], _filter["data"])
                await UserFilter.create(
                    message_filter=message_filter,
                    filter_type=_type,
                    ids=data)
                # filters_data.update(user_filter=user_filter)

        await message_filter.save()
        return message_filter

    async def message_check(self, message) -> bool:
        if self.user_filters:
            if not any((_filter.message_check(message) for _filter in self.user_filters)):
                return False

        if self.word_filter:
            if not self.word_filter.message_check(message):
                return False
        return True

        # for _filter in filter(bool, (*self.user_filters, self.word_filter)):  # self.chat_filter,
        #     if not await _filter.message_check(message):
        #         return False
        # return True


class UserFilter(models.Model):
    ids = fields.JSONField()
    filter_type: Literal["admin", "user"] = fields.CharField(max_length=10)
    message_filter: fields.ForeignKeyRelation["MessageFilter"] = fields.ForeignKeyField("models.MessageFilter",
                                                                                        "user_filters",
                                                                                        on_delete=fields.CASCADE)

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

    def message_check(self, message: patched.Message) -> bool:
        _id = message.from_id.user_id
        if _id in self.ids.values():
            logger.success(f"Проверка фильтра по {self.filter_type}|{_id} прошел")
            return True
        logger.trace(f"Проверка фильтра по {self.filter_type}|{_id} не прошел")
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

    def message_check(self, message: patched.Message) -> bool:
        text = message.text.lower()
        if any(filter(lambda x: x in text, self.words)):
            logger.success(f"Проверка фильтра по ключевым словам прошел")
            return True
        logger.trace(f"Проверка фильтра по ключевым словам не прошел")
        return False


class DummyFilter(models.Model):
    @staticmethod
    async def message_check(message: patched.Message) -> bool:
        return False
