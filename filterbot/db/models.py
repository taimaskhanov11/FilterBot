from typing import Literal

from tortoise import fields, models


class Account(models.Model):
    api_id = fields.IntField(unique=True)
    api_hash = fields.CharField(max_length=50)
    phone = fields.CharField(max_length=20)
    user: fields.OneToOneRelation["User"] = fields.OneToOneField("models.User", index=True)
    chatstorages: fields.ReverseRelation["ChatStorage"]


class User(models.Model):
    user_id = fields.BigIntField(unique=True)
    username = fields.CharField(max_length=255, null=True)
    registered_at = fields.DatetimeField(auto_now_add=True, description="Registration date")
    language: Literal["ru", "en"] = fields.CharField(max_length=5, description="Language code")
    account: fields.OneToOneNullableRelation["Account"]

    async def set_language(self, language: Literal["ru", "en"]):
        self.language = language
        await self.save(update_fields=["language"])

    @classmethod
    async def connect_account(cls, **kwargs):
        account = await Account.create(**kwargs)
        user = await cls.get(user_id=kwargs.get("user_id"))
        user.account = account
        await user.save()


class ChatStorage(models.Model):
    chat_id = fields.BigIntField(index=True)
    title = fields.CharField(max_length=100)
    filter: fields.OneToOneRelation["Filter"] = fields.OneToOneField("models.Filter")
    account: fields.ForeignKeyRelation["Account"] = fields.ForeignKeyField("models.Account")

    class Meta:
        table_description = "Chat storage for forwarding messages"


class ChatFilter(models.Model):
    ids: list = fields.JSONField()
    chatstorage: fields.OneToOneRelation["ChatStorage"]

    class Meta:
        table_description = "Filter for chats"

    async def filter(self, message):
        pass


class UserFilter(models.Model):
    ids: list = fields.JSONField()
    chatstorage: fields.OneToOneRelation["ChatStorage"]

    class Meta:
        table_description = "Filter for users"

    async def filter(self, message):
        pass


class WordFilter(models.Model):
    words: list = fields.JSONField()
    chatstorage: fields.OneToOneRelation["ChatStorage"]

    class Meta:
        table_description = "Filter for words"

    async def filter(self, message):
        pass


class Filter(models.Model):
    chat_filter: fields.OneToOneNullableRelation[ChatFilter] = fields.OneToOneField("models.ChatFilter", null=True,
                                                                                    on_delete=fields.SET_NULL)
    user_filter: fields.OneToOneNullableRelation[UserFilter] = fields.OneToOneField("models.UserFilter", null=True,
                                                                                    on_delete=fields.SET_NULL)
    word_filter: fields.OneToOneNullableRelation[WordFilter] = fields.OneToOneField("models.WordFilter", null=True,
                                                                                    on_delete=fields.SET_NULL)

    class Meta:
        table_description = "Filter collections"

    async def filter(self, message):
        for _filter in filter(bool, (self.chat_filter,
                                     self.user_filter,
                                     self.word_filter)):
            if not _filter.filter(message):
                return True
