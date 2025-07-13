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
from array import ArrayType
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

# Константы для состояния в ConversationHandler
CHOOSE_ACTION, CHOOSE_CATEGORY = range(2)
# Статусы для ConversationHandler
SELECT_CATEGORY, CHOOSE_ACTION, ADD_SUBCATEGORY, ADD_CATEGORY = range(4)


current_category_id = 0
DB_path = "comments.db"
conn = sqlite3.connect("comments.db")
cursor = conn.cursor()

class Categories():
    def __init__(self):
        cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            active BOOLEAN, 
            parent_id INTEGER 
        )
        ''')
        conn.commit()

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

class Users():
    def __init__(self):
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            name TEXT NOT NULL,
            dt_first DATETIME NOT NULL,         # дата и время когда зарегистрировался
            dt_last DATETIME NOT NULL,          # дата и время последнего входа
            comment TEXT,                       # комментарий
            last_category_id INTEGER DEFAULT 0,  # последняя выбранная категория
            last_keyword  TEXT DEFAULT '',       # последняя выбранная ключевая фраза
            result TEXT DEFAULT 'random',        #last - последние, first - первые, random - рандомные
            max_comments INTEGER DEFAULT 0,      # макс. количество рекомендаций при поиске (0 - все)
       )''')

        self.categories = Categories()

    # # возвращает id юзера по его telegram_id. Если его не нашли - возвратит 0
    # def id_user(self, telegram_id:int) -> bool:
    #     try:
    #         cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    #         row = cursor.fetchone()
    #         if row:
    #             return row.id
    #         else:
    #             return 0
    #     except e:
    #         print(f"Ощибка в базе данных {e}")
    #         return 0

    # возвращает id юзера по его telegram_id. Если его не нашли - возвратит 0
    def get_user_id(self, telegram_id:int) -> int:
        try:
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
            if row:
                return row.id
            else:
                return 0

        except e:
            print(f"Ощибка в базе данных {e}")
            return 0

    def get_user_find_parametrs(self, user_id:int):
        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {'max_comments':max_comments,'category_id':category_id,'result':result,'keyword':keyword}
            else:
                return {}

        except e:
            print(f"Ощибка в базе данных {e}")
            return  {}

    def change_find_parametr(self, user_id:int, param:str, value:str) -> str:
        if param in ("max_comments","category_id"):
            try:
                m = int( value )
            except:
                txt = "Введите число, а не строку!"
                return txt
        elif param == "result":
            val = value.strip().lower()
            if not (val in ('last','first''random')):
                txt = "Введите last или first или random"
                return txt

        try:
            txt = "Успех!"
            if param == "max_comments":
                cursor.execute("UPDATE Users SET max_comments = ? WHERE id = ?", (m, user_id,))
                conn.commit()
            elif param == "last_category_id":
                cursor.execute("UPDATE Users SET last_category_id = ? WHERE id = ?", (m, user_id,))
                conn.commit()
            elif param == "result":
                cursor.execute("UPDATE Users SET result = ? WHERE id = ?", (value.strip().lower(), user_id,))
                conn.commit()
            elif param == "last_keyword":
                cursor.execute("UPDATE Users SET last_keyword = ? WHERE id = ?", (value, user_id,))
                conn.commit()
            else:
                txt = f"{param} указан некорректно. Нужно указать max_comments или last_category_id или result или last_keyword"

        except e:
            txt = f"Проблема с базой данных {e}"

        return txt

    def append_user(self, telegram_id:int, name:str) -> int:
        try:
            id = self.get_user_id(telegram_id)

            if id != 0:
                return id
            else:
                cursor.execute("INSERT INTO users (telegram_id, name, dt_first, dt_last ) "
                               "VALUES (?, ?, ?, ?)",
                               (telegram_id, name, datetime.now().isoformat(), datetime.now().isoformat()))
                conn.commit()
                id = cursor.lastrowid
                return id

        except e:
            print(f"Ощибка в базе данных {e}")
            return 0

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
        conn.commit()

        self.users = Users()

    def add_comment(self,user_id:int,category_id:int,name:str,comment:str):
        cursor.execute("INSERT INTO comments (user_id,category_id,name,comment,dt) VALUES (?, ?, ?, ?, ?)",
                       (user_id, category_id, name, comment, datetime.now().isoformat(), ))
        conn.commit()

    def find_comments(self,user_id:int,from_user_id:int=0) -> str:

        if from_user_id > 0 and self.users.is_exist_user(from_user_id):
            # Создаем временную таблицу для параметров
            cursor.execute("""
                DROP TABLE IF EXISTS temp_params_from_user;
                CREATE TEMP TABLE temp_params_from_user (from_user_id INTEGER)
                """)
            cursor.execute("INSERT INTO temp_params_from_user (from_user_id) VALUES (?)", (from_user_id,))

            # Используем временную таблицу в запросе
            cursor.execute("""
            CREATE VIEW IF NOT EXISTS from_comments AS
            SELECT c.* FROM comments c, temp_params_from_user p WHERE c.user_id = p.from_user_id
            """)
        else:
            cursor.execute("""
             CREATE VIEW IF NOT EXISTS from_comments AS
             SELECT c.* FROM comments c
             """)

        # получаем параметры поиска result и max_comments потом - last_category_id,last_keyword
        params = self.users.get_user_find_parametrs(user_id)
        max_comments = params.get('max_comments', 0)
        result = params.get('result', 'random')

        if max_comments > 0 and (result == 'first' or result == 'last'):
            # Создаем временную таблицу для параметров
            cursor.execute("""
                DROP TABLE IF EXISTS temp_params_max_comments;
                CREATE TEMP TABLE temp_params_max_comments (max_comments INTEGER)
            """)

            cursor.execute("INSERT INTO temp_params_max_comments (max_comments) VALUES (?)", (max_comments,))

            # Используем временную таблицу в запросе
            if result == 'first':
              cursor.execute("""
              CREATE VIEW IF NOT EXISTS max_comments AS
              SELECT c.* FROM from_comments c, temp_params_max_comments p ORDER BY dt ASC LIMIT p.max_comments
              """)
            else:
                cursor.execute("""
                 CREATE VIEW IF NOT EXISTS max_comments AS
                 SELECT c.* FROM from_comments c, temp_params_max_comments p ORDER BY dt DSC LIMIT p.max_comments
                 """)

        else:
            cursor.execute("""
               CREATE VIEW IF NOT EXISTS max_comments AS
               SELECT c.* FROM from_comments c
               """)

        #получаем параметры поиска last_category_id
        last_category_id = params.get('last_category_id',0)

        if last_category_id > 0 :
            #Получаем массив с подкатегориями
            arr_category_id = self.categories.tree_categories(last_category_id)

            # Создаем временную таблицу для параметров
            cursor.execute("""
                 DROP TABLE IF EXISTS temp_params_category_id;
                 CREATE TEMP TABLE temp_params_category_id (category_id INTEGER)
             """)
            for cat_id in arr_category_id:
                cursor.execute("INSERT INTO temp_params_category_id (category_id) VALUES (?)", (cat_id,))

            # Используем временную таблицу в запросе
            cursor.execute("""
             CREATE VIEW IF NOT EXISTS category_id AS
             SELECT c.* FROM max_comments c
             INNER JOIN temp_params_category_id p ON c.category_id = p.category_id
             """)
        else:
            cursor.execute("""
              CREATE VIEW IF NOT EXISTS category_id AS
              SELECT c.* FROM max_comments c
              """)

        # получаем параметры поиска keyword
        keyword = params.get('last_keyword', '')
        arr_keyword = []
        arr_keyword1 = keyword.split()
        for kword1 in arr_keyword1:
            arr_keyword2 = kword1.split(';')
            for kword2 in arr_keyword2:
                arr_keyword3 = kword2.split(',')
               for kword3 in arr_keyword3:
                   if kword3.count()>0:
                        arr_keyword.append(kword3)

        if len(arr_keyword) > 0:
            len_arr = len(arr_keyword)
            # Создаем временную таблицу для параметров
            cursor.execute("""
                  DROP TABLE IF EXISTS temp_params_keyword;
                  CREATE TEMP TABLE temp_params_keyword (keyword TEXT, len_arr INT)
              """)
            for kword in arr_keyword:
                cursor.execute("INSERT INTO temp_params_category_id (keyword,len_arr) VALUES (?,?)", (kword,len_arr))

            # Используем временную таблицу в запросе: вначале создаем временную таблицу с id тех рекомендаций,
            # в которых есть все слова без разделителей ';',',',' '
            cursor.execute("""
               CREATE VIEW IF NOT EXISTS comments_id_kword AS
               SELECT c.id AS id, COUNT(p.keyword) AS cnt, MAX(p.len_arr) AS len_arr FROM category_id c
               INNER JOIN temp_params_keyword p ON (c.name || ' ' || c.comment LIKE '%' || p.keyword || '%') 
               GROUP BY
                    c.id 
               HAVING 
                    HAVING COUNT(p.keyword) = MAX(p.len_arr)
               """)
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS comments_kword AS
                SELECT c.* FROM category_id c
                INNER JOIN comments_id_kword c_id ON (c.id = c_id.id)
                 """)
        else:
            cursor.execute("""
                CREATE VIEW IF NOT EXISTS comments_kword AS
                SELECT c.* FROM category_id c
                """)
        cursor.execute("""
              SELECT c.user_id, c.category_id, c.name AS name, c.comment AS comment, c.dt AS dat, usr.name AS user, usr.comment AS about_user, cat.name AS category FROM comments_kword c
                    INNER JOIN user usr ON (c.user_id = usr.id)
                    INNER JOIN categories cat ON (c.category_id = cat.id)
               """)
        rows = cursor.fetchall()
        if max_comments > 0:
            if max_comments > len(rows):
                max_comments = len(rows)
        else:
            max_comments = len(rows)

        i = 0
        arr_int = []
        while i < max_comments:
            arr_int.append(i)
            i = i + 1

        # Осталось учесть случай когда result='random'
        if result == 'random':
            random.shuffle(arr_int)

        txt = ""
        for i in range(len(arr_int)):
            txt = txt + f"{rows[arr_int[i]]}" + "\n"

        return txt

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

# Заполнение таблицы categories
def initialize_categories():
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

    # Состояния для взаимодействия
    STATE_ADD_CAT = "STATE_ADD_CAT"
    STATE_FIND_CAT = "STATE_FIND_CAT"
    STATE_ADD_COMMENT = "STATE_ADD_COMMENT"
    STATE_FIND_COMMENT = "STATE_FIND_COMMENT"
    STATE_EDIT_COMMENT = "STATE_EDIT_COMMENT"

    # Хранилище временных данных
    user_data = {}

    # Команда /start
    def start(update: Update, context: CallbackContext) -> None:
        update.message.reply_text(
            "Добро пожаловать! Вот доступные команды:\n"
            "/add_cat - Добавить категорию\n"
            "/find_cat - Найти категорию\n"
            "/add - Добавить рекомендацию\n"
            "/find - Найти рекомендации"
        )

initialize_categories()
comments = Comments()

# Обработчик команды /start
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    telegram_id = user.id
    name = user.first_name

    # Проверяем, есть ли пользователь в базе
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user_data = cursor.fetchone()

    if not user_data:
        # Если пользователь впервые заходит в бота
        dt_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO users (telegram_id, name, dt_first, dt_last) VALUES (?, ?, ?, ?)',
                       (telegram_id, name, dt_now, dt_now))
        conn.commit()
        # update.message.reply_text(f"Добро пожаловать, {name}!")
    else:
        # Обновляем время последнего захода
        cursor.execute('UPDATE users SET dt_last = ? WHERE telegram_id = ?', (datetime.now(), telegram_id))
        conn.commit()

        # last_category_id = user_data[5]
        # if last_category_id:
        #     cursor.execute('SELECT name FROM categories WHERE id = ?', (last_category_id,))
        #     category_name = cursor.fetchone()[0]
        #     update.message.reply_text(f"Привет, {name}! Последний раз вы заходили {user_data[4]}. "
        #                               f"Ваша последняя выбранная категория: {category_name}.")
        # else:
        #     update.message.reply_text(f"Привет, {name}! Последний раз вы заходили {user_data[4]}. "
        #                               f"У вас пока нет выбранной категории.")


    update.message.reply_text(
        f"Добро пожаловать, {name}! Вот доступные команды:\n"
        "/add_cat - Добавить категорию\n"
        "/find_cat - Найти категорию\n"
        "/add - Добавить рекомендацию\n"
        "/find - Найти рекомендации"
    )

# Команда /add_cat
def add_cat(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Введите ID категории:")

    # Сохраняем состояние
    user_data[update.message.chat_id] = {"state": STATE_ADD_CAT}

# Обработчик ввода ID категории для /add_cat
def handle_add_cat(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    state = user_data.get(chat_id, {}).get("state")

    if state == STATE_ADD_CAT:
        try:
            category_id = int(update.message.text)
            cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
            category = cursor.fetchone()

            if category:
                # Формируем кнопки
                keyboard = [
                    [InlineKeyboardButton("Добавить подкатегорию", callback_data=f"add_subcat_{category_id}")],
                    [InlineKeyboardButton("Добавить категорию", callback_data=f"add_cat_{category_id}")],
                    [InlineKeyboardButton("Возврат", callback_data="return_add_cat")],
                    [InlineKeyboardButton("Конец", callback_data="end")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
            else:
                update.message.reply_text("Категория с таким ID не найдена. Попробуйте снова.")
        except ValueError:
            update.message.reply_text("Введите корректный ID категории.")

# Обработчик нажатий кнопок
def button_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data

    if data.startswith("add_subcat_"):
        category_id = int(data.split("_")[2])
        query.edit_message_text(f"Введите имя новой подкатегории для категории c ID={category_id}:")

        # Сохраняем состояние
        user_data[query.message.chat_id] = {"state": "add_subcategory", "category_id": category_id}

    elif data.startswith("add_cat_"):
        category_id = int(data.split("_")[2])
        query.edit_message_text(f"Введите имя новой категории, смежной с категорией с ID={category_id}:")

        # Сохраняем состояние
        user_data[query.message.chat_id] = {"state": "add_category", "category_id": category_id}

    elif data == "return_add_cat":
        add_cat(update.callback_query, context)

    elif data == "end":
        #query.edit_message_text("Возврат в главное меню. Введите /start для начала.")
        start(update.callback_query, context)

# Обработчик ввода имени подкатегории или категории
def handle_subcategory_or_category_name(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    state_data = user_data.get(chat_id, {})

    if state_data.get("state") == "add_subcategory":
        category_id = state_data.get("category_id")
        subcategory_name = update.message.text

        cursor.execute("INSERT INTO categories (name, active, parent_id) VALUES (?, ?, ?)",
                       (subcategory_name, True, category_id))
        conn.commit()
        update.message.reply_text(f"Подкатегория '{subcategory_name}' добавлена!")

    elif state_data.get("state") == "add_category":
        category_id = state_data.get("category_id")
        category_name = update.message.text

        cursor.execute("SELECT parent_id FROM categories WHERE id = ?", (category_id,))
        parent_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO categories (name, active, parent_id) VALUES (?, ?, ?)",
                       (category_name, True, parent_id))
        conn.commit()
        update.message.reply_text(f"Категория '{category_name}' добавлена!")

    # Сброс состояния
    user_data[chat_id] = {}

def main() -> None:
    # Создаем бота
    updater = Updater("YOUR_BOT_TOKEN")

    # Регистрируем обработчики
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("add_cat", add_cat))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_add_cat))
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_subcategory_or_category_name))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()