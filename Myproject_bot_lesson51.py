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

# - Главное меню (при отказах - возврат в главное меню):                MAIN
# - /add - Добавление новой рекомендации                                ADD -> ADD_CHOOSE_CAT
#        -   Выбор категории или отказ                                  ADD_CHOOSE_CAT -> ADD_COM
#        -   Добавление рекомендации по выбранной категории или отказ   ADD_COM -> ADD_COM|ADD_CHOOSE_CAT|MAIN
# - /find - Поиск и просмотр по рекомендациям                           FIND -> FIND_CHOOSE_CAT
#        -   Выбор категории или отказ                                  FIND_CHOOSE_CAT -> FIND_ANY_COM|FIND_SPEC_COM
#        -  1. /anything - Выдача рандомных рекомендаций в выбранной категории FIND_ANY_COM -> FIND_COM
#        -  2. /specific - Выдача рекомендаций по ключевым словам              FIND_SPEC_COM -> FIND_EDIT_KEY
#           -   ввод пользователем ключевого слова или отказ                   FIND_EDIT_KEY -> FIND_COM

#        -   поиск по двум столбцам: название и комментарий.                   FIND_COM -> FIND_ANY_COM|FIND_SPEC_COM|FIND_CHOOSE_CAT|MAIN
#        -   выдача по 5 столбцам: своя/чужая, имя пользователя, id рекомендации, название, комментарий.
# - /ctrl - Управление своими рекомендациями:                           CTRL -> CTRL_ID
#        -   Ввод id рекомендации или отказ                             CTRL_ID -> CTRL_EDIT_COM|CTRL+DEL_COM|MAIN
#        -   Проверка по id, что это своя рекомендация (если чужая - повторный ввод id рекомендации или оказ)
#        -   1. /edit - редактировать свою рекомендацию                 CTRL_EDIT_COM -> CTRL_ID|CTRL+DEL_COM|MAIN
#        -   2. /del - удалить свою рекомендацию                        CTRL+DEL_COM -> CTRL_ID|MAIN

#Документация по pandas	https://pandas.pydata.org/docs/user_guide/index.html

# Импорт необходимых библиотек
from array import array
import requests  # Для выполнения HTTP-запросов к API
import logging  # Для настройки системы логирования
import csv  # Для работы с CSV-файлами (чтение/запись)
from datetime import datetime  # Для работы с датой и временем
import pandas as pd  # Для анализа и обработки данных
import matplotlib.pyplot as plt  # Для создания графиков и визуализации данных
from io import BytesIO  # Для работы с бинарными потоками в памяти
import os  # Для взаимодействия с файловой системой
import time #для замера времени
import sqlite3
from collections import namedtuple
from threading import Thread

# Импорт компонентов Telegram API
from dotenv import load_dotenv #config.env
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
import random

# Настройка системы логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат записи логов
    level=logging.INFO  # Уровень детализации логов
)
logger = logging.getLogger(__name__)  # Создание логгера для текущего модуля

load_dotenv("config.env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print(TOKEN)

# States
START, FIND_CAT_COM, FIND_CAT, FIND_CAT_MANY, CHOOSE_CAT_ID, FIND_CAT_ONE, CANCEL = range(7)

#OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")  # API-ключ OpenWeatherMap
#my_telegram_id = os.getenv("MY_TELEGRAM_ID")
#CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"  # URL API Центробанка для курсов валют
COMMENT_LOG_PATH = "comments_log.csv"  # Путь к файлу логов рекомендаций
#ADMIN_IDS = [my_telegram_id]  # Список ID администраторов бота
#print(f"токен={TOKEN} OPENWEATHER_API_KEY = {OPENWEATHER_API_KEY} my_telegram_id ={my_telegram_id}")

DB_path = "comments.db"
# Хранилище временных данных
user_data = {}
#first = True

 #Инициализация файла логов

if not os.path.exists(COMMENT_LOG_PATH):
    # Создание нового файла с заголовками
    with open(COMMENT_LOG_PATH, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'user_id', 'username', 'case', 'status','handler', 'category_id' ])
else:
    # Проверка существующего файла на наличие заголовков
    with open(COMMENT_LOG_PATH, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        # Если заголовки отсутствуют - добавляем их
        if not first_line.startswith('timestamp') or 'user_id' not in first_line:
            with open(COMMENT_LOG_PATH, 'r+', encoding='utf-8') as f:
                content = f.read()
                f.seek(0, 0)
                f.write('timestamp,user_id,username,case,status,handler,category_id\n' + content)

def status(n:int):
   if n == START:
       return 'START'
   elif n == FIND_CAT_COM:
       return 'FIND_CAT_COM'
   elif n == FIND_CAT:
       return 'FIND_CAT'
   elif n == FIND_CAT_ONE:
       return 'FIND_CAT_ONE'
   elif n == FIND_CAT_MANY:
       return 'FIND_CAT_MANY'
   elif n == CHOOSE_CAT_ID:
       return 'CHOOSE_CAT_ID'
   elif n == CANCEL:
       return 'CANCEL'
   else:
       return '?'


def log_comment_request(user_id: int, username: str, case: str, status: str, handler:str, category_id: int ):
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
                case,  # действие
                status,     # States
                handler,    # функция
                category_id,  # id категории
            ])
    except Exception as e:
        # Обработка ошибок записи в лог
        logger.error(f"Ошибка записи в лог: {e}")

def log_start(update: Update, context: CallbackContext) -> None:
    records = []
    with open(COMMENT_LOG_PATH, 'r', encoding='utf-8') as file:
        reader = list(csv.reader(file))
        # Найти индекс последнего status='START'
        last_start_idx = None
        for i in range(len(reader)-1, -1, -1):
            if len(reader[i]) > 4 and reader[i][4] == 'START':
                last_start_idx = i
                break
        if last_start_idx is not None:
            records = reader[last_start_idx:]
        else:
            records = []

    if not records:
        update.message.reply_text("Нет записей с status='START' в логе.")
        return

    # Формируем текст ответа
    response = []
    for row in records:
        # Преобразуем строку в удобочитаемый вид
        response.append('|'.join(row))
    # Telegram ограничение в 4096 символов, разобьем, если что
    for i in range(0, len(response), 40):
        text = '\n'.join(response[i:i+40])
        update.message.reply_text(text)


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
                if len(row) < 8:
                    row += [''] * (8 - len(row))
                logs.append(row[:8])  # Сохранение только первых 8 значений

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
        unique_categories = df[df['status'] == 'success']['category_id'].nunique()  # Уникальные категории (только успешные запросы)

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
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            df = df.dropna(subset=['timestamp'])
            if not df.empty:
                df['date'] = df['timestamp'].dt.date
                daily_activity = df.groupby('date').size().reset_index(name='requests')
                daily_activity = daily_activity.sort_values('date', ascending=False).head(7)
                report += "\n📅 Активность по дням (последние 7):\n"
                for _, row in daily_activity.iterrows():
                    report += f"  {row['date']}: {row['requests']}\n"
        except Exception as e:
            report += f"\n(Ошибка анализа ежедневной активности: {e})\n"


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

