#Документация по pandas	https://pandas.pydata.org/docs/user_guide/index.html

# Импорт необходимых библиотек
import requests  # Для выполнения HTTP-запросов к API
import logging  # Для настройки системы логирования
import csv  # Для работы с CSV-файлами (чтение/запись)
from datetime import datetime  # Для работы с датой и временем
import pandas as pd  # Для анализа и обработки данных
import matplotlib.pyplot as plt  # Для создания графиков и визуализации данных
from io import BytesIO  # Для работы с бинарными потоками в памяти
import os  # Для взаимодействия с файловой системой
import time #для замера времени
from dotenv import load_dotenv #config.env

# Импорт компонентов Telegram API
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, \
    ConversationHandler

# Настройка системы логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат записи логов
    level=logging.INFO  # Уровень детализации логов
)
logger = logging.getLogger(__name__)  # Создание логгера для текущего модуля

load_dotenv("config.env")

# Константы для работы бота
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # API-ключ OpenWeatherMap
my_telegram_id = os.getenv("MY_TELEGRAM_ID")
CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"  # URL API Центробанка для курсов валют
WEATHER_LOG_PATH = "weather_logs.csv"  # Путь к файлу логов погодных запросов
ADMIN_IDS = [my_telegram_id]  # Список ID администраторов бота
print(f"токен={TOKEN} OPENWEATHER_API_KEY = {OPENWEATHER_API_KEY} my_telegram_id ={my_telegram_id}")

# Определение состояний для ConversationHandler
WAIT_CITY, SHOW_INFO = range(2)  # Состояния: ожидание города и показ информации


# Инициализация файла логов
if not os.path.exists(WEATHER_LOG_PATH):
    # Создание нового файла с заголовками
    with open(WEATHER_LOG_PATH, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'user_id', 'username', 'city', 'status'])
