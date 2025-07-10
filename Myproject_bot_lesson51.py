#Telegram-бот для хранения и выдачи пользовательских рекомендаций
# Цель: Создать чат-бота для Telegram, позволяющего пользователям сохранять рекомендованные им фильмы,
# сериалы, книги, продукты и прочее) и в любой момент (например, когда пользователь захотел посмотреть
# фильм) получать одну или список рекомендаций по нужной категории.
# Функционал:
# - Приветственное сообщение по команде /start с информацией о возможностях бота и меню.
# - Добавление новых рекомендаций по категориям (фильмы, сериалы, книги, другое):
# - /add - команда для добавления рекомендации.
# - Далее предоставляется выбор категории: фильмы, книги, сериала, другое.
# - После выбора категории бот последовательно просит пользователя ввести название рекомендации (например, “Титаник”/ “Бегущая с Волками”) и комментарий к этой рекомендации - это может быть любой сопроводительный текст: ”посоветовала Маша/ из блога Васи/ смотреть, если грустно/ автор - Ричард Бах/ про мотивацию и т.п”.
# - Информация сохраняется в базу данных со столбцами (id записи, id пользователя, категория, название, комментарий).
# - Поиск и просмотр рекомендаций:
# - /find - команда для начала поиска. Поиск ведется только по рекомендациям, которые добавлены этим же пользователем (по id пользователя).
# - Далее предоставляется выбор категории: фильмы, книги, сериала, другое.
# - Далее выбор из 2-х опций:
# 1. /anything - Запрос на выдачу рандомной рекомендации в выбранной категории. Формат выдачи: название и комментарий.
# 2. /specific - Бот запрашивает пользователя ввести ключевое слово, поиск ведется по двум столбцам: название и комментарий.
# - Управление рекомендациями:
# - Возможность редактировать и удалять рекомендации. (команды в меню: /edit - редактировать, /del - удалить.)
from array import ArrayType

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
from fontTools.misc.bezierTools import namedtuple

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
#OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # API-ключ OpenWeatherMap
#my_telegram_id = os.getenv("MY_TELEGRAM_ID")
#CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"  # URL API Центробанка для курсов валют
COMMENT_LOG_PATH = "comments_log.csv"  # Путь к файлу логов рекомендаций
ADMIN_IDS = [my_telegram_id]  # Список ID администраторов бота
#print(f"токен={TOKEN} OPENWEATHER_API_KEY = {OPENWEATHER_API_KEY} my_telegram_id ={my_telegram_id}")

# Определение состояний для ConversationHandler
WAIT_CATEGORY, WAIT_KEYWORD, SHOW_INFO = range(3)  # Состояния: ожидание категории, ключевой фразы и показ информации

current_category_id = 0
DB_path = "comments.db"
conn = sqlite3.connect("comments.db")
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dt_first DATATIME NOT NULL,     # дата и время когда зарегистрировался
    comment TEXT 
)
''')
cursor.execute('''CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER 
    name TEXT NOT NULL,
    comment TEXT NOT NULL, 
    dt DATATIME NOT NULL,     # дата и время когда изменил запись
)
''')

conn.commit()

class Users():
    def __init__(self):
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dt_first DATATIME NOT NULL,     # дата и время когда зарегистрировался
            comment TEXT 
        )
        ''')

    def get_user_id(self, name:str) -> int:
        try:
            cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return row.id
            else:
                return 0

        except e:
            print(f"Ощибка в базе данных {e}")
            return 0

    def append_user(self, name:str, comment:str='') -> int:
        try:
            id = self.get_user_id(name)

            if id != 0:
                return id
            else:
                cursor.execute("INSERT INTO users (name, comment, dt_first) VALUES (?, ?, ?)",
                               (name, comment, datetime.now().isoformat(),))
                id = cursor.lastrowid
                return id

        except e:
            print(f"Ощибка в базе данных {e}")
            return 0

