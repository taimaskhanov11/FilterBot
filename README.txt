Установка переводов

для linux
1. Вытаскиваем тексты из файлов, Добавляем текст в переведенные версии
# Обновить переводы
pybabel extract ./filterbot/apps/ -o ./filterbot/apps/bot/locales/filterbot.pot
pybabel update -d ./filterbot/apps/bot/locales -D filterbot -i ./filterbot/apps/bot/locales/filterbot.pot
# После перевода
pybabel compile -d ./filterbot/apps/bot/locales/ -D filterbot


Для windows
Обновляем переводы
1. Вытаскиваем тексты из файлов, Добавляем текст в переведенные версии
# Обновить переводы
pybabel extract .\filterbot\apps\ -o .\filterbot\apps\bot\locales\filterbot.pot
pybabel update -d .\filterbot\apps\bot\locales -D filterbot -i .\filterbot\apps\bot\locales\filterbot.pot
# После перевода
pybabel compile -d .\filterbot\apps\bot\locales\ -D filterbot

Запуск бота: poetry run python filterbot\main.py