else:
    # Проверка существующего файла на наличие заголовков
    with open(WEATHER_LOG_PATH, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        # Если заголовки отсутствуют - добавляем их
        if not first_line.startswith('timestamp') or 'user_id' not in first_line:
            with open(WEATHER_LOG_PATH, 'r+', encoding='utf-8') as f:
                content = f.read()
                f.seek(0, 0)
                f.write('timestamp,user_id,username,city,status\n' + content)

def log_weather_request(user_id: int, username: str, city: str, status: str):
    """Записывает информацию о запросе погоды в CSV-лог"""
    try:
        # Открытие файла в режиме добавления
        with open(WEATHER_LOG_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Формирование строки лога
            writer.writerow([
                datetime.now().isoformat(),  # Текущая дата и время
                user_id,  # ID пользователя
                username,  # Имя пользователя
                city,  # Запрошенный город
                status  # Статус запроса: success/error/city_not_found
            ])
    except Exception as e:
        # Обработка ошибок записи в лог
        logger.error(f"Ошибка записи в лог: {e}")


def create_reply_keyboard():
    """Создает клавиатуру с основными командами"""
    return ReplyKeyboardMarkup(
        [
            ["🌤️ Узнать погоду", "Каталог"],  # Первый ряд кнопок
            ['📞 Контакты', "Мой профиль"],  # Второй ряд
            # Специальные кнопки с запросом данных
            [KeyboardButton("Отправить контакт", request_contact=True),
             KeyboardButton("Отправить геолокацию", request_location=True)]
        ],
        resize_keyboard=True,  # Автоматическое изменение размера
        input_field_placeholder="Выберите действие"  # Подсказка в поле ввода
    )


def create_profile_keyboard():
    """Создает клавиатуру для раздела профиля"""
    return ReplyKeyboardMarkup(
        [["✏Изменить имя", "Дата рождения"], ["Главное меню"]],
        resize_keyboard=True,  # Автоматическое изменение размера
        one_time_keyboard=True  # Скрытие после использования
    )


def create_main_menu_keyboard():
    """Создает инлайн-клавиатуру главного меню"""
    keyboard = [
        [
            # Кнопки первого ряда
            InlineKeyboardButton("🌤️ Посмотреть погоду", callback_data='weather'),
            InlineKeyboardButton("🖥️ Открыть сайт ZeroCoder", url="https://zerocoder.ru"),
        ],
        [
            # Кнопки второго ряда
            InlineKeyboardButton("💶 Курсы валют", callback_data='currency'),
            InlineKeyboardButton("💰 Поддержать", url="https://donate.com")
        ],
        [InlineKeyboardButton("❌ Закрыть", callback_data='close')]  # Кнопка закрытия
    ]
    return InlineKeyboardMarkup(keyboard)  # Возврат разметки клавиатуры

def process_find_cat_keyword(update: Update, context: CallbackContext):
    # Логика поиска категорий
    category_id = 1  # Пример ID категории
    parent_id = 0  # Пример родительского ID
    update.message.reply_text(
        f"Найдены категории по ключевому слову: {keyword}.",
        reply_markup=generate_find_keyboard(category_id, parent_id)
        )

    return  FIND_CAT_ACTIONS

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user = update.effective_user  # Получение информации о пользователе
    # Приветственное сообщение с основной клавиатурой
    update.message.reply_text(
        f"Привет, {user.first_name}! Я твой бот помощник. Что ты хочешь сделать?",
        reply_markup=create_reply_keyboard()
    )
    # Сообщение с инлайн-меню
    update.message.reply_text(
        "Используйте кнопки ниже или меню: ",
        reply_markup=create_main_menu_keyboard()
    )


def button_click(update: Update, context: CallbackContext) -> int:
    """Обработчик нажатий инлайн-кнопок"""
    query = update.callback_query  # Данные callback-запроса
    query.answer()  # Подтверждение получения callback

    # Обработка кнопки погоды
    if query.data == "weather":
        query.message.reply_text(
            "Введите название города:",
            reply_markup=ReplyKeyboardRemove()  # Удаление текущей клавиатуры
        )
        return WAIT_CITY  # Переход в состояние ожидания города

    # Обработка кнопки курсов валют
    elif query.data == 'currency':
        show_currency_rates(query)  # Вызов функции показа курсов
        return SHOW_INFO  # Переход в состояние показа информации

    # Обработка кнопки возврата в меню
    elif query.data == 'back_to_menu':
        query.edit_message_text(
            text="Главное меню: ",
            reply_markup=create_main_menu_keyboard()  # Обновление меню
        )
        return ConversationHandler.END  # Завершение диалога

    # Обработка кнопки закрытия
    elif query.data == 'close':
        query.delete_message()  # Удаление сообщения с меню
        return ConversationHandler.END  # Завершение диалога

    return ConversationHandler.END  # Запасной вариант завершения


def get_weather(update: Update, context: CallbackContext) -> int:
    """Получает и отображает погоду для указанного города"""
    city = update.message.text  # Извлечение города из сообщения
    user = update.effective_user  # Информация о пользователе
    user_id = user.id if user else 0  # ID пользователя (0 если не определен)
    username = user.username or user.first_name or "Unknown"  # Имя пользователя

    # Формирование URL для запроса погоды
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"

    try:
        response = requests.get(url)  # Выполнение HTTP-запроса
        data = response.json()  # Парсинг JSON-ответа

        # Обработка успешного ответа
        if response.status_code == 200:
            # Логирование успешного запроса
            log_weather_request(user_id, username, city, 'success')

            # Формирование строки с информацией о погоде
            weather_info = (
                f"Погода в {city}:\n"
                f"Температура: {data['main']['temp']} °C\n"
                f"Состояние: {data['weather'][0]['description']}\n"
                f"Влажность: {data['main']['humidity']} %\n"
                f"Ветер: {data['wind']['speed']} м/с"
            )
            # Создание кнопки возврата
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]]
            # Отправка информации о погоде
            update.message.reply_text(weather_info, reply_markup=InlineKeyboardMarkup(keyboard))
            return SHOW_INFO  # Переход в состояние показа информации

        # Обработка ошибки "город не найден"
        log_weather_request(user_id, username, city, 'city_not_found')
        update.message.reply_text("Город не найден, попробуйте еще раз:")
        return WAIT_CITY  # Повторный запрос города

    except Exception as e:
        # Обработка системных ошибок
        log_weather_request(user_id, username, city, 'error')
        logger.error(f"Ошибка при получении погоды: {e}")
        update.message.reply_text("Произошла ошибка. Попробуйте позже")
        return ConversationHandler.END  # Завершение диалога