def initialize_categories():

    conn = sqlite3.connect(DB_path)  # Создаём новое соединение в этом потоке
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        active BOOLEAN,
        parent_id INTEGER
    )''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        dt_first DATETIME NOT NULL,
        dt_last DATETIME NOT NULL,
        comment TEXT,
        last_category_id INTEGER DEFAULT 0,
        last_keyword TEXT DEFAULT '',
        result TEXT DEFAULT 'random',
        max_comments INTEGER DEFAULT 0
    )''')
    conn.commit()

    cursor.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category_id INTEGER,
        name TEXT NOT NULL,
        comment TEXT NOT NULL,
        dt DATETIME NOT NULL
    )''')
    conn.commit()

    categories = [
        (1, 'Книги', 1, 0),
        (2, 'Учебники', 1, 1),
        (3, 'Справочники', 1, 2),
        (4, 'Справочники по математике', 1, 3),
        (5, 'Справочники по физике', 1, 3),
        (6, 'Приключения', 1, 1),
        (7, 'Современные авторы', 1, 6),
        (8, 'Ретро', 1, 6),
        (9, 'Фантастика', 1, 1),
        (10, 'Детективы', 1, 1),
        (11, 'Любовные истории', 1, 1),
        (12, 'Стихи', 1, 1),
        (13, 'Фильмы', 1, 0),
        (14, 'Сериалы', 1, 13),
        (15, 'Приключения', 1, 14),
        (16, 'Путешествия', 1, 14),
        (17, 'Любовные', 1, 14),
        (18, 'Анимация', 1, 13),
        (19, 'Зарубежные', 1, 13),
        (20, 'Российская классика', 1, 13),
        (21, 'Российские детективы', 1, 13),
        (22, 'Мультфильмы', 1, 13)
    ]

    cursor.executemany('INSERT OR IGNORE INTO categories (id, name, active, parent_id) VALUES (?, ?, ?, ?)', categories)
    conn.commit()
    conn.close()

# Выполнение SQL-запросов с автоматическим подключением к базе данных.
def execute_query(query, params=(), fetchone=False, fetchall=False):

    try:
        #print(f"DB_path = {DB_path}")
        conn = sqlite3.connect(DB_path)
        #conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)

        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()
        else:
            result = cursor.lastrowid

        conn.commit()
        conn.close()
        return result

    except Exception as e:
        print(f"Ошибка базы данных: {e}\n"
              f"{query}"
              f"{params}")
    return None

