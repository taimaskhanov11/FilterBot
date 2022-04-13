import collections

from filterbot.db.models import User
from filterbot.loader import _


class StatisticStorage:
    storage = collections.defaultdict(int)

    def get(self, key):
        return self.storage.get(key)

    def incr(self, key):
        self.storage[key] += 1

    def getset(self, key, value):
        old_val = self.storage.get(key)
        self.storage[key] = value
        return old_val

    async def get_by_user_stats(self, user_id):
        user = await User.get(user_id=user_id).prefetch_related(
            "account__chats__message_filter__user_filters",
            "account__chats__message_filter__word_filter",
            "account__chats__chat_storage",
        )
        chat_storages = set([chat.chat_storage for chat in user.account.chats])
        answer = _("Количество фильтрованных чатов: {}\n"
                   "Количество хранилищ: {}\n"
                   "Количество отфильтрованных сообщений {}\n"
                   "Всего полученных сообщений {}").format(
            len(user.account.chats),
            len(chat_storages),
            self.get(f"{user.user_id}_filter_message"),
            self.get(f"{user.user_id}_all_message"),
        )
        return answer

    def get_by_admin_stats(self):
        pass


statistic_storage = StatisticStorage()