def show_currency_rates(query):
    """Отображает текущие курсы валют"""
    try:
        response = requests.get(CBR_API_URL)  # Запрос к API ЦБ
        data = response.json()  # Парсинг JSON-ответа
        rates = data['Valute']  # Извлечение данных о валютах

        # Формирование текста с курсами
        text = (
            f"Курсы ЦБ РФ:\n"
            f"Доллар USA: {rates['USD']['Value']:.2f} ₽\n"
            f"Евро: {rates['EUR']['Value']:.2f} ₽\n"
            f"Юань: {rates['CNY']['Value']:.2f} ₽\n"
        )
        # Кнопка возврата в меню
        keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")]]
        # Обновление сообщения с курсами
        query.edit_message_text(
            text=text, reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        # Обработка ошибок получения курсов
        logger.error(f"Ошибка при получении курса валют: {e}")
        query.edit_message_text("Не удалось получить курсы валют")


def cancel(update: Update, context: CallbackContext) -> int:
    """Отмена текущего действия"""
    update.message.reply_text("Действие отменено", reply_markup=create_reply_keyboard())
    return ConversationHandler.END  # Завершение диалога


def weather_stats(update: Update, context: CallbackContext):
    """Показывает статистику запросов погоды (только для администраторов)"""
    # Проверка прав администратора
    print(f" {update.effective_user.id}  -  {ADMIN_IDS}")
    if f"{update.effective_user.id}" not in ADMIN_IDS:
        update.message.reply_text("⚠️ Эта команда доступна только администраторам")
        return

    try:
        # Проверка существования и доступности файла логов
        if not os.path.exists(WEATHER_LOG_PATH) or os.path.getsize(WEATHER_LOG_PATH) == 0:
            update.message.reply_text("📊 Статистика пока недоступна. Запросы еще не делались.")
            return

        # Чтение и обработка файла логов
        logs = []
        with open(WEATHER_LOG_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Пропуск заголовка

            for row in reader:
                if not row:  # Пропуск пустых строк
                    continue
                # Нормализация строк (добавление недостающих значений)
                if len(row) < 5:
                    row += [''] * (5 - len(row))
                logs.append(row[:5])  # Сохранение только первых 5 значений

        # Создание DataFrame из логов
        df = pd.DataFrame(logs, columns=['timestamp', 'user_id', 'username', 'city', 'status'])

        # Проверка на наличие данных
        if df.empty:
            update.message.reply_text("📊 Статистика пока недоступна. Нет данных для анализа.")
            return

        # Преобразование user_id в числовой формат
        df['user_id'] = pd.to_numeric(df['user_id'], errors='coerce')

        # Расчет основных метрик
        total_requests = len(df)  # Общее количество запросов
        status_counts = df['status'].value_counts()  # Распределение по статусам
        success_requests = status_counts.get('success', 0)  # Успешные запросы
        error_requests = status_counts.get('error', 0)  # Ошибки сервера
        city_not_found = status_counts.get('city_not_found', 0)  # Города не найдены
        unique_users = df['user_id'].nunique()  # Уникальные пользователи

        # Топ-5 городов (только успешные запросы)
        popular_cities = df[df['status'] == 'success']['city'].value_counts().head(5)

        # Формирование текстового отчета
        report = (
            f"📊 Статистика запросов погоды:\n"
            f"• Всего запросов: {total_requests}\n"
            f"• Успешных запросов: {success_requests}\n"
            f"• Ошибок 'город не найден': {city_not_found}\n"
            f"• Системных ошибок: {error_requests}\n"
            f"• Уникальных пользователей: {unique_users}\n\n"
            f"🏙️ Топ-5 запрашиваемых городов:\n"
        )

        # Добавление информации о городах
        if not popular_cities.empty:
            for city, count in popular_cities.items():
                report += f"  - {city}: {count}\n"
        else:
            report += "  Нет данных о городах\n"

        # Анализ ежедневной активности
        try:
            # Преобразование времени и фильтрация
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])

            if not df.empty:
                # Группировка по дате
                df['date'] = df['timestamp'].dt.date
                daily_activity = df.groupby('date').size().reset_index(name='requests')
                # Сортировка и выбор последних 7 дней
                daily_activity = daily_activity.sort_values('date', ascending=False).head(7)

                # Добавление данных в отчет
                if not daily_activity.empty:
                    report += "\n📅 Активность за последние 7 дней:\n"
                    for _, row in daily_activity.iterrows():
                        report += f"  {row['date']}: {row['requests']} запросов\n"
                else:
                    report += "\n📅 Нет данных о ежедневной активности\n"
            else:
                report += "\n📅 Нет данных о ежедневной активности\n"
        except Exception as e:
            # Обработка ошибок анализа времени
            logger.error(f"Ошибка при расчете ежедневной активности: {e}")
            report += "\n📅 Не удалось рассчитать ежедневную активность\n"

        # Отправка текстового отчета
        update.message.reply_text(report)

        # Создание и отправка графика (если есть данные)
        if not popular_cities.empty:
            plt.figure(figsize=(10, 6))  # Размер графика
            # Построение столбчатой диаграммы
            popular_cities.plot(kind='bar', color='skyblue')
            plt.title('Топ запрашиваемых городов')  # Заголовок
            plt.ylabel('Количество запросов')  # Подпись оси Y
            plt.xticks(rotation=45, ha='right')  # Наклон подписей
            plt.tight_layout()  # Оптимизация расположения

            # Сохранение в бинарный буфер
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=80)
            buf.seek(0)

            # Отправка изображения
            update.message.reply_photo(photo=buf)
            buf.close()  # Закрытие буфера
            plt.close()  # Закрытие графика

    except Exception as e:
        # Обработка общих ошибок статистики
        logger.error(f"Ошибка генерации статистики: {e}", exc_info=True)
        update.message.reply_text("⚠️ Произошла ошибка при формировании статистики")


