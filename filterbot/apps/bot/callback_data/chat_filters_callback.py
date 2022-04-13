from aiogram.utils.callback_data import CallbackData

chat_cb = CallbackData("chat", "chat_id", "action")
filter_cb = CallbackData("filter", "type")
user_cd = CallbackData("user", "id")