class Categories():
    def __init__(self):
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            active BOOLEAN, 
            parent_id INTEGER 
        )
        ''')
    def is_exist_category(self, category_id:int) -> bool:
        try:
            cursor.execute("SELECT * FROM categories WHERE active=True and id = ?", (category_id,))
            row = cursor.fetchone()
            if row:
                return True
            else:
                return False
        except e:
            print(f"Ощибка в базе данных {e}")
            return False

    def add_category(self, name:str, parent_id:int) -> int:
        #Обеспечиваем иерархию категорий
        try:
            if parent_id == 0:
                cursor.execute("INSERT INTO categories (name, active, parent_id) VALUES (?, ?, ?)",
                               (name, True, parent_id))
            elif self.is_exist_category( parent_id ):
                cursor.execute("INSERT INTO categories (name, active, parent_id) VALUES (?, ?, ?)",
                                   (name, True, parent_id))

            else:
                cursor.execute("INSERT INTO categories (name, active, parent_id) VALUES (?, ?, ?)",
                                   (name, True, 0))
                print(f"Указан некорректный id = {parent_id} родителя при создании категории {name}. Установлен без иерархии")

            id = cursor.lastrowid

            conn.commit()
        except e:
            print(f"Ощибка создания категории {name} в базе данных {e}")
            id = 0

        return id

    def change_parent_for_category(self, category_id: int, parent_id: int):
        # Обеспечиваем иерархию категорий
        try:
            cursor.execute("SELECT * FROM categories WHERE id = ?", (parent_id,))
            row = cursor.fetchone()
            if not row:
                print(f"Указан некорректный id = {parent_id} родителя при для изменения иерархии категории с id={category_id}")
            else:
                cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
                row = cursor.fetchone()
                if not row:
                    print(f"Указан некорректный id = {category_id} категории для изменения")
                else:
                    cursor.execute("UPDATE categories SET parent_id= ? WHERE id = ?", (parent_id,category_id,))
                    print("Успех!")
            conn.commit()
        except e:
            print(f"Ощибка в базе данных {e}")

    def change_name_for_category(self, category_id: int, name: str):
        # Обеспечиваем иерархию категорий
        try:
            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            row = cursor.fetchone()
            if not row:
                print(f"Указан некорректный id = {category_id} категории для изменения")
            else:
                cursor.execute("UPDATE categories SET name= ? WHERE id = ?", (name,category_id,))
                print("Успех!")
                conn.commit()
        except e:
            print(f"Ощибка создания категории {name} в базе данных {e}")

    def change_active_category(self, category_id:int) :
        cursor.execute("SELECT active FROM categories WHERE id = ?", (category_id,))
        row = cursor.fetchone()
        if row:
            if row.active:
                cursor.execute("UPDATE categories SET active=False WHERE id = ?", (category_id,))
            else:
                cursor.execute("UPDATE categories SET active=True WHERE id = ?", (category_id,))

            conn.commit()
        else:
            print(f"Для выбора категрии указан некоррктный id {category_id,}")

    def list_categories(self, parent_id:int) -> ArrayType:
        cursor.execute("SELECT * FROM categories WHERE active=True and parent_id = ? ORDER BY name ASC", (parent_id,))
        rows = cursor.fetchall()

        arr = []
        for row in rows:
            arr.append({'id':row.id,'name':row.name})

        return arr

    # выбираются категории, начиная с заданной и ниже по иерархии
    def tree_categories(self, category_id:int) -> ArrayType:

        arr = []
        id = category_id
        arr.append(id)
        arr1 = arr

        flag = True
        while flag:
            cursor.execute("SELECT * FROM categories WHERE active=True and parent_id IN ?", (arr1,))
            rows = cursor.fetchall()
            arr1 = []
            for row in rows:
                arr.append(row.id)
                arr1.append(row.id)

            flag = (arr1.count() == 0)

        return arr

class Comments():
    def __init__(self):
        cursor.execute('''CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER 
            category_id INTEGER 
            name TEXT NOT NULL,
            comment TEXT NOT NULL, 
            dt DATATIME NOT NULL,     # дата и время когда изменил запись
        )
        ''')
        self.stru_find = {'user_id':0,'category_id':0,'random':False, keyword:str}

    def add_comment(self,user_id:int,category_id:int,name:str,comment:str):
        cursor.execute("INSERT INTO comments (user_id,category_id,name,comment,dt) VALUES (?, ?, ?, ?, ?)",
                       (user_id, category_id, name, comment, datetime.now().isoformat(), ))

    def find_your_comment(self,keyword:str):
        pass


    def find_all_comment(self, keyword: str):
        pass


#Инициализация файла логов
if not os.path.exists(COMMENT_LOG_PATH):
    # Создание нового файла с заголовками
    with open(COMMENT_LOG_PATH, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'user_id', 'username', 'category_id', 'keyword', 'status'])
else:
    # Проверка существующего файла на наличие заголовков
    with open(COMMENT_LOG_PATH, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        # Если заголовки отсутствуют - добавляем их
        if not first_line.startswith('timestamp') or 'user_id' not in first_line:
            with open(WEATHER_LOG_PATH, 'r+', encoding='utf-8') as f:
                content = f.read()
                f.seek(0, 0)
                f.write('timestamp,user_id,username,category_id,keyword,status\n' + content)


def log_comment_request(user_id: int, username: str, category_id: int, keyword: str, status: str):
    """Записывает информацию о запросе рекомендаций в CSV-лог"""
    try:
        # Открытие файла в режиме добавления
        with open(COMMENT_LOG_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # Формирование строки лога
            writer.writerow([
                datetime.now().isoformat(),  # Текущая дата и время
                user_id,  # ID пользователя
                username,  # Имя пользователя
                category_id,  # Запрошенная категория
                keyword,  # Запрошенное слово/фраза
                status  # Статус запроса: success/not_found
            ])
    except Exception as e:
        # Обработка ошибок записи в лог
        logger.error(f"Ошибка записи в лог: {e}")


# def create_reply_keyboard():
#     """Создает клавиатуру с основными командами"""
#     return ReplyKeyboardMarkup(
#         [
#             ["🌤️ Узнать погоду", "Каталог"],  # Первый ряд кнопок
#             ['📞 Контакты', "Мой профиль"],  # Второй ряд
#             # Специальные кнопки с запросом данных
#             [KeyboardButton("Отправить контакт", request_contact=True),
#              KeyboardButton("Отправить геолокацию", request_location=True)]
#         ],
#         resize_keyboard=True,  # Автоматическое изменение размера
#         input_field_placeholder="Выберите действие"  # Подсказка в поле ввода
#     )


def create_profile_keyboard():
    """Создает клавиатуру для раздела профиля"""
    return ReplyKeyboardMarkup(
        [["✏Изменить имя", "Дата рождения"], ["Главное меню"]],
        resize_keyboard=True,  # Автоматическое изменение размера
        one_time_keyboard=True  # Скрытие после использования
    )


def create_main_menu_keyboard():
    """Создает инлайн-клавиатуру главного меню"""
    f"/categories – Актуальные категории\n"
    f"/category – Работа с категорией\n"
    f"/add – Добавить рекомендацию в категорию\n"
    f"/find – Найти свою рекомендацию (для редактирования, удаления)\n"
    f"/anything – Искать случайные рекомендации по категории\n"
    f"/specific – Искать рекомендации по слову/фразе"

    keyboard = [
        [
            # Кнопки первого ряда
            InlineKeyboardButton("🌤️ Актуальные категории", callback_data='categories'),
            InlineKeyboardButton("🖥️ Работа с категорией", callback_data='category'),
        ],
        [
            # Кнопки второго ряда
            InlineKeyboardButton("🌤️ Добавить рекомендацию", callback_data='add_comment'),
            InlineKeyboardButton("🖥️ Найти свою рекомендацию", callback_data='find_comment'),
        ],
        [
            # Кнопки третьего ряда
            InlineKeyboardButton("🌤️ Искать случайные рекомендации", callback_data='anything'),
            InlineKeyboardButton("🖥️ Искать рекомендации по слову/фразе", callback_data='specific'),
        ],
        [InlineKeyboardButton("❌ Закрыть", callback_data='close')]  # Кнопка закрытия
    ]
    return InlineKeyboardMarkup(keyboard)  # Возврат разметки клавиатуры

#   Обработчики команд
def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user = update.effective_user  # Получение информации о пользователе
    command_text = (
                    f"/categories – Актуальные категории\n"
                    f"/category – Работа с категорией\n"
                    f"/add – Добавить рекомендацию в категорию\n"
                    f"/find – Найти свою рекомендацию\n"
                    f"/anything – Искать случайные рекомендации по категории\n"
                    f"/ specific – Искать рекомендации по слову/фразе"
    )

    # # Приветственное сообщение с основной клавиатурой
    update.message.reply_text(
        f"Привет, {user.first_name}! Я твой бот по рекомендациям."
        f"Ты можешь использовать кнопки ниже или команды:\n{command_text}")

    ,
        reply_markup=create_main_menu_keyboard()    #create_reply_keyboard()
    )

#Актуальные категории
def categories(update: Update, context: CallbackContext) -> None:

    if parent_id == None:
        cursor.execute("SELECT id,name FROM categories WHERE active AND parent_id = ?", (parent_id))

    row = cursor.fetchone()
    if row:
        zoo_id = row.zoo_id

        cursor.execute("SELECT * FROM animals WHERE zoo_id = ?", (zoo_id))
        result = cursor.fetchall()


#Работа с категорией
def category(update: Update, context: CallbackContext) -> None:


#Добавить рекомендацию в категорию
def add(update: Update, context: CallbackContext) -> None:

#Найти свою рекомендацию
def find(update: Update, context: CallbackContext) -> None:

#Искать случайные рекомендации по категории
def anything(update: Update, context: CallbackContext) -> None:

#Искать рекомендации по слову/фразе
def specific(update: Update, context: CallbackContext) -> None:




def button_click(update: Update, context: CallbackContext) -> int:
    """Обработчик нажатий инлайн-кнопок"""
    query = update.callback_query  # Данные callback-запроса
    query.answer()  # Подтверждение получения callback

    # Обработка кнопки Актуальные категории
    if query.data == 'categories':
        show_currency_categories(query)  # Вызов функции показа курсов
        return SHOW_INFO  # Переход в состояние показа информации

    # Обработка кнопки погоды
    elif query.data == "weather":
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
            text="Меню работы с рекомендациями: ",
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


def show_currency_categories(query):
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


def comments_stats(update: Update, context: CallbackContext):
    """Показывает статистику запросов рекомендаций (только для администраторов)"""
    # Проверка прав администратора
    # print(f" {update.effective_user.id}  -  {ADMIN_IDS}")
    # if f"{update.effective_user.id}" not in ADMIN_IDS:
    #     update.message.reply_text("⚠️ Эта команда доступна только администраторам")
    #     return

    try:
        # Проверка существования и доступности файла логов
        if not os.path.exists(COMMENT_LOG_PATH) or os.path.getsize(COMMENT_LOG_PATH) == 0:
            update.message.reply_text("📊 Статистика пока недоступна. Запросы еще не делались.")
            return

        # Чтение и обработка файла логов
        logs = []
        with open(COMMENT_LOG_PATH, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Пропуск заголовка

            for row in reader:
                if not row:  # Пропуск пустых строк
                    continue
                # Нормализация строк (добавление недостающих значений)
                if len(row) < 6:
                    row += [''] * (6 - len(row))
                logs.append(row[:6])  # Сохранение только первых 5 значений

        # Создание DataFrame из логов
        df = pd.DataFrame(logs, columns=['timestamp', 'user_id', 'username', 'category_id', 'keyword', 'status'])

        # Проверка на наличие данных
        if df.empty:
            update.message.reply_text("📊 Статистика пока недоступна. Нет данных для анализа.")
            return

        # Преобразование user_id и category_id в числовой формат
        df['user_id'] = pd.to_numeric(df['user_id'], errors='coerce')
        df['category_id'] = pd.to_numeric(df['category_id'], errors='coerce')

        # Расчет основных метрик
        total_requests = len(df)  # Общее количество запросов
        status_counts = df['status'].value_counts()  # Распределение по статусам
        success_requests = status_counts.get('success', 0)  # Успешные запросы
        error_requests = status_counts.get('error', 0)  # Ошибки сервера
        unique_users = df['user_id'].nunique()  # Уникальные пользователи
        unique_categories = df[df['status'] == 'success'].nunique()  # Уникальные категории (только успешные запросы)

        # Топ-5 слов/фраз (только успешные запросы)
        popular_keywords = df[df['status'] == 'success']['keyword'].value_counts().head(5)

        # Формирование текстового отчета
        report = (
            f"📊 Статистика запросов рекомендаций:\n"
            f"• Всего запросов: {total_requests}\n"
            f"• Успешных запросов: {success_requests}\n"
            f"• Неуспешных запросов: {error_requests}\n"
            f"• Уникальных пользователей: {unique_users}\n\n"
            f"• Уникальных категорий: {unique_categories}\n\n"
            f"🏙️ Топ-5 поисковых слов/фраз:\n"
        )

        # Добавление информации о поисковых словах/фразах
        if not popular_keywords.empty:
            for keyword, count in popular_keywords.items():
                report += f"  - {keyword}: {count}\n"
        else:
            report += "  Нет данных о поисковых словах/фразах\n"

        # Анализ ежедневной активности поиска рекомендаций
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
                    report += "\n📅 Активность поиска рекомендаций за последние 7 дней:\n"
                    for _, row in daily_activity.iterrows():
                        report += f"  {row['date']}: {row['requests']} запросов\n"
                else:
                    report += "\n📅 Нет данных о ежедневной активности поиска рекомендаций\n"
            else:
                report += "\n📅 Нет данных о ежедневной активности поиска рекомендаций\n"
        except Exception as e:
            # Обработка ошибок анализа времени
            logger.error(f"Ошибка при расчете ежедневной активности поиска рекомендаций: {e}")
            report += "\n📅 Не удалось рассчитать ежедневную активность поиска рекомендаций\n"

        # Отправка текстового отчета
        update.message.reply_text(report)

        # Создание и отправка графика (если есть данные)
        if not popular_keywords.empty:
            plt.figure(figsize=(10, 6))  # Размер графика
            # Построение столбчатой диаграммы
            popular_keywords.plot(kind='bar', color='skyblue')
            plt.title('Топ запрашиваемых слов/фраз')  # Заголовок
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

    # Регистрация обработчиков
    dispatcher.add_handler(conv_handler)  # Диалоги рекомендаций
    dispatcher.add_handler(CommandHandler("start", start))  # Команда /start
    dispatcher.add_handler(CommandHandler("categories", categories))  # Команда /categories
    dispatcher.add_handler(CommandHandler("category", category))  # Команда /category
    dispatcher.add_handler(CommandHandler("add", add))  # Команда /add
    dispatcher.add_handler(CommandHandler("find", find)) # Команда /find
    dispatcher.add_handler(CommandHandler("anything", anything))  # Команда /anything
    dispatcher.add_handler(CommandHandler("specific", specific))  # Команда /specific

    # Обработчики инлайн-кнопок
    dispatcher.add_handler(CallbackQueryHandler(button_click, pattern='^(currency|back_to_menu|close)$'))
    # Обработчик статистики
    dispatcher.add_handler(CommandHandler("comments_stats", comments_stats))

    updater.start_polling()  # Запуск бота в режиме опроса
    logger.info("Бот запущен и готов к работе")  # Запись в лог
    updater.idle()  # Бесконечный цикл до остановки


if __name__ == '__main__':
    main()  # Запуск приложения