def main():
    """Основная функция инициализации и запуска бота"""
    # TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    # OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # API-ключ OpenWeatherMap
    # my_telegram_id = os.getenv("MY_TELEGRAM_ID")
    #
    # print(f"токен={TOKEN} OPENWEATHER_API_KEY = {OPENWEATHER_API_KEY} my_telegram_id ={my_telegram_id}")
    updater = Updater(TOKEN)  # Создание объекта Updater
    dispatcher = updater.dispatcher  # Получение диспетчера

    # Настройка обработчика диалогов для погоды
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_click, pattern='^weather$')],  # Точка входа
        states={
            WAIT_CITY: [MessageHandler(Filters.text & ~Filters.command, get_weather)],  # Ожидание города
            SHOW_INFO: [CallbackQueryHandler(button_click)]  # Показать информацию
        },
        fallbacks=[CommandHandler('cancel', cancel)],  # Обработчик отмены
        allow_reentry=True  # Разрешение повторного входа
    )

    # Регистрируем обработчики
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('find_cat', find_cat))
    updater.dispatcher.add_handler(CallbackQueryHandler(button_handler))
    updater.dispatcher.add_handler(conv_handler)  # Добавляем ConversationHandler, если используется


    # # Регистрация обработчиков
    # dispatcher.add_handler(conv_handler)  # Диалоги погоды
    # dispatcher.add_handler(CommandHandler("start", start))  # Команда /start
    # # Обработчики инлайн-кнопок
    # dispatcher.add_handler(CallbackQueryHandler(button_click, pattern='^(currency|back_to_menu|close)$'))
    # # Обработчик статистики
    # dispatcher.add_handler(CommandHandler("weather_stats", weather_stats))

    updater.start_polling()  # Запуск бота в режиме опроса
    logger.info("Бот запущен и готов к работе")  # Запись в лог
    updater.idle()  # Бесконечный цикл до остановки


if __name__ == '__main__':
    main()  # Запуск приложения