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

from Myproject_bot_lesson51 import command_find_cat
from Myproject_bot_test3 import fname_catid

# Настройка системы логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат записи логов
    level=logging.INFO  # Уровень детализации логов
)
logger = logging.getLogger(__name__)  # Создание логгера для текущего модуля

load_dotenv("config.env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print(TOKEN)

# Категории (используются в нескольких процессах)

START, FIND_CAT, CHOOSE_CAT_ID, FIND_CAT_ONE, FIND_CAT_COM, EDIT_CAT, DEL_CAT = range(1,7)
FIND_KEYWORD, CHOOSE_COMM_ID, FIND_COMM_ONE, DEL_COMM_ONE, ADD_NAME, EDIT_NAME = range(11,16)
ADD_COMMENT, EDIT_COMMENT, RETURN, CANCEL = range(21,24)

COMMENT_LOG_PATH = "comments_log.csv"  # Путь к файлу логов рекомендаций
#ADMIN_IDS = [my_telegram_id]  # Список ID администраторов бота

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
    fname = fname_catid(id)
    keyboard = [
        [InlineKeyboardButton(f"Установить текущей", callback_data="choose_"+str(id))],
        [InlineKeyboardButton(f"Редактировать", callback_data="edit_" + str(id))],
        [InlineKeyboardButton(f"Добавить рядом", callback_data="addnear_" + str(id))],
        [InlineKeyboardButton(f"Добавить подкатегорию", callback_data="addsub_" + str(id))],
        [InlineKeyboardButton(f"Удалить", callback_data="del_" + str(id))]
    ]

    prnt = parent(id)
    if prnt != 0:
        fprnt = fname_catid(prnt)
        keyboard.append([InlineKeyboardButton(f"Выбрать родителя - '{fprnt}'", callback_data="parent_" + str(prnt))])

    if have_subcategory(id):
        keyboard.append( [InlineKeyboardButton(f"Выбрать подкатегорию", callback_data="subcategory_"+str(id))] )

    if have_near(id):
        keyboard.append([InlineKeyboardButton(f"Выбрать рядом", callback_data="near_" + str(id))] )

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup

def keyboard_comment_id(id:int, user_id:int):
    comm = comm_commid()
    keyboard = [
        [InlineKeyboardButton(f"Посмотреть рекомендацию", callback_data="look_"+str(id))],
        [InlineKeyboardButton(f"Добавить рекомендацию", callback_data="add_")],
        [InlineKeyboardButton(f"Вернуться к перечню", callback_data="return_" + str(id))]
    ]
    if comm[3] == user_id:
        keyboard.append([InlineKeyboardButton(f"Изменить наименование", callback_data="editname_" + str(id))])
        keyboard.append([InlineKeyboardButton(f"Изменить рекомендацию", callback_data="editcomm_" + str(id))])
        keyboard.append([InlineKeyboardButton(f"Удалить рекомендацию", callback_data="delcomm_" + str(id))])

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup

def keyboard_comment_choose(context, keyword):

    keyboard = [
                 [InlineKeyboardButton("Возврат", callback_data="return_")]
               ]
    cat_id = context.user_data.get('find_cat_id')
    results = execute_query("SELECT id, name, comment FROM comments WHERE (category_id = ?) and (name LIKE ? or comment LIKE ?)" , (cat_id,keyword,keyword,),
                               fetchall=True)
    for comm in results:
        fname = fname_cat(comm)
        txt = txt +"\n"+f"{fname}"
        keyboard.append([InlineKeyboardButton(f"{fname}", callback_data="comment_" + str(comm[0]))])

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup

def keyboard_choose(data):

    keyboard = []
    txt = ''
    if data.startswith("subcategory_"):
        cat_id = int(data[len("subcategory_"):])
        results = execute_query("SELECT id, name, parent_id FROM categories WHERE parent_id = ?", (cat_id,),
                                   fetchall=True)
        for comm in results:
            fname = fname_cat(comm)
            txt = txt +"\n"+f"{fname}"
            keyboard.append([InlineKeyboardButton(f"{fname}", callback_data="choose_" + str(comm[0]))])

    elif data.startswith("near_"):
        cat_id = int(data[len("near_"):])

        results = execute_query(
            "SELECT c.id as id, c.name as name, c.parent_id as parent_id FROM categories c "
            "INNER JOIN categories cat ON (c.parent_id = cat.parent_id) WHERE cat.id = ?", (cat_id,), fetchall=True)

        for comm in results:
            fname = fname_cat(comm)
            txt = txt +"\n"+f"{fname}"
            keyboard.append([InlineKeyboardButton(f"{fname}", callback_data="choose_" + str(comm[0]))])

    elif data.startswith("choose_"):
        cat_id = int(data.replace("choose_", ""))
        results = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (cat_id,),
                                   fetchall=True)
        for comm in results:
            fname = fname_cat(comm)
            txt = txt +"\n"+f"{fname}"
            keyboard.append([InlineKeyboardButton(f"{fname}", callback_data="choose_" + str(comm[0]))])

    if keyboard.count() != 0:
        reply_markup = InlineKeyboardMarkup(keyboard)
        return reply_markup
    else:
        return None

## 2. Кнопки для отмены
def keyboard_cancel():
    return ReplyKeyboardMarkup(
        [
            [InlineKeyboardButton("Подтвердить", callback_data="yes")],
            [InlineKeyboardButton("Отменить", callback_data="cancel")]
        ],
        one_time_keyboard=True, resize_keyboard=True
    )

## 2. Кнопка для возврата в процесс
def keyboard_return():
    return ReplyKeyboardMarkup(
        [
            [InlineKeyboardButton("Возврат", callback_data="return")]
        ],
        one_time_keyboard=True, resize_keyboard=True
    )

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    telegram_id = user.id
    user_name = user.first_name

    # Проверяем, есть ли пользователь в базе
    users = execute_query("SELECT id, name FROM users WHERE telegram_id = ?", (telegram_id,), fetchone=True)

    txt1 = ""
    dt_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not users:
        # Если пользователь впервые заходит в бота
        user_id = execute_query("INSERT INTO users (telegram_id, name, dt_first, dt_last) VALUES (?, ?, ?, ?)",
                                (telegram_id, user_name, dt_now, dt_now))

        update.message.reply_text(f"Добро пожаловать, {user_name}! Ты первый раз!")
    else:
        # Обновляем время последнего захода
        execute_query("UPDATE users SET dt_last = ? WHERE telegram_id = ?", (dt_now, telegram_id,))
        user_id = execute_query("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,), fetchone=True)[0]

        update.message.reply_text(f"Добро пожаловать, {user_name}! Ты уже бывал!")

    context.user_data['user_id'] = user_id
    context.user_data['user_name'] = user_name
    context.user_data['cat_id'] = 0

    keyboard = [
        [InlineKeyboardButton("Добавить рекомендацию", callback_data='add'),
         InlineKeyboardButton("Изменить свою рекомендацию", callback_data='edit')],
        [InlineKeyboardButton("Операции с категорией", callback_data='find_cat'),
         InlineKeyboardButton("Найти рекомендации", callback_data='find')],
        [InlineKeyboardButton("завершить диалог", callback_data='end')]
    ]
    message_text = (
        "Привет! Выберите действие:\n\n"
        "Доступные команды:\n"
        "/add  - Добавить рекомендацию\n"
        "/edit - Изменить свою рекомендацию\n"
        "/find_cat - Операции с категорией\n"
        "/find - Найти рекомендации\n"
        "/end - завершить диалог"
    )
    update.message.reply_text(
        message_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    log_comment_request(user_id, user_name, 'start', status(START), 'start', 0)
    return START

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    context.user_data['process'] = query.data

    if query.data == 'add' or query.data == 'edit' or query.data == 'find':
        query.message.reply_text("Вначале нужно определиться с категорией!")

    if query.data == 'end':
        query.message.reply_text("Диалог завершён. Для нового диалога отправьте /start.")
        return ConversationHandler.END
    else:
        query.message.reply_text("Введите id или ключевое слово категории:")
        return FIND_CAT

async def add_comment(update, context):
    if update.message.text == "Отказаться":
        return await add_cancel(update, context)
    context.user_data["rec_comment"] = update.message.text
    # Сохраняем рекомендацию в БД тут
    await update.message.reply_text(
        "Ваша рекомендация добавлена! Возвращаемся в главное меню."
    )
    return ConversationHandler.END

async def add_cancel(update, context):
    await update.message.reply_text(
        "Добавление рекомендации отменено. Возвращаемся в главное меню."
    )
    return ConversationHandler.END
#
# async def edit_name_begin(update, context):
#     if update.message.text == "Отказаться":
#         return await edit_cancel(update, context)
#     elif update.message.text == "Изменить наименование":
#         await update.message.reply_text(
#             "Введите новое наименование:",
#             reply_markup=cancel_keyboard()
#         )
#         return EDIT_NAME
#     elif update.message.text == "Оставить прежнее наименование":
#         # Можно загрузить текущее название в user_data
#         return await edit_comment_begin(update, context)
#     else:
#         await update.message.reply_text("Пожалуйста, выберите действие кнопкой.")
#         return EDIT_NAME_BEGIN

# async def edit_name(update, context):
#     if update.message.text == "Отказаться":
#         return await edit_cancel(update, context)
#     context.user_data["rec_name"] = update.message.text
#     return await edit_comment_begin(update, context)
#
# async def edit_comment_begin(update, context):
#     await update.message.reply_text(
#         "Изменить текст рекомендации?",
#         reply_markup=edit_comment_keyboard()
#     )
#     return EDIT_COMMENT
#
# async def edit_comment(update, context):
#     if update.message.text == "Отказаться":
#         return await edit_cancel(update, context)
#     elif update.message.text == "Изменить рекомендацию":
#         await update.message.reply_text(
#             "Введите новый текст рекомендации:",
#             reply_markup=cancel_keyboard()
#         )
#         return EDIT_COMMENT
#     elif update.message.text == "Оставить прежнюю рекомендацию":
#         await update.message.reply_text(
#             "Рекомендация обновлена! Возвращаемся в главное меню."
#         )
#         return ConversationHandler.END
#     else:
#         # Если в состоянии EDIT_COMMENT и получен текст, считаем это новая рекомендация
#         context.user_data["rec_comment"] = update.message.text
#         await update.message.reply_text(
#             "Рекомендация обновлена! Возвращаемся в главное меню."
#         )
#         return ConversationHandler.END
#
# async def edit_cancel(update, context):
#     await update.message.reply_text(
#         "Редактирование рекомендации отменено. Возвращаемся в главное меню."
#     )
#     return ConversationHandler.END

### 3. Реализация процесса выбора категории поиска FIND_FIND_CAT (используем процесс как в /find_cat):
def find_cat_handler(update: Update, context: CallbackContext):
    # Показываем список категорий, если нужно (или ничего не делаем)
    return FIND_CAT

def find_cancel(update: Update, context: CallbackContext):
    update.message.reply_text("Выход в главное меню.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

### 4. FIND_KEYWORD: ввод ключевого слова и выдача рекомендаций
def find_keyword_prompt(update: Update, context: CallbackContext):
    """Получаем ключевое слово от пользователя и предлагаем рекомендации"""
    # Сохраняем ключевое слово
    keyword = update.message.text.strip()

    keyboard = keyboard_comment_choose(context,keyword)
    if keyboard_comment_choose !=

    context.user_data['find_keyword'] = keyword

    # Формируем клавиатуру с рекомендациями
    keyboard = keyboard_comment_id()
    keyboard = [
        [KeyboardButton("Рекомендация1")],
        [KeyboardButton("Рекомендация2")],
        [KeyboardButton("Рекомендация3")],
        [KeyboardButton("Возврат в главное меню")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(
        "Выберите одну из рекомендаций, либо вернитесь в главное меню.",
        reply_markup=reply_markup
    )
    return FIND_KEYWORD

def find_keyword_handler(update: Update, context: CallbackContext):
    """Обработка выбора рекомендации или выхода"""
    keyword = update.message.text

    keyboard = keyboard_comment_choose(context, keyword)
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    update.message.reply_text(
        "Выберите одну из рекомендаций, либо вернитесь в главное меню.",
        reply_markup=reply_markup
    )
    return CHOOSE_COMM_ID

############ конец процедур для /find
def update_comm_name(comm_id, new_name):
    # логика изменения названия рекомендации в БД
    result = execute_query("UPDATE comments SET name = ? WHERE id = ?", (new_name, comm_id,))
    return comm_id

def update_comm_comm(comm_id, new_comm):
    # логика изменения рекомендации в БД
    result = execute_query("UPDATE comments SET comment = ? WHERE id = ?", (new_comm, comm_id,))
    return comm_id

def update_cat_name(cat_id, new_name):
    # логика изменения названия категории в БД
    result = execute_query("UPDATE categories SET name = ? WHERE id = ?", (new_name, cat_id,))
    return cat_id

def add_comm(name, comment, cat_id:int, user_id:int):
    # логика добавления рекомендации в БД
    comm_id = execute_query("INSERT INTO categories (name, comment, cat_id, user_id) VALUES (?, ?, ?, ?)", (name, comment,cat_id, user_id, ))
    return comm_id

def add_category(name, parent_id):
    # логика добавления категории в БД
    cat_id = execute_query("INSERT INTO categories (name, parent_id) VALUES (?, ?)", (name, parent_id,))
    return cat_id

def delete_comment(comm_id):
    # логика удаления рекомендации из БД
    comm = comm_commid(comm_id)
    execute_query("DELETE FROM comments WHERE id = ?", (comm_id,))
    prnt_id = execute_query("SELECT id,name,user_id,category_id,comment FROM comments WHERE category_id = ? ", (comm[3],), fetchone = True)
    return prnt_id

def delete_category(cat_id):
    # логика удаления категории из БД
    prnt_id = execute_query("SELECT parent_id FROM categories WHERE id = ?", (cat_id,), fetchone = True)
    execute_query("DELETE FROM categories WHERE id = ?", (cat_id,))
    return prnt_id

def fname_cat(comm):
    return f"{comm[1]}(id={comm[0]})"

def comm_commid(id:int):
    comm = execute_query("SELECT id, name, user_id, category_id, comment FROM comments WHERE id = ?", (id,),
                            fetchone=True)
    return comm

def fname_commid(id:int):
    comm = comm_commid(id)

    return f"{comm[1]}(id={comm[0]})"

def fname_catid(id:int):
    comm = execute_query("SELECT id, name FROM categories WHERE id = ?", (id,),
                            fetchone=True)
    return f"{comm[1]}(id={comm[0]})"

def parent(id:int):
    comm = execute_query("SELECT parent_id FROM categories WHERE id = ?", (id,),
                         fetchone=True)
    if comm:
        return comm[0]
    else:
        return 0

def have_subcategory(id:int):
    results = execute_query("SELECT id, name, parent_id FROM categories WHERE parent_id = ?", (id,),
                            fetchone=True)
    return bool(results)

def have_near(id:int):
    results = execute_query(
        "SELECT c.id as id, c.name as name, c.parent_id as parent_id FROM categories c "
        "INNER JOIN categories cat ON (c.parent_id = cat.parent_id) WHERE c.id != cat.id and cat.id = ?", (id,), fetchall=True)

    return bool(results)
#############################################################

def find_cat_command(update: Update, context: CallbackContext):
    update.message.reply_text("Введите id или ключевое слово:")

    user_id = context.user_data.get('user_id', 0)
    user_name = context.user_data.get('user_name', '')

    log_comment_request(user_id, user_name, 'ожидаем id/ключ', status(FIND_CAT), 'find_cat_command', '0' )
    return FIND_CAT

def end_command(update: Update, context: CallbackContext):
    update.message.reply_text("Диалог завершён. Для нового диалога отправьте /start.")
    return ConversationHandler.END

def end(update: Update, context: CallbackContext):
    update.message.reply_text("Диалог завершён. Для нового диалога отправьте /start.")
    return ConversationHandler.END

def find_cat_text(update: Update, context: CallbackContext):
    text = update.message.text
    # здесь обработка поиска по text
    update.message.reply_text(f"Вы ввели: {text}")

    keyword = update.message.text.strip()

    user_id = context.user_data.get('user_id', 0)
    user_name = context.user_data.get('user_name', '')

    # keyword = update.message.text.strip()
    log_comment_request(user_id, user_name, f"обрабатываем {text}", status(FIND_CAT), 'find_cat_text', '')

    try:
        cat_id = int(keyword)
        fname = fname_catid(cat_id)
        categories = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (cat_id,), fetchone=True)
        if categories:
            reply_markup = keyboard_for_id(cat_id)
            update.message.reply_text(f"Действия c категорией '{fname}'", reply_markup=reply_markup)
            log_comment_request(user_id, user_name, 'нашли по id', status(FIND_CAT_ONE), 'find_cat_text',
                                str(cat_id))
            return FIND_CAT_ONE
    except ValueError:
        pass

    keywords = [kw.strip() for kw in keyword.split() if kw.strip()]
    if not keywords:
        update.message.reply_text("Cтрока для поиска не годится!. Попробуйте ещё раз.")
        log_comment_request(user_id, user_name, 'пустой ключ', status(FIND_CAT), 'find_cat_text', '')
        return FIND_CAT

    else:
        where_clause = " OR ".join(["name LIKE ?" for _ in keywords])
        query = f"SELECT id, name, parent_id FROM categories WHERE {where_clause}"
        params = [f"%{kw}%" for kw in keywords]

    results = execute_query(query, tuple(params), fetchall=True)

    if not results:
        update.message.reply_text(f"Не найдено ни одной категории по '{keyword}'.")

        log_comment_request(user_id, user_name, f"нет категорий по {keyword}", status(START), 'find_cat_text', '')
        return START

    elif len(results) == 1:
        comm = results[0]
        fname = fname_cat(comm)
        reply_markup = keyboard_for_id(comm[0])
        update.message.reply_text(f"Действия с категорией '{fname}'", reply_markup=reply_markup)

        log_comment_request(user_id, user_name, f"категория {fname}. Действия", status(FIND_CAT_ONE),
                            'find_cat_text', str(comm[0]))
        return FIND_CAT_ONE

    else:
        response = "Выберите категорию:\n"
        keyboard = []
        str_id = ''
        for comm in results:
            fname = fname_cat(comm)
            keyboard.append([InlineKeyboardButton(f"{fname}", "choose_"+str(comm[0]))])
            str_id = str_id + " " + f"{comm[0]}"

        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(response, reply_markup=reply_markup)

        log_comment_request(user_id, user_name, f"несколько категорий. На выбор", status(CHOOSE_CAT_ID),
                            'find_cat_text', str_id)

        return CHOOSE_CAT_ID

# обработчик состояния CHOOSE_COMM_ID
def handle_comm_id(update: Update, context: CallbackContext) -> int:

    query = update.callback_query
    query.answer()

    data = query.data
    query.message.reply_text(f"handle_comm_id data = {data}")
    if data.startswith("comment_"):
        comm_id = int(data[len("comment_"):])
        fname = comm_commid(comm_id)
        user_id = context.user_data.get('user_id')
        reply_markup = keyboard_comment_id(comm_id,user_id)
        query.message.reply_text(f"Действия с рекомендацией '{fname}'", reply_markup=reply_markup)

        return FIND_COMM_ONE

    else:
        query.message.reply_text("Неизвестное действие.")
        return ConversationHandler.END

# обработчик состояния CHOOSE_CAT_ID
def handle_cat_id(update: Update, context: CallbackContext) -> int:

    query = update.callback_query
    query.answer()

    data = query.data
    query.message.reply_text(f"handle_cat_id data = {data}")
    if data.startswith("choose_"):
        cat_id = int(data[len("choose_"):])
        fname = fname_catid(cat_id)
        reply_markup = keyboard_for_id(cat_id)
        query.message.reply_text(f"Действия с категорией '{fname}'", reply_markup=reply_markup)

        return FIND_CAT_ONE

    elif data.startswith("subcategory_") or data.startswith("near_"):

        reply_markup = keyboard_choose(data)
        query.message.reply_text(f"Выберите категорию", reply_markup=reply_markup)

        return CHOOSE_CAT_ID

    else:
        query.message.reply_text("Неизвестное действие.")
        return ConversationHandler.END

def find_cat_one(update: Update, context: CallbackContext) -> int:

    user_id = context.user_data.get('user_id', 0)
    user_name = context.user_data.get('user_name', '')

    query = update.callback_query
    query.answer()
    data = query.data

    # Обработка редактирования, добавления, удаления
    if data.startswith("edit_") or data.startswith("addnear_") or data.startswith("addsub_"):
        if data.startswith("edit_"):
            action, cat_id = "edit", int(data.replace("edit_", "", 1))
        elif data.startswith("addnear_"):
            action, cat_id = "addnear", int(data.replace("addnear_", "", 1))
        else:
            action, cat_id = "addsub", int(data.replace("addsub_", "", 1))

        context.user_data['edit_action'] = action
        context.user_data['edit_id'] = cat_id
        query.edit_message_text(f"Введите новое название категории:")
        # Кнопки 'Сохранить' и 'Отказаться' будут после ввода названия
        return EDIT_CAT

    elif data.startswith("del_"):
        cat_id = int(data.replace("del_", "", 1))
        context.user_data['del_id'] = cat_id
        keyboard = [
            [InlineKeyboardButton("Подтвердить", callback_data="confirm_del_cat")],
            [InlineKeyboardButton("Отказаться", callback_data="cancel_del_cat")]
        ]
        query.edit_message_text(
            f"Вы уверены, что хотите удалить эту категорию?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return DEL_CAT

    if data.startswith("choose_"):
        # Сохраняем выбранную категорию
        cat_id = int(data.replace("choose_", ""))
        context.user_data['find_cat_id'] = cat_id

        process = context.user_data.get("process")
        if process == "add":
            # Автоматический переход к вводу наименования рекомендации
            query.edit_message_text("Введите наименование рекомендации в выбранной категории:")
            return ADD_NAME
        elif process == "edit" or process == "find":
            # Автоматический переход к вводу ключевого слова
            query.edit_message_text("Введите ключевое слово для поиска рекомендации в выбранной категории:")
            return FIND_KEYWORD
        else:
            return START

    elif data.startswith("cancel"):
        query.edit_message_text("Поиск отменён. Возвращаемся в главное меню.")
        return ConversationHandler.END
    # else:
    #     query.edit_message_text("Выберите категорию для поиска.")
    #     return FIND_CAT
    #
    #
    # elif data.startswith("choose_"):
    #     if data.startswith("choose_"):
    #         cat_id = int(data[len("choose_"):])
    #     else:
    #         cat_id = int(data[len("edit_"):])
    #
    #     context.user_data['cat_id'] = cat_id
    #
    #     query.message.reply_text("Процесс завершен. Возвращаемся в начало.")
    #     keyboard = [
    #         [InlineKeyboardButton("FindCat", callback_data='find_cat')],
    #         [InlineKeyboardButton("End", callback_data='end')]
    #     ]
    #     message_text = (
    #         "Выберите действие:\n"
    #         "Доступные команды:\n"
    #         "/find_cat - найти кота (или используйте кнопку)\n"
    #         "/end - завершить диалог (или используйте кнопку)"
    #     )
    #     query.message.reply_text(
    #         message_text,
    #         reply_markup=InlineKeyboardMarkup(keyboard)
    #     )
    #
    #     return START

    elif data.startswith("subcategory_") or data.startswith("near_"):

        #query.message.reply_text(f"Выбрали  {data}")
        # После этого возвращаем меню подкатегорий
        reply_markup = keyboard_choose(data)

        query.message.reply_text(
            f"Выберите категорию:",
            reply_markup=reply_markup
        )

        log_comment_request(user_id, user_name, f"выбор из {data}", status(CHOOSE_CAT_ID),
                            'find_cat_one', data)
        return CHOOSE_CAT_ID

    else:
        return unknown(update, context)

def find_comm_one(update: Update, context: CallbackContext) -> int:

    user_id = context.user_data.get('user_id', 0)
    user_name = context.user_data.get('user_name', '')

    query = update.callback_query
    query.answer()
    data = query.data

    # Обработка редактирования, добавления, удаления
    if data.startswith("lookcomm_") or data.startswith("editname_") or data.startswith("editcomm_") or data.startswith("delcomm_"):
        if data.startswith("delcomm_"):
            action, comm_id = "delcomm", int(data.replace("delcomm_", "", 1))

            keyboard = keyboard_cancel()
            fname = fname_commid(comm_id)
            query.edit_message_text(
                f"Хотите удалить рекомендацию {fname}?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            context.user_data['comm_id'] = comm_id
            return DEL_COMM

        elif data.startswith("editname_"):
            action, comm_id = "editname", int(data.replace("editname_", "", 1))

            context.user_data['comm_id'] = comm_id

            fname = fname_commid(comm_id)
            query.edit_message_text(f"Введите новое название рекомендации {fname}")
            # Кнопки 'Сохранить' и 'Отказаться' будут после ввода названия
            return EDIT_COMM_NAME

        elif data.startswith("editcomm_"):
            action, comm_id = "editcomm", int(data.replace("editcomm_", "", 1))

            context.user_data['comm_id'] = comm_id

            comm = comm_commid(comm_id)
            fname = fname_commid(comm_id)
            query.edit_message_text(f"Вот рекомендация, которую вы дали по {fname}")

            fname = comm[3]
            query.edit_message_text(f"{fname}")

            query.edit_message_text(f"\nВведите исправленную рекомендацию по {fname}")
            # Кнопки 'Сохранить' и 'Отказаться' будут после ввода рекомендации
            return EDIT_COMM_COMM

        else:
            action, comm_id = "lookcomm", int(data.replace("lookcomm_", "", 1))

            context.user_data['comm_id'] = comm_id

            comm = comm_commid(comm_id)
            fname = fname_catid(comm_id[3])
            query.edit_message_text(f"Введите наименование рекомендации в категории {fname}")
            fname = comm[4]
            query.edit_message_text(f"{fname}")

            query.edit_message_text(f"Введите исправленную рекомендацию по {fname}")
            # Кнопки 'Сохранить' и 'Отказаться' будут после ввода рекомендации
            return EDIT_COMM_COMM

    elif data.startswith("addcomm_")
        action, comm_id = "addcomm", int(data.replace("addcomm_", "", 1))
        context.user_data['comm_id'] = comm_id

        comm = comm_commid(comm_id)
        fname = fname_catid(comm_id[3])
        query.edit_message_text(f"Введите наименование рекомендации в категории {fname}")

        return ADD_COMM_NAME

    else:        #return_

        return CHOOSE_CAT_ID


def return_handler(update: Update, context: CallbackContext) -> int:
    process = context.user_data.get('process')
    status = context.user_data.get('status')

    ret_status = START
    if status == FIND_KEYWORD:
        ret_status = CHOOSE_CAT_ID #    cat_id
    elif status == CHOOSE_COMM_ID:
        ret_status = FIND_KEYWORD  # keyword
    elif status == FIND_COMM_ONE:
        ret_status = CHOOSE_CAT_ID  # comm_id/keyword
    elif status == DEL_COMM_ONE:
        ret_status = FIND_KEYWORD  # keyword
    elif status in (ADD_NAME, ADD_COMMENT, EDIT_NAME, EDIT_COMMENT):
        ret_status = FIND_COMM_ONE  # comm_id

    return ret_status

def find_cat_one(update: Update, context: CallbackContext) -> int:

    user_id = context.user_data.get('user_id', 0)
    user_name = context.user_data.get('user_name', '')

    query = update.callback_query
    query.answer()
    data = query.data

    # Обработка редактирования, добавления, удаления
    if data.startswith("edit_") or data.startswith("addnear_") or data.startswith("addsub_"):
        if data.startswith("edit_"):
            action, cat_id = "edit", int(data.replace("edit_", "", 1))
        elif data.startswith("addnear_"):
            action, cat_id = "addnear", int(data.replace("addnear_", "", 1))
        else:
            action, cat_id = "addsub", int(data.replace("addsub_", "", 1))

        context.user_data['edit_action'] = action
        context.user_data['edit_id'] = cat_id
        query.edit_message_text(f"Введите новое название категории:")
        # Кнопки 'Сохранить' и 'Отказаться' будут после ввода названия
        return EDIT_CAT

    elif data.startswith("del_"):
        cat_id = int(data.replace("del_", "", 1))
        context.user_data['del_id'] = cat_id
        keyboard = [
            [InlineKeyboardButton("Подтвердить", callback_data="confirm_del_cat")],
            [InlineKeyboardButton("Отказаться", callback_data="cancel_del_cat")]
        ]
        query.edit_message_text(
            f"Вы уверены, что хотите удалить эту категорию?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return DEL_CAT

    if data.startswith("choose_"):
        # Сохраняем выбранную категорию
        cat_id = int(data.replace("choose_", ""))
        context.user_data['find_cat_id'] = cat_id

        process = context.user_data.get("process")
        if process == "add":
            # Автоматический переход к вводу наименования рекомендации
            query.edit_message_text("Введите наименование рекомендации в выбранной категории:")
            return ADD_NAME
        elif process == "edit" or process == "find":
            # Автоматический переход к вводу ключевого слова
            query.edit_message_text("Введите ключевое слово для поиска рекомендации в выбранной категории:")
            return FIND_KEYWORD
        else:
            return START

    elif data.startswith("cancel"):
        query.edit_message_text("Поиск отменён. Возвращаемся в главное меню.")
        return START

    elif data.startswith("subcategory_") or data.startswith("near_"):

        #query.message.reply_text(f"Выбрали  {data}")
        # После этого возвращаем меню подкатегорий
        reply_markup = keyboard_choose(data)

        query.message.reply_text(
            f"Выберите категорию:",
            reply_markup=reply_markup
        )

        log_comment_request(user_id, user_name, f"выбор из {data}", status(CHOOSE_CAT_ID),
                            'find_cat_one', data)
        return CHOOSE_CAT_ID

    else:
        return unknown(update, context)

def edit_cat(update: Update, context: CallbackContext):
    # Получить введённое название
    text = update.message.text
    if not text or not text.strip():
        update.message.reply_text("Пожалуйста, введите название категории.")
        return EDIT_CAT

    context.user_data['new_cat_name'] = text

    keyboard = [
        [InlineKeyboardButton("Сохранить", callback_data="save_edit")],
        [InlineKeyboardButton("Отказаться", callback_data="cancel_edit")]
    ]
    update.message.reply_text(
        f"Наименование: <b>{text}</b>\nСохранить?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return EDIT_CAT  # Ожидать нажатия на кнопки

def edit_cat_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    action = context.user_data.get('edit_action')
    cat_id = context.user_data.get('edit_id')
    text = context.user_data.get('new_cat_name')

    if query.data == "save_edit":
        if action == "edit":
            # обновить имя категории
            cat_id = update_cat_name(cat_id, text)

        elif action == "addnear":
            prnt_id = parent(cat_id)
            cat_id = add_category(text, prnt_id)

        elif action == "addsub":
            cat_id = add_category(text, cat_id)

        # После операции – переход обратно к CHOOSE_CAT_ID для нужного id
        query.edit_message_text("Изменения сохранены.")

        # Показываем кнопки выбора
        fname = fname_catid(cat_id)
        query.message.reply_text( f"{fname}",
        reply_markup=keyboard_choose(f"choose_{cat_id}")
        )
        return CHOOSE_CAT_ID

    elif query.data == "cancel_edit":
        # Возврат без изменений
        query.edit_message_text("Операция отменена.")
        cat_id = context.user_data.get('edit_id')
        fname = fname_catid(cat_id)

        query.message.reply_text(
            f"{fname}",
            reply_markup=keyboard_choose(f"choose_{cat_id}")
        )
        return CHOOSE_CAT_ID

    return ConversationHandler.END

def del_cat(update: Update, context: CallbackContext):
    if update.callback_query:
        query = update.callback_query
        if query.data == "confirm_del_cat":
            id = context.user_data.get("cat_del_id")
            parent_id = parent(id)
            delete_category(id) # реализуйте сами
            if parent_id > 0:
                fname = fname_catid(parent_id)
                query.edit_message_text(
                    f"Родитель:{fname}",
                    reply_markup=keyboard_choose(f"choose_{parent_id}")
                )
                return CHOOSE_CAT_ID
            else:
                query.edit_message_text(
                    "Главные категории",
                    reply_markup=keyboard_choose("subcategory_0")
                )
                return CHOOSE_CAT_ID
        elif query.data == "cancel_del_cat":
            cat_id = context.user_data.get("cat_del_id")
            fname = fname_catid(cat_id)
            query.edit_message_text(
                f"Удаление {fname} отменено.",
                reply_markup=keyboard_choose(f"choose_{cat_id}")
            )
            return CHOOSE_CAT_ID

#обработчик состояния CANCEL
def cancel(update: Update, context: CallbackContext) -> int:

    update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return START

def unknown(update: Update, context: CallbackContext):
    def unknown(update: Update, context: CallbackContext):
        if update.callback_query:
            query = update.callback_query
            data = query.data
            query.edit_message_text(f"Извините, я не понял команду {data}")
            keyboard = [
                [InlineKeyboardButton("FindCat", callback_data='find_cat')],
                [InlineKeyboardButton("End", callback_data='end')]
            ]
            query.message.reply_text(
                "Выберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            data = update.message.text if update.message else ""
            update.message.reply_text(f"Извините, я не понял команду {data}")
            keyboard = [
                [InlineKeyboardButton("FindCat", callback_data='find_cat')],
                [InlineKeyboardButton("End", callback_data='end')]
            ]
            update.message.reply_text(
                "Выберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        return START

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            START: [
                CallbackQueryHandler(button_handler, pattern="^(find_cat|end)$")
            ],
            FIND_CAT: [
                MessageHandler(Filters.text & ~Filters.command, find_cat_text),
                CommandHandler("end", end_command),
            ],
            CHOOSE_CAT_ID: [
                CallbackQueryHandler(handle_cat_id, pattern="^(choose_|edit_|subcategory_|near_)\d+$")
            ],
            FIND_CAT_ONE: [
                CallbackQueryHandler(find_cat_one, pattern="^(choose_|edit_|subcategory_|near_)\d+$")
            ],
            EDIT_CAT: [
                MessageHandler(Filters.text & ~Filters.command, edit_cat),
                CallbackQueryHandler(edit_cat_callback, pattern="^(save_edit|cancel_edit)$"),
            ],
            DEL_CAT: [
                CallbackQueryHandler(del_cat, pattern="^(confirm_del_cat|cancel_del_cat)$"),
            ],
            CANCEL: [
                CallbackQueryHandler(cancel, pattern=r"^cancel$")
            ],

            # ADD_FIND_CAT: [
            #     MessageHandler(Filters.text & ~Filters.command, add_find_cat),
            #     CommandHandler("end", end_command),
            # ],
            # ADD_NAME: [MessageHandler(Filters.text & ~Filters.command, add_name)],
            CHOOSE_COMM_ID: [
                CallbackQueryHandler(handle_comm_id, pattern="^(comment_)\d+$")]
            FIND_COMM_ONE: [
                CallbackQueryHandler(find_comm_one, pattern="^(choose_|edit_|subcategory_|near_)\d+$")],

            ADD_COMMENT: [MessageHandler(Filters.text & ~Filters.command, add_comment)],

            # EDIT_FIND_CAT: [
            #     MessageHandler(Filters.text & ~Filters.command, edit_find_cat),
            #     CommandHandler("end", end_command),
            # ],
            EDIT_NAME: [MessageHandler(Filters.text & ~Filters.command, edit_name)],
            EDIT_COMMENT: [MessageHandler(Filters.text & ~Filters.command, edit_comment)],

            # FIND_FIND_CAT: [
            #     MessageHandler(Filters.text | Filters.command, find_find_cat_start)
            # ],
            FIND_KEYWORD: [
                MessageHandler(Filters.text & ~Filters.command, find_keyword_handler),
            ],
            RETURN: [
                MessageHandler(Filters.text & ~Filters.command, return_handler),
            ],
        },
        fallbacks=[CommandHandler("end", end_command),
                   MessageHandler(Filters.command, unknown)
                   ],
        allow_reentry=True
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("comments_stats", comments_stats))
    dispatcher.add_handler(CommandHandler('log_start', log_start))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