def keyboard_for_id(id:int):
    keyboard = [
        [InlineKeyboardButton("Использовать", callback_data="choose_"+str(id))],
        [InlineKeyboardButton("Использовать родителя", callback_data="parent_"+str(id))],
        [InlineKeyboardButton("Редактировать", callback_data="edit_"+str(id))],
        [InlineKeyboardButton("Выбрать подкатегорию", callback_data="subcategory_"+str(id))],
        [InlineKeyboardButton("Выбрать из категорий рядом", callback_data="near_"+str(id))],
        [InlineKeyboardButton("Выбрать главные категории", callback_data="main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup

def keyboard_choose(id:int, data):

    keyboard = []
    if data.startswith("subcategory_"):
        cat_id = int(data.replace("subcategory_", ""))
        results = execute_query("SELECT id, name, parent_id FROM categories WHERE parent_id = ?", (cat_id,),
                                   fetchall=True)
        for comm in results:
            keyboard.append([InlineKeyboardButton(f"id={comm[0]} {comm[1]}", callback_data="choose_" + str(comm[0]))])

    elif data.startswith("near_"):
        cat_id = int(data.replace("near_", ""))

        results = execute_query(
            "SELECT c.id as id, c.name as name, c.parent_id as parent_id FROM categories c "
            "INNER JOIN categories cat ON (c.parent_id = cat.parent_id) WHERE cat.id = ?", (cat_id,), fetchall=True)

        for comm in results:
            keyboard.append([InlineKeyboardButton(f"id={comm[0]} {comm[1]}", callback_data="choose_" + str(comm[0]))])

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup

def have_subcategory(id:int):
    results = execute_query("SELECT id, name, parent_id FROM categories WHERE parent_id = ?", (id,),
                            fetchone=True)
    return bool(results)

def have_near(id:int):
    results = execute_query(
        "SELECT c.id, c.user_id, c.id as id, c.name as name, c.parent_id as parent_id FROM categories c "
        "INNER JOIN categories cat ON (c.parent_id = cat.parent_id) and (c.id != cat.id) WHERE cat.id = ?", (id,), fetchall=True)

    return bool(results)

# Обработчик команды /start
def start(update: Update, context: CallbackContext) -> None:

    user = update.effective_user
    telegram_id = user.id
    user_name = user.first_name

    # Проверяем, есть ли пользователь в базе
    users = execute_query("SELECT id, name FROM users WHERE telegram_id = ?", (telegram_id,), fetchone=True)

    txt1 = ""
    dt_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not users:
        # Если пользователь впервые заходит в бота
        user_id = execute_query("INSERT INTO users (telegram_id, name, dt_first, dt_last) VALUES (?, ?, ?, ?)", (telegram_id, user_name, dt_now, dt_now))

        update.message.reply_text(f"Добро пожаловать, {user_name}! Ты первый раз!")
    else:
        # Обновляем время последнего захода
        user_id = execute_query("UPDATE users SET dt_last = ? WHERE telegram_id = ?", (dt_now,telegram_id,))
        update.message.reply_text(f"Добро пожаловать, {user_name}! Ты уже бывал!")

    context.user_data['user_id'] = user_id
    context.user_data['user_name'] = user_name
    context.user_data['cat_id'] = 0

    commands = ("/find_cat - Действия над категорией\n"
                "/add - Добавить рекомендацию\n"
                "/edit - Изменить свою рекомендацию\n"
                "/find - Найти рекомендации\n"
                "/end - Закончить диалог"
                )

    #update.message.reply_text(f"Используй команды:\n{commands}")

    keyboard = [
        [InlineKeyboardButton("FindCat", callback_data="find_cat")],
        [InlineKeyboardButton("End", callback_data="end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text(f"Используй команды:\n{commands}", reply_markup=reply_markup)
    elif update.callback_query:
        update.callback_query.message.reply_text(f"Варианты:\n{commands}", reply_markup=reply_markup)

    log_comment_request(user_id, user_name, 'start', status(START), 'start', 0 )

    return START

# обработчик команды /start
def button_handler(update: Update, context: CallbackContext) -> int:

    user_id = context.user_data.get('user_id',0)
    user_name = context.user_data.get('user_name', '')

    query = update.callback_query
    query.answer()

    if query.data == "find_cat":
        log_comment_request(user_id, user_name, 'обработка /find_cat', status(FIND_CAT_COM), 'button_handler', '0')
        return FIND_CAT_COM
    # elif query.data == "add_cat":
    #     return add_cat(update, context)
    elif query.data == "end":
        log_comment_request(user_id, user_name, 'обработка /end', 'ConversationHandler.END', 'button_handler', '0')
        return ConversationHandler.END
    # elif query.data == "find":
    #     return find(update, context)
    # elif query.data.startswith("choose"):
    #     return start(update, context)
    # elif query.data == "add":
    #     return edit(update, context)
    # elif query.data == "edit":
    #     return edit(update, context)
    else:
        log_comment_request(user_id, user_name, f"не распознали {query.data}", status(START), 'button_handler', '0')
        return START

# обработчик команды /find_cat
def command_find_cat(update: Update, context: CallbackContext):

    if update.message:
        # Это команда /find_cat
        update.message.reply_text("Введите ID или ключевое слово:")
    elif update.callback_query:
        # Это callback
        query = update.callback_query
        query.answer()
        query.message.reply_text("Введите ID или ключевое слово:")

    user_id = context.user_data.get('user_id', 0)
    user_name = context.user_data.get('user_name', '')

    log_comment_request(user_id, user_name, 'ожидаем id/ключ', status(FIND_CAT), 'command_find_cat', '0' )
    return FIND_CAT

def find_cat(update: Update, context: CallbackContext):

    return command_find_cat(update, context)

#     user_id = context.user_data.get('user_id',0)
#     user_name = context.user_data.get('user_name', '')
#
#     if update.message:
#         # Это команда /find_cat
#         update.message.reply_text("Введите ID или ключевое слово (find_cat):")
#     elif update.callback_query:
#         # Это callback FIND_CAT
#         query = update.callback_query
#         query.answer()
#         query.message.reply_text("Введите ID или ключевое слово (find_cat):")
#
#     # keyboard = [
#     #     [InlineKeyboardButton("Ok", callback_data="find_cat")]
#     #     ]
#     # reply_markup = InlineKeyboardMarkup(keyboard)
#     # update.message.reply_text("Ок?", reply_markup=reply_markup)
#
#     log_comment_request(user_id, user_name, 'find_cat', status(FIND_CAT), 'find_cat', '0' )
#     return FIND_CAT

# обработчик состояния FIND_CAT
def handle_cat_input(update: Update, context: CallbackContext) -> int:

    if True:
        return FIND_CAT_MANY


    if update.message:

        update.message.reply_text(f"handle_cat_input update={update}\n context={context}")

        #print(f"handle_cat_input update.message {update.message}")
        # Это текст
        keyword = update.message.text.strip()

    elif update.callback_query:
        #print(f"handle_cat_input update.callback_query {update.callback_query}")

        # Это callback FIND_CAT
        query = update.callback_query
        query.answer()
        keyword = query.data

        update.message.reply_text(f"handle_cat_input keyword={keyword}")
    else:
        keyword = ''


    user_id = context.user_data.get('user_id',0)
    user_name = context.user_data.get('user_name', '')

   #keyword = update.message.text.strip()
    log_comment_request(user_id, user_name, f"обрабатываем {keyword}", status(FIND_CAT), 'handle_cat_input', '')

    try:
        cat_id = int(keyword)
        categories = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (cat_id,), fetchone=True)
        if categories:
            reply_markup = keyboard_for_id( cat_id )
            update.message.reply_text(f"Выберите действие над категорией с id={cat_id}", reply_markup=reply_markup)
            log_comment_request(user_id, user_name, 'нашли по id', status(CHOOSE_CAT_ID), 'handle_cat_input', str(cat_id))
            return CHOOSE_CAT_ID
    except ValueError:
        pass

    keywords = [kw.strip() for kw in keyword.split() if kw.strip()]
    if not keywords:
        update.message.reply_text("Вы ввели пустую строку. Попробуйте ещё раз.")
        log_comment_request(user_id, user_name, 'пустой ключ', status(FIND_CAT_COM), 'handle_cat_input', '')
        return FIND_CAT_COM

    query = (
        "SELECT id, name, parent_id FROM categories "
        "WHERE "
        " OR ".join( ["name LIKE ?" for _ in keywords] )
    )
    params = [f"%{kw}%" for kw in keywords]
    results = execute_query(query, tuple(params), fetchall=True)

    if not results:
        update.message.reply_text(f"Не найдено ни одной категории по '{keyword}'.")

        log_comment_request(user_id, user_name, f"нет категорий по {keyword}", status(START), 'handle_cat_input', '')
        return START

    elif len(results) == 1:
        comm = results[0]
        keyboard = keyboard_for_id(comm[0])
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f"Что делать с категорией ID={comm[0]} '{comm[1]}?", reply_markup=reply_markup)

        log_comment_request(user_id, user_name, f"одна категория. Действия на выбор", status(CHOOSE_CAT_ID), 'handle_cat_input',  str(comm[0]))
        return CHOOSE_CAT_ID

    else:
         response = "Найдено несколько категорий. Выберите нужную:\n"
         keyboard = []
         str_id = ''
         for comm in results:
             keyboard.append([InlineKeyboardButton( f"id={comm[0]} {comm[1]}", "choose_"+comm[0] ) ] )
             str_id = str_id + " " + comm[0]

         reply_markup = InlineKeyboardMarkup(keyboard)
         update.message.reply_text(response, reply_markup = reply_markup)

         log_comment_request(user_id, user_name, f"несколько категорий. На выбор", status(FIND_CAT_MANY),
                             'handle_cat_input', str_id)

         return FIND_CAT_MANY

def finish_process(context: CallbackContext, query, user_id, user_name, action, cat_id):

    context.user_data['cat_id'] = cat_id

    query.message.reply_text("Процесс завершен. Возвращаемся в начало.")
    log_comment_request(user_id, user_name, action, status(START), 'find_cat_one', str(cat_id))
    return START

# обработчик состояния FIND_CAT_ONE
def find_cat_one(update: Update, context: CallbackContext) -> int:

    user_id = context.user_data.get('user_id',0)
    user_name = context.user_data.get('user_name', '')

    query = update.callback_query
    query.answer()
    data = query.data

    if data.startswith("choose_"):
        cat_id = int(data[len("choose_"):])
        return finish_process(context, query, user_id, user_name, "выбрана категория", cat_id)

    elif data.startswith("edit_"):
        cat_id = int(data[len("edit_"):])
        return finish_process(context, query, user_id, user_name, "изменена категория", cat_id)

    elif data.startswith("subcategory_") or data.startswith("near_"):
        if data.startswith("subcategory_"):
            cat_id = int(data.replace("subcategory_", ""))
        else:
            cat_id = int(data.replace("near_", ""))

        log_comment_request(user_id, user_name, "несколько категорий.", status(FIND_CAT_MANY),
                            'find_cat_one', cat_id)
        return FIND_CAT_MANY

    else:
       query.message.reply_text(f"Неизвестная команда в find_cat_one {data}.")
       log_comment_request(user_id, user_name, f"Неизвестная команда {data}", status(START), 'find_cat_one', '')
       return START

# обработчик состояния FIND_CAT_MANY
def find_cat_many(update: Update, context: CallbackContext) -> int:

    user_id = context.user_data.get('user_id',0)
    user_name = context.user_data.get('user_name', '')

    query = update.callback_query
    query.answer()
    data = query.data

    if data.startswith("subcategory_") or data.startswith("near_"):

        if data.startswith("subcategory_"):
            cat_id = int(data.replace("subcategory_", ""))
        else:
            cat_id = int(data.replace("near_", ""))

        keyboard = keyboard_choose(cat_id, data)

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text(f"Выберите вариант", reply_markup=reply_markup)

        log_comment_request(user_id, user_name, "категории для выбора", status(CHOOSE_CAT_ID), 'find_cat_many', str(cat_id))
        return CHOOSE_CAT_ID

    elif data in ["cancel"]:
        query.message.reply_text("Отказ")

        log_comment_request(user_id, user_name, "категории для выбора", status(CANCEL), 'find_cat_many', '')
        return CANCEL
    else:
       query.message.reply_text(f"Неизвестная команда {data}.")

       log_comment_request(user_id, user_name, f"Неизвестная команда {data}", status(START), 'find_cat_many', '')
       return START

# обработчик состояния CHOOSE_CAT_ID
def handle_cat_id(update: Update, context: CallbackContext) -> int:

    user_id = context.user_data.get('user_id',0)
    user_name = context.user_data.get('user_name', '')

    if update.message:
        data = update.message.text

    elif update.callback_query:
        #print(f"handle_cat_input update.callback_query {update.callback_query}")

        # Это callback FIND_CAT
        query = update.callback_query
        query.answer()
        data = query.data

    cat_id = int(data.replace("choose_", ""))
    reply_markup = keyboard_for_id(cat_id)
    update.message.reply_text(f"Выберите действие над категорией с id={cat_id}:", reply_markup=reply_markup)

    log_comment_request(user_id, user_name, f"одна категория. Действия на выбор", status(FIND_CAT_ONE), 'handle_cat_id',
                        str(cat_id))
    return FIND_CAT_ONE

# обработчик состояния CANCEL
def cancel(update: Update, context: CallbackContext) -> int:

    user_id = context.user_data.get('user_id',0)
    user_name = context.user_data.get('user_name', '')

    update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    log_comment_request(user_id, user_name, "действие по cancel", status(START), 'cancel',
                        '')
    return START

# обработчик состояния END
def end(update: Update, context: CallbackContext) -> int:

    user_id = context.user_data.get('user_id',0)
    user_name = context.user_data.get('user_name', '')

    update.message.reply_text("Закончили.", reply_markup=ReplyKeyboardRemove())
    log_comment_request(user_id, user_name, "действие по end", status(START), 'end',
                        '')
    return ConversationHandler.END

def unknown(update: Update, context: CallbackContext):

    user_id = context.user_data.get('user_id', 0)
    user_name = context.user_data.get('user_name', '')

    update.message.reply_text(f"Извините, я не понял команду update={update.message.text if update.message else str(update)}")
    log_comment_request(user_id, user_name, f"непонятная команда {update}", status(START), 'unknown',
                        '')
    return START

# --- Main Function ---
def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    #dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("find_cat", command_find_cat))
    # dispatcher.add_handler(CommandHandler("end", end))
    dispatcher.add_handler(CommandHandler("comments_stats", comments_stats))
    dispatcher.add_handler(CommandHandler('log_start', log_start))

   # Регистрация обработчиков
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [CallbackQueryHandler(button_handler, pattern="^(start|find_cat|end)$")],     #->FIND_CAT_COM|END
            FIND_CAT: [CallbackQueryHandler(handle_cat_input),MessageHandler(Filters.text & ~Filters.command, handle_cat_input)],
            FIND_CAT_COM: [CallbackQueryHandler(command_find_cat)],                 #->FIND_CAT
            #FIND_CAT: [MessageHandler(Filters.text & ~Filters.command, handle_cat_input)], #->CHOOSE_CAT_ID|FIND_CAT_MANY|FIND_CAT_COM
            #FIND_CAT: [CallbackQueryHandler(find_cat)],
            FIND_CAT_MANY: [CallbackQueryHandler(find_cat_many, pattern=r"^(choose_|edit_|subcategory_|near_)\d+$")], #->CHOOSE_CAT_ID|CANCEL|START
            CHOOSE_CAT_ID: [CallbackQueryHandler(handle_cat_id, pattern=r"^(choose_)\d+$")],  #->FIND_CAT_ONE
            FIND_CAT_ONE: [CallbackQueryHandler(find_cat_one, pattern=r"^(choose_|edit_|subcategory_|near_)\d+$")], #->START|FIND_CAT_MANY
            CANCEL: [CallbackQueryHandler(cancel, pattern=r"^cancel$")],    #->START
                 },
        fallbacks=[CommandHandler('start', start), MessageHandler(Filters.command, unknown)]

     )
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()


#
#
# def find_cat_kword(update: Update, context: CallbackContext):
#     """Поиск категорий по ключевому слову или отображение верхнего уровня."""
#     print("find_cat_kword")
#     keyword = update.message.text.strip()
#     user_id = update.message.from_user.id
#     user_data = {}
#
#     try:
#         category_id = int(keyword)
#         categories = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (category_id,), fetchone=True)
#         if categories:
#             parent_id = categories['parent_id']
#             reply_markup = generate_find_keyboard(category_id, parent_id)
#
#             update.message.reply_text(f"Найдена категории c id={category_id}\nВыберите действие с ней:",
#                                 reply_markup=reply_markup)
#             return FIND_CAT_ACTIONS
#
#     finally:
#
#             keywords = [kw.strip() for kw in keyword.split() if kw.strip()]
#
#     if not keywords:
#         update.message.reply_text("Вы ввели пустую строку. Попробуйте ещё раз.")
#         return FIND_CAT_KWORD
#
#     query = (
#         "SELECT id, name, parent_id FROM categories "
#         "WHERE "
#         " OR ".join( ["name LIKE ?" for _ in keywords] )
#     )
#     params = [f"%{kw}%" for kw in keywords]
#     results = execute_query(query, tuple(params), fetchall=True)
#
#     if not results:
#         update.message.reply_text(f"Не найдено ни одной категории по ключевым словам: '{kword}'.")
#         return FIND_CAT_KWORD
#
#     elif len(results) == 1:
#         comm = results[0]
#         update.message.reply_text(
#             f"Нашли одну категорию с ID={comm['id']} '{comm['name']}'"
#             )
#         return FIND_CAT_ACTIONS
#     else:
#         response = "Найдено несколько категорий. Укажите ID нужной:\n"
#         for comm in results:
#             response += f"ID={comm['id']}, Категория: {comm['cat_name']}, Название: {comm['name']}\n"
#
#         update.message.reply_text(response)
#
#     return FIND_CAT_KWORD
#
# def category_actions(update: Update, context: CallbackContext):
#     """Действия с выбранной категорией."""
#     query = update.callback_query
#     query.answer()
#     category_id = int(query.data.split("_")[1])
#
#     category = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (category_id,), fetchone=True)
#
#     if category:
#         # Формирование кнопок
#         reply_markup = generate_find_keyboard(category_id, parent_id)
#
#         return FIND_CAT_ACTIONS
#
# # Обработчик callback_data
# def find_cat_actions(update: Update, context: CallbackContext):
#     query = update.callback_query
#     query.answer()
#     data = query.data
#
#     if data.startswith("confirm_"):
#         category_id = int(data.split("_")[1])
#
#         category = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (category_id,),
#                                    fetchone=True)
#         if category:
#             user_data[query.from_user.id]['selected_category'] = category_id
#             query.message.reply_text`(f"Вы выбрали:\nID: {category[0]}\nНазвание: {category[1]}\nParent ID: {category[2]}")
#         else:
#             query.message.reply_text`("Категория не найдена.")
#
#     elif data.startswith("parent_"):
#          category_id = int(data.split("_")[1])
#
#          category = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (category_id,), fetchone=True)
#
#          if category:
#             if category['id'] != 0:  # Если есть родитель
#
#                 category = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (category[2],),
#                                          fetchone=True)
#                 if category:
#                     user_data[query.from_user.id]['selected_category'] = category[0]
#                     query.message.reply_text`(
#                         f"Вы выбрали категорию с ID: {category['id']}\nНазвание: {category['name']}\nParent ID: {category['parent_id']}")
#                 else:
#                     query.message.reply_text`("Родительская категория не найдена.")
#             else:
#                 query.message.reply_text`("Родительская категория не найдена.")
#          else:
#             query.message.reply_text`("Родительская категория не найдена.")
#
#     elif data.startswith("siblings_"):
#         category_id = int(data.split("_")[1])
#
#         category = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (category_id,),
#                          fetchone=True)
#         if category:
#             category = execute_query("SELECT id, name, parent_id FROM categories WHERE parent_id = ?", (category[2],),
#                                      fetchall=True)
#             if siblings:
#                 buttons = [[InlineKeyboardButton(f"{sibling[0]}: {sibling[1]}", callback_data=f"confirm_{sibling[0]}")] for sibling in siblings]
#                 reply_markup = InlineKeyboardMarkup(buttons)
#                 query.message.reply_text`("Соседние категории:", reply_markup=reply_markup)
#                 return
#
#         qquery.message.reply_text`("Соседние категории не найдены.")
#
#     elif data.startswith("subcategories_"):
#         category_id = int(data.split("_")[1])
#
#         subcategories = execute_query("SELECT id, name, parent_id FROM categories WHERE parent_id = ?", (category_id,),
#                                  fetchall=True)
#         if subcategories:
#             buttons = [[InlineKeyboardButton(f"{subcategory[0]}: {subcategory[1]}", callback_data=f"confirm_{subcategory[0]}")] for subcategory in subcategories]
#             reply_markup = InlineKeyboardMarkup(buttons)
#             query.message.reply_text`("Подкатегории:", reply_markup=reply_markup)
#         else:
#             query.message.reply_text`("Подкатегории не найдены.")
#
#     elif data.startswith("goto_find_cat"):
#         query.delete_message()  # Удаляем предыдущее сообщение с кнопками
#         find_cat(update, context)
#
#     elif data.startswith("goto_start"):
#         query.delete_message()  # Удаляем предыдущее сообщение с кнопками
#         start(update, context)
#
#  # /edit_cat
# def edit_cat(update: Update, context: CallbackContext):
#     """Обработчик команды /edit_cat."""
#     user_id = update.message.chat.id
#     if 'selected_category' not in user_data:
#         update.message.reply_text("Сначала выполните команду /find_cat для выбора категории.")
#     else:
#         category_id = user_data.get('selected_category',0)
#
#         category = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (category_id,),
#                                  fetchone=True)
#
#         update.message.reply_text(f"Вы собираетесь изменить категорию с ID: {category[0]}\nНазвание: {category[1]}\nParent ID: {category[2]}. Введите новое название:")
#         return EDITING_CAT_ID
#
# def update_category_name(update: Update, context: CallbackContext):
#     """Обновление названия категории."""
#     if 'selected_category' in user_data.get(user_id, {}):
#         category_id = user_data.get('selected_category',0)
#         new_name = update.message.text.strip()
#
#         execute_query("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id,))
#
#         update.message.reply_text(f"Название категории обновлено на: {new_name}")
#
#     return ConversationHandler.END
#
# # Команда /add_cat
# def add_cat(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.chat.id
#     update.message.reply_text("Введите название новой категории:")
#
#     if 'selected_category' not in user_data:
#         user_data['selected_category'] = 0
#         return ADDING_CAT_0
#
#     return ADDING_CAT_ID
#
# def save_new_category(update: Update, context: CallbackContext) -> int:
#     category_name = update.message.text.strip()
#
#     category_id = execute_query("INSERT INTO categories (name, parent_id) VALUES (?, 0)",(category_name,))
#
#     update.message.reply_text(f"Добавлена категория верхнего уровня с id={category_id} '{category_name}'")
#     return ConversationHandler.END
#
# def cancel(update: Update, context: CallbackContext) -> int:
#     update.message.reply_text("Отмена")
#
# # Обработчик действий по категории для /add_cat
# def handle_add_cat(update: Update, context: CallbackContext) -> None:
#     user_id = update.message.chat.id
#     new_name = update.message.text.strip()
#     category_id = user_data.get('selected_category',0)
#
#     reply_markup = generate_keyboard(category_id)
#     update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
#     return ADDING_CAT_DOING
#
# # Обработчик нажатий кнопок
# def button_handler(update: Update, context: CallbackContext) -> None:
#     query = update.callback_query
#     query.answer()
#     data = query.data
#
#     print(f"update={update} update.message={update.message}")
#
#     #user_id = update.message.chat.id
#     user_id = 1
#
#     if data.startswith("add_subcat_"):
#         category_id = int(data.split("_")[2])
#         new_name = user_data.get('new_name','')
#
#         category_id = execute_query("INSERT INTO categories (name, active, parent_id) VALUES (?, ?, ?)", (new_name, True, category_id,))
#
#         user_data['category_id'] = category_id
#
#     elif data.startswith("add_cat_"):
#         parent_id = int(data.split("_")[3])
#         new_name = user_data.get('new_name','')
#
#         category_id = execute_query("INSERT INTO categories (name, active, parent_id) VALUES (?, ?, ?)",
#                                     (new_name, True, parent_id,))
#
#         user_data['category_id'] = category_id
#
#     elif data.startswith("goto_find_cat"):
#          #ищем другое место
#          query.delete_message()
#          find_cat(update.callback_query, context)
#
#     elif data.startswith("goto_start"):
#     #начнем опять с главного меню
#         query.delete_message()
#         start(update.callback_query, context)
#
#     return ConversationHandler.END
# # /add
# def add(update: Update, context: CallbackContext):
#     """Обработчик команды /add."""
#     user_id = update.message.chat.id
#     if 'selected_category' not in user_data.get(user_id, {}):
#         update.message.reply_text("Сначала выполните команду /find_cat для выбора категории.")
#
#         return ConversationHandler.END
#
#     elif user_data['category_id'] == 0:
#         update.message.reply_text("Сначала выполните команду /find_cat для выбора категории.")
#
#         return ConversationHandler.END
#
#     else:
#         category_id = user_data.get('category_id',0)
#         update.message.reply_text(f"О каком объекте Вы хотите поделиться в категории с id={category_id}")
#
#         return ADDING_COMM_NAME
#
# def save_comment(update: Update, context: CallbackContext):
#     """Сохранение комментария."""
#     user_id = update.message.chat.id
#     #category_id = user_data.get('selected_category',0)
#     name = update.message.text.strip()
#     user_data['new_name'] = name
#
#     update.message.reply_text(f"Ок! Итак, {name}. Какие Ваши рекомендации?:")
#
#     return ADDING_COMM_COMM
#
# def save_comment_text(update: Update, context: CallbackContext):
#     """Сохранение текста комментария."""
#     # telegram_user_id здесь это user_id в телеграмме, вначале мы должны определить по нему user_id из таблицы users
#     telegram_user_id = update.message.chat.id
#     category_id = user_data.get('selected_category',0)
#     name = user_data.get('new_name','')
#     comment = update.message.text.strip()
#
#     user_id = get_user_id(telegram_user_id)
#
#     if user_id != 0:
#
#        comments_id = execute_query("INSERT INTO comments (user_id, category_id, name, comment, dt) VALUES (?, ?, ?, ?, ?)",
#                       (user_id, category_id, name, comment, datetime.now().isoformat(),))
#        update.message.reply_text(f"Рекомендация успешно добавлена c id={comments_id}")
#
#     else:
#        update.message.reply_text(f"Рекомендация не добавлена т.к. такой пользователь не найден")
#
#     return ConversationHandler.END
#
# ############################
# def edit(update: Update, context: CallbackContext):
#     """Обработчик команды /add."""
#     update.message.reply_text(f"Введите для поиска id своей рекомендации или ключевое слово/фразу")
#
#     return EDITING_COMM_KWORD
#
# def find_your_comment(update: Update, context: CallbackContext):
#     """Сохранение комментария."""
#     telegram_user_id = update.message.chat.id
#     user_id = get_user_id(telegram_user_id)
#
#     kword = update.message.text.strip()
#     comm = execute_query("SELECT c.id, c.user_id, c.category_id as category_id, cat.name as cat_name, c.name, c.comment FROM comments c "
#                                "INNER JOIN categories cat ON (c.category_id = cat.id) WHERE id = ?", (kword,),  fetchone=True)
#     if comm:
#         if comm['user_id'] == user_id:
#             update.message.reply_text(f"Нашли вашу рекомендацию c id={kword} по {comm['cat_name']} на\n"
#                                       f"{comm['name']}. Введите новое название:")
#             user_data['selected_category'] = comm['category_id']
#             user_data['comment_id'] = comm['kword']
#             return EDITING_COMM_NAME
#
#         else:
#            update.message.reply_text(f"Рекомендация c id={kword} не ваша, а пользователя с id={comm['id']}\n"
#                                       f"Вы не можете ее менять!")
#            return ConversationHandler.END
#     else:
#         # как id не получилось, попробуем через ключевое слово/фразу
#         keywords = [kw.strip() for kw in kword.split() if kw.strip()]
#         if not keywords:
#             update.message.reply_text("Вы ввели пустую строку. Попробуйте ещё раз.")
#             return EDITING_COMM_KWORD
#
#         # Формируем запрос для поиска по ключевым словам
#         try:
#             query = (
#                     "SELECT c.id, c.user_id, users.name AS user_name, c.category_id AS category_id, "
#                     "cat.name AS cat_name, c.name, c.comment "
#                     "FROM comments c "
#                     "INNER JOIN users ON c.user_id = users.id "
#                     "INNER JOIN categories cat ON c.category_id = cat.id "
#                     "WHERE " +
#                     " OR ".join(["c.name LIKE ? OR c.comment LIKE ?" for _ in keywords])
#             )
#             params = [f"%{kw}%" for kw in keywords for _ in range(2)]
#             results = execute_query(query, tuple(params), fetchall=True)
#
#             # Формируем запрос для поиска по ключевым словам
#         except Exception as e:
#             update.message.reply_text(f"Ошибка базы данных: {e}")
#             return ConversationHandler.END
#
#         if not results:
#             update.message.reply_text(f"Не найдено ни одной рекомендации по ключевым словам: '{kword}'.")
#             return FIND_COMM_KWORD
#
#         if len(results) == 1:
#             comm = results[0]
#             update.message.reply_text(
#                 f"Нашли одну рекомендацию с ID={comm['id']} по категории '{comm['cat_name']}'\n"
#                 f"от {comm['user_name']} для '{comm['name']}'. Вот она:\n"
#                 f"{comm['comment']}"
#             )
#             return EDITING_COMM_NAME
#         else:
#             response = "Найдено несколько рекомендаций. Укажите ID нужной:\n"
#             for comm in results:
#                 response += f"ID={comm['id']}, Категория: {comm['cat_name']}, Название: {comm['name']}\n"
#             update.message.reply_text(response)
#
#             return EDITING_COMM_KWORD
#
# def edit_comment(update: Update, context: CallbackContext):
#     """Сохранение комментария."""
#     user_id = update.message.chat.id
#     # category_id = user_data.get('selected_category','')
#     name = update.message.text.strip()
#     user_data['comm_name'] = name
#
#     update.message.reply_text(f"Ок! Итак, {name}. Какие Ваши рекомендации?:")
#
#     return EDITING_COMM_COMM
#
# def edit_comment_text(update: Update, context: CallbackContext):
#     """Сохранение текста комментария."""
#     telegram_user_id = update.message.chat.id
#     user_id = get_user_id(telegram_user_id)
#
#     comment_id = user_data.get('comment_id','')
#     category_id = user_data.get('selected_category',0)
#     name = user_data.get('new_name','')
#     comment = update.message.text.strip()
#
#     dt_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#
#     if user_id != 0:
#         try:
#             execute_query(
#                 "UPDATE comments SET user_id = ?, category_id = ?, name = ?, comment = ?, dt = ? WHERE id = ?",
#                 (user_id, category_id, name, comment, dt_now, comment_id,)
#             )
#             update.message.reply_text(f"Рекомендация успешно изменена! Ее id = {comment_id}")
#         except Exception as e:
#             update.message.reply_text(f"Ошибка при обновлении рекомендации: {e}")
#     else:
#         update.message.reply_text("Рекомендация не обновлена, так как пользователь не найден")
#
#     return ConversationHandler.END
#
# def find(update: Update, context: CallbackContext):
#     """Обработчик команды /find."""
#     update.message.reply_text(f"Введите для поиска id рекомендации или ключевое слово/фразу")
#
#     return FIND_COMM_KWORD
#
# def find_comments(update: Update, context: CallbackContext):
#     """Обработчик поиска комментариев."""
#     telegram_user_id = update.message.chat.id
#     user_id = get_user_id(telegram_user_id)
#
#     if not user_id:
#         update.message.reply_text("Ваш ID не найден в базе данных.")
#         return ConversationHandler.END
#
#     kword = update.message.text.strip()
#
#     # Попробуем сначала найти по ID
#     try:
#         comm = execute_query(
#             "SELECT c.id, c.user_id, users.name AS user_name, c.category_id AS category_id, "
#             "cat.name AS cat_name, c.name, c.comment, c.dt "
#             "FROM comments c "
#             "INNER JOIN users ON c.user_id = users.id "
#             "INNER JOIN categories cat ON c.category_id = cat.id "
#             "WHERE c.id = ?",
#             (kword,), fetchone=True
#         )
#     except Exception as e:
#         update.message.reply_text(f"Ошибка базы данных: {e}")
#         return ConversationHandler.END
#
#     if comm:
#         update.message.reply_text(
#             f"Нашли рекомендацию с ID={kword} по категории '{comm['cat_name']}'\n"
#             f"от {comm['user_name']} для '{comm['name']}'. Вот она:\n"
#             f"{comm['comment']}"
#         )
#         return ConversationHandler.END
#
#     # Если как ID не найдено, пробуем искать как ключевое слово
#     keywords = [kw.strip() for kw in kword.split() if kw.strip()]
#     if not keywords:
#         update.message.reply_text("Вы ввели пустую строку. Попробуйте ещё раз.")
#         return FIND_COMM_KWORD
#
#     # Формируем запрос для поиска по ключевым словам
#     try:
#         query = (
#             "SELECT c.id, c.user_id, users.name AS user_name, c.category_id AS category_id, "
#             "cat.name AS cat_name, c.name, c.comment "
#             "FROM comments c "
#             "INNER JOIN users ON c.user_id = users.id "
#             "INNER JOIN categories cat ON c.category_id = cat.id "
#             "WHERE " +
#             " OR ".join(["c.name LIKE ? OR c.comment LIKE ?" for _ in keywords])
#         )
#         params = [f"%{kw}%" for kw in keywords for _ in range(2)]
#         results = execute_query(query, tuple(params), fetchall=True)
#     except Exception as e:
#         update.message.reply_text(f"Ошибка базы данных: {e}")
#         return ConversationHandler.END
#
#     if not results:
#         update.message.reply_text(f"Не найдено ни одной рекомендации по ключевым словам: '{kword}'.")
#         return FIND_COMM_KWORD
#
#     if len(results) == 1:
#         comm = results[0]
#         update.message.reply_text(
#             f"Нашли одну рекомендацию с ID={comm['id']} по категории '{comm['cat_name']}'\n"
#             f"от {comm['user_name']} для '{comm['name']}'. Вот она:\n"
#             f"{comm['comment']}"
#         )
#         return ConversationHandler.END
#     else:
#         response = "Найдено несколько рекомендаций. Укажите ID нужной:\n"
#         for comm in results:
#             response += f"ID={comm['id']}, Категория: {comm['cat_name']}, Название: {comm['name']}\n"
#         update.message.reply_text(response)
#
#     return FIND_COMM_KWORD
#
# ###############
#     # возвращает id юзера по его telegram_id. Если его не нашли - возвратит 0
# def get_user_id(telegram_id:int) -> int:
#     try:
#         row = execute_query("SELECT * FROM users WHERE telegram_id = ?",(telegram_id,),fetchone=True)
#         if row:
#             return row.id
#         else:
#             return 0
#
#     except e:
#         print(f"Ощибка в базе данных {e}")
#         return 0
#
# # /end
# def end(update: Update, context: CallbackContext):
#     """Обработчик команды /end."""
#     user_id = update.message.chat.id
#     user_data.pop(user_id, None)
#     update.message.reply_text(f"Пока, {user_id}. Диалог завершён.")
#
#     return ConversationHandler.END
#
# # Основная функция для запуска бота
# def main():
#     # Telegram Bot:
#     #   - Для обработки команд используются `CommandHandler`, для ввода текста — `MessageHandler`,
#     #     для кнопок — `CallbackQueryHandler`.
#     # Состояния:
#     #   - Для управления состояниями пользователя используется словарь `user_data`.
#     # Кнопки:
#     #   - Используются кнопки `InlineKeyboardButton` для взаимодействия с пользователем.
#
#     # Регистрируем обработчики
#     updater = Updater(TOKEN)  # Создание объекта Updater
#     dispatcher = updater.dispatcher
#     dispatcher.add_handler(CommandHandler("start", start))
#     dispatcher.add_handler(CommandHandler("end", end))
#     dispatcher.add_handler(CommandHandler("find_cat", find_cat))
#     dispatcher.add_handler(CommandHandler("add_cat", add_cat))
#     dispatcher.add_handler(CommandHandler("edit_cat", edit_cat))
#     dispatcher.add_handler(CommandHandler("find", find))
#     dispatcher.add_handler(CommandHandler("add", add))
#     dispatcher.add_handler(CommandHandler("edit", edit))
#     dispatcher.add_handler(CallbackQueryHandler(button_handler))
#
#     find_cat_handler = ConversationHandler(
#         entry_points=[CommandHandler('find_cat', find_cat)],
#         states={
#             FIND_CAT_KWORD: [MessageHandler(Filters.text & ~Filters.command, find_cat_kword)],
#             FIND_CAT_ACTIONS: [MessageHandler(Filters.text & ~Filters.command, find_cat_actions)]
#         },
#         fallbacks=[CommandHandler('cancel', cancel)],
#     )
#     updater.dispatcher.add_handler(find_cat_handler)
#
#     add_cat_handler = ConversationHandler(
#         entry_points=[CommandHandler('add_cat', add_cat)],
#         states={
#             ADDING_CAT_0: [MessageHandler(Filters.text & ~Filters.command, save_new_category)],
#             ADDING_CAT_ID: [MessageHandler(Filters.text & ~Filters.command, handle_add_cat)],
#             ADDING_CAT_DOING: [MessageHandler(Filters.text & ~Filters.command, button_handler)],
#         },
#         fallbacks=[CommandHandler('cancel', cancel)],
#     )
#     updater.dispatcher.add_handler(add_cat_handler)
#
#     edit_cat_handler = ConversationHandler(
#         entry_points=[CommandHandler('edit_cat', edit_cat)],
#         states={
#             EDITING_CAT_ID: [MessageHandler(Filters.text & ~Filters.command, update_category_name)],
#         },
#         fallbacks=[CommandHandler('cancel', cancel)],
#     )
#     updater.dispatcher.add_handler(edit_cat_handler)
#
#     add_comm_handler = ConversationHandler(
#         entry_points=[CommandHandler('add', add)],
#         states={
#             ADDING_COMM_NAME: [MessageHandler(Filters.text & ~Filters.command, save_comment)],
#             ADDING_COMM_COMM: [MessageHandler(Filters.text & ~Filters.command, save_comment_text)],
#
#         },
#         fallbacks=[CommandHandler('cancel', cancel)],
#     )
#     updater.dispatcher.add_handler(add_comm_handler)
#
#     edit_comm_handler = ConversationHandler(
#         entry_points=[CommandHandler('edit', edit)],
#         states={
#             EDITING_COMM_KWORD:[MessageHandler(Filters.text & ~Filters.command, find_your_comment)],
#             EDITING_COMM_NAME: [MessageHandler(Filters.text & ~Filters.command, edit_comment)],
#             EDITING_COMM_COMM: [MessageHandler(Filters.text & ~Filters.command, edit_comment_text)],
#
#         },
#         fallbacks=[CommandHandler('cancel', cancel)],
#     )
#     updater.dispatcher.add_handler(edit_comm_handler)
#
#     find_comm_handler = ConversationHandler(
#         entry_points=[CommandHandler('find', find)],
#         states={
#             FIND_COMM_KWORD: [MessageHandler(Filters.text & ~Filters.command, find_comments)]
#         },
#         fallbacks=[CommandHandler('cancel', cancel)],
#     )
#     updater.dispatcher.add_handler(find_comm_handler)
#
#     # Запускаем бота
#     updater.start_polling()  # Запуск бота в режиме опроса
#     logger.info("Бот запущен и готов к работе")  # Запись в лог
#     updater.idle()  # Бесконечный цикл до остановки
#
# if __name__ == "__main__":
# #    import asyncio
#     main()
#
