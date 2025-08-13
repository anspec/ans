# Импорт необходимых библиотек:
# requests - для HTTP-запросов к Bitrix24 API
# telegram - для работы с Telegram Bot API
# telegram.ext - дополнительные инструменты для обработки сообщений
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Конфигурационные константы:
# BITRIX_WEBHOOK_URL - URL вебхука Bitrix24 с указанием домена и кода доступа
# TELEGRAM_TOKEN - токен вашего Telegram бота, полученный от @BotFather
BITRIX_WEBHOOK_URL = "https://b24-taph3l.bitrix24.ru/rest/1/uir30ogxnrtxvr4e/"
TELEGRAM_TOKEN = "7837541577:AAGlCQ5ni1zEC0JhF2Xlap51Y_2iRC67LuU"


# Функция создания лида в Bitrix24
# Принимает обязательные параметры name и phone, и опциональный comment
def create_bitrix_lead(name: str, phone: str, comment: str = "") -> dict:
    # Формируем полный URL для API-запроса добавления лида
    url = f"{BITRIX_WEBHOOK_URL}crm.lead.add.json"

    # Подготавливаем данные для отправки:
    # TITLE - заголовок лида с именем клиента
    # NAME - имя контакта
    # PHONE - список телефонов (в данном случае один)
    # COMMENTS - дополнительная информация с пометкой о источнике заявки
    data = {
        "fields": {
            "TITLE": f"Заявка от {name}",
            "NAME": name,
            "PHONE": [{"VALUE": phone}],
            "COMMENTS": f"Источник: Telegram Bot\n{comment}"
        }
    }

    # Отправляем POST-запрос к API Bitrix24 с данными в формате JSON
    response = requests.post(url, json=data)

    # Возвращаем ответ от сервера в формате JSON
    return response.json()


# Обработчик команды /start - приветственное сообщение
def start(update: Update, context: CallbackContext):
    # Отправляем пользователю форматированное сообщение с инструкциями:
    # - Используем HTML-разметку для форматирования
    # - Показываем пример ввода данных
    update.message.reply_text(
        "📝 Отправьте данные в формате:\n"
        "<b>Имя Телефон [Комментарий]</b>\n\n"
        "Пример: <code>Иван +79123456789 Хочу узнать про скидки</code>",
        parse_mode="HTML"
    )


# Обработчик обычных текстовых сообщений
def handle_message(update: Update, context: CallbackContext):
    try:
        # Разбиваем текст сообщения на части:
        # 1. name - первое слово
        # 2. phone - второе слово
        # 3. comment (опционально) - все остальное
        text = update.message.text.split(maxsplit=2)
        name, phone = text[0], text[1]
        comment = text[2] if len(text) > 2 else ""

        # Создаем лид в Bitrix24, передавая полученные данные
        result = create_bitrix_lead(name, phone, comment)

        # Проверяем результат:
        # Если есть поле 'result' - заявка создана успешно
        if 'result' in result:
            update.message.reply_text(f"✅ Заявка создана!\nID: {result['result']}")
        else:
            # Если ошибка - получаем описание или используем стандартное сообщение
            error = result.get('error_description', 'Неизвестная ошибка')
            update.message.reply_text(f"❌ Ошибка: {error}")

    except Exception as e:
        # В случае ошибки формата сообщения (например, недостаточно данных)
        # отправляем пользователю пример правильного ввода
        update.message.reply_text("⚠️ Ошибка формата. Пример:\n<code>Иван +79123456789</code>", parse_mode="HTML")


# Основная функция для настройки и запуска бота
def main():
    # Создаем экземпляр Updater для работы с Telegram API
    updater = Updater(TELEGRAM_TOKEN)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher

    # Регистрируем обработчики:
    # 1. Для команды /start
    # 2. Для обычных текстовых сообщений (исключая команды)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Выводим сообщение о запуске в консоль
    print("🤖 Бот запущен...")

    # Запускаем бота в режиме polling (постоянный опрос сервера Telegram)
    updater.start_polling()

    # Оставляем бота работать до принудительной остановки
    updater.idle()


# Стандартная проверка для запуска кода только при прямом вызове файла
if __name__ == '__main__':
    main()