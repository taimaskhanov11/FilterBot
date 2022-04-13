Установка переводов
pybabel extract .\filterbot\ -o .\filterbot\apps\bot\locales\filterbot.pot
pybabel init -i .\filterbot\apps\bot\locales\filterbot.pot -d .\filterbot\apps\bot\locales\ -D filterbot -l ru
pybabel init -i .\filterbot\apps\bot\locales\filterbot.pot -d .\filterbot\apps\bot\locales\ -D filterbot -l en
# Собрать переводы
pybabel compile -d .\filterbot\apps\bot\locales\ -D filterbot


Обновляем переводы
1. Вытаскиваем тексты из файлов, Добавляем текст в переведенные версии
# Обновить переводы
pybabel extract .\filterbot\apps\ -o .\filterbot\apps\bot\locales\filterbot.pot
pybabel update -d .\filterbot\apps\bot\locales -D filterbot -i .\filterbot\apps\bot\locales\filterbot.pot
# После перевода
pybabel compile -d .\filterbot\apps\bot\locales\ -D filterbot