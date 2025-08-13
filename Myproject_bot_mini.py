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

import json

from Myproject_bot_test3 import fname_cat
#from parser.test20_wb_parsing import options

DB_path = "comments.db"

# Настройка системы логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат записи логов
    level=logging.INFO  # Уровень детализации логов
)
logger = logging.getLogger(__name__)  # Создание логгера для текущего модуля

load_dotenv("config.env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
COMMENT_LOG_PATH = "comments_log.csv"  # Путь к файлу логов рекомендаций
print(TOKEN)

class FSM_proc:
    def __init__(self,user_id:int,user_name:str,telegram_id:int=0):
        self.user_id = user_id
        self.user_name = user_name
        self.telegram_id = telegram_id
        self.process = None
        self.status = None
        self.state_status = None
        self.data = None
        self.dict = {}
        self.stack = []
        self.processes = {}  # {process: [status1, status2, ...]}
        self.processes_name = {}
        self.state_vars = {}  # {status: [var1, var2]}
        self.state_forward_mooving = {}  # {status: [next_status1, ...]}

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

        # cursor.execute('''DROP TABLE IF EXISTS comments''')
        # conn.commit()
        # conn.close()
        #
        # conn = sqlite3.connect(DB_path)  # Создаём новое соединение в этом потоке
        # cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                category_id INTEGER,
                name TEXT,
                comment TEXT,
                dt DATETIME 
            )''')
        conn.commit()
        conn.close()

        # Инициализация файла логов

        if not os.path.exists(COMMENT_LOG_PATH):
            # Создание нового файла с заголовками
            with open(COMMENT_LOG_PATH, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['timestamp', 'process', 'user_id', 'status', 'state', 'data', 'cat_id', 'comm_id',
                                 'len_stack','comment'])

        else:
            # Проверка существующего файла на наличие заголовков
            with (open(COMMENT_LOG_PATH, 'r', encoding='utf-8') as f):
                first_line = f.readline().strip()
                # Если заголовки отсутствуют - добавляем их
                if not (first_line.startswith('timestamp') and 'process' in first_line
                    and 'user_id' in first_line and 'status' in first_line and 'state' in first_line
                    and 'data' in first_line and 'cat_id' in first_line and 'comm_id' in first_line
                    and 'len_stack' in first_line):
                    with open(COMMENT_LOG_PATH, 'r+', encoding='utf-8') as f:
                        #content = f.read()
                        f.seek(0, 0)
                        #f.write('timestamp,user_id,username,case,status,handler,category_id\n' + content)
                        f.write('timestamp,process,user_id,status,state,data,cat_id,comm_id,len_stack,comment')

    def add_status(self, status_names: str):
        names = [s.strip() for s in status_names.split(",")]
        for name in names:
            if name not in self.state_vars:
                self.state_vars[name] = []
            if name not in self.state_forward_mooving:
                self.state_forward_mooving[name] = []

    def it_process(self, status, process_name, status_names: str):
        if status not in self.state_vars:
            raise Exception(f"Статус {status} не создан")
        arr = [s.strip() for s in status_names.split(",")]
        for s in arr:
            if s not in self.state_vars:
                raise Exception(f"Статус {s} не объявлен")
        self.processes[status] = arr
        self.processes_name[status] = process_name

    def add_forward_moving(self, status_from, status_to_names: str):
        if status_from not in self.state_vars:
            raise Exception(f"Статус {status_from} не создан")
        arr = [s.strip() for s in status_to_names.split(",")]
        for s in arr:
            if s not in self.state_vars:
                raise Exception(f"Статус {s} не объявлен")
        self.state_forward_mooving[status_from] = arr

    def back_moving(self, status_to):
        arr = []
        for k, v in self.state_forward_mooving.items():
            if status_to in v:
                arr.append(k)
        return arr

    def add_state_vars(self, status, var_names: str):
        if status not in self.state_vars:
            raise Exception(f"Статус {status} не создан")
        arr = [s.strip() for s in var_names.split(",") if s.strip()]
        self.state_vars[status].extend([v for v in arr if v not in self.state_vars[status]])

    def get_vars(self, status):
        if status not in self.state_vars:
            raise Exception(f"Статус {status} не создан")
        return self.state_vars[status]

    def log_comment_request(self, comment:str = ''):
        """Записывает информацию в CSV-лог"""
        try:
            # Открытие файла в режиме добавления
            with open(COMMENT_LOG_PATH, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Формирование строки лога
                if not self.process is None:
                    writer.writerow([
                        datetime.now().isoformat(),  # Текущая дата и время
                        self.process,  # процесс
                        self.user_id,
                        self.status,  # тек.статус
                        self.state_status,
                        self.data,
                        self.dict.get('cat_id',0),
                        self.dict.get('comm_id',0),
                        len(self.stack),
                        comment
                ])
        except Exception as e:
            raise Exception(f"Ошибка записи в лог: {e}")

    def _reset_state(self):
        self.process = None
        self.status = None
        self.dict = {}
        self.data = None

    def forward_stack(self, status, dct, state_status, data ):
        # Проверка process

        if self.process is None:
            if status not in self.processes:
                raise Exception(f"Процесс {status} не объявлен")
            else:
                self.process = status
                self.status = status
                self.state_status = state_status
                self.data = data

        if self.status == status:
            for var in self.state_vars[status]:
                if var in dct:
                    if var in self.dict:
                        self.dict[var] = dct[var]
            return

        # Проверка достижимости статуса
        if self.status is None:
            prev_statuses = [self.process]
        else:
            prev_statuses = [self.status]
        reachable = False
        for s in prev_statuses:
            if status in self.state_forward_mooving.get(s, []):
                reachable = True
                break
        if not reachable:
            raise Exception(f"Статус {status} недостижим из {self.status}")

        # Сформировать dict_new
        dict_new = {}
        for var in self.state_vars[status]:
            if var in dct:
                dict_new[var] = dct[var]
            elif self.stack and var in self.stack[-1]['dict']:
                dict_new[var] = self.stack[-1]['dict'][var]

        # Записать в стек
        self.stack.append({'process': self.process, 'status': status, 'dict': dict_new.copy(),
                           'state_status':state_status,'data':data})

        # Обновить текущие переменные
        self.status = status
        self.dict = dict_new.copy()
        self.state_status = state_status
        self.data = data

        self.log_comment_request(f"forward dict={self.dict}")

    # откат на 1 шаг назад
    def back_stack(self):
        if not self.stack:
            self._reset_state()
            self.log_comment_request(f"back dict={self.dict}")
            return

        self.stack.pop()
        if not self.stack:
            self._reset_state()
            self.log_comment_request(f"back dict={self.dict}")
            return
        else:
            top = self.stack[-1]
            self.process = top['process']
            self.status = top['status']
            self.dict = top['dict'].copy()
            self.state_status = top['state_status']
            self.data = top['data']
            self.log_comment_request(f"back dict={self.dict}")

            if self.state_status is None:
                self.back_stack()
            elif self.state_forward_mooving.get(self.status) is None:
                self.back_stack()

    #откат до определенного статуса
    def back_stack_status(self, status):
        if not self.stack:
            return
        elif self.status == status:
            return
        else:
            self.back_stack()
            self.back_stack_status(status)


def Init_Fsm(fsm_proc):
    print("Начали инициализироть fsm_proc")
    fsm_proc.state_vars = {
        "FIND_CAT": ["keyword"],
        "CHOOSE_CAT_ID": [],
        "FIND_CAT_ONE": ["cat_id"],
        "LIST_CAT": ["cat_id"],
        "EDIT_CAT": [ "data", "name"],
        "DEL_CAT": ["cat_id"],
        "FIND": [],
        "FIND_COMM": ["cat_id", "keyword"],
        "LIST_COMM": ["comm_id"],
        "CHOOSE_COMM_ID": ["cat_id"],
        "FIND_COMM_ONE": ["cat_id","comm_id"],
        "ADD": [],
        "ADD_NAME": [ "cat_id", "name","comment"],
        "EDIT": [],
        "EDIT_COMM_NAME": ["comm_id", "name"],
        "EDIT_COMM_COMM": ["comm_id", "comment"],
        "DEL_COMMENT": ["comm_id"],
        "END": []
    }
    fsm_proc.state_forward_mooving = {
        "START": ["FIND_CAT", "FIND", "ADD", "EDIT", "END"],
        "FIND_CAT": ["CHOOSE_CAT_ID","FIND_CAT_ONE"],
        "CHOOSE_CAT_ID": ["FIND_CAT_ONE"],
        "FIND_CAT_ONE": ["EDIT_CAT", "DEL_CAT", "CHOOSE_CAT_ID", "ADD_NAME","FIND_COMM","FIND_COMM_ONE","LIST_CAT","LIST_COMM"],
        "EDIT_CAT": [],
        "DEL_CAT": [],
        "FIND": ["FIND_CAT","FIND_COMM"],
        "FIND_COMM": ["CHOOSE_COMM_ID","FIND_COMM_ONE"],
        "CHOOSE_COMM_ID": ["FIND_COMM_ONE"],
        "FIND_COMM_ONE": ["ADD_NAME", "EDIT_COMM_NAME", "EDIT_COMM_COMM", "DEL_COMMENT"],
        "ADD": ["FIND_CAT"],
        "ADD_NAME": [],
        "EDIT": ["FIND_CAT","FIND_COMM"],
	    "EDIT_COMM_NAME": [],
        "EDIT_COMM_COMM": [],
        "DEL_COMMENT": [],
        "END": []
    }
    fsm_proc.it_process("LIST_CAT","Смотрим категории...", "LIST_CAT")
    fsm_proc.it_process("FIND_CAT","Ищем категорию...", "FIND_CAT,CHOOSE_CAT_ID,FIND_CAT_ONE,EDIT_CAT,DEL_CAT,LIST_CAT,LIST_COMM")
    fsm_proc.it_process("FIND", "Ищем рекомендации...", "FIND,FIND_CAT,CHOOSE_CAT_ID,FIND_CAT_ONE,LIST_CAT,LIST_COMM,FIND_COMM,CHOOSE_COMM_ID,\n"
                                "FIND_COMM_ONE,ADD_NAME,DEL_COMMENT,EDIT_COMM_NAME,EDIT_COMM_COMM")
    fsm_proc.it_process("ADD", "Добавляем рекомендацию...", "ADD,FIND_CAT,CHOOSE_CAT_ID,FIND_CAT_ONE,ADD_NAME")
    fsm_proc.it_process("EDIT", "Редактируем рекомендации...", "EDIT,FIND_CAT,CHOOSE_CAT_ID,FIND_CAT_ONE,FIND_COMM,CHOOSE_COMM_ID,\n"
                                "FIND_COMM_ONE,EDIT_COMM_NAME,EDIT_COMM_COMM")
    #print("Инициализировали fsm_proc")

def log_last(update: Update, context: CallbackContext) -> None:

    fsm_proc = context.user_data.get("fsm_proc")
    user_id = fsm_proc.user_id

    records = []
    with open(COMMENT_LOG_PATH, 'r', encoding='utf-8') as file:
        reader = list(csv.reader(file))
        # Найти индекс последнего status='START'
        last_start_idx = None
        for i in range(len(reader) - 1, -1, -1):
            if len(reader[i]) > 1:
                if reader[i][2] != str(user_id):
                    last_start_idx = i
                    continue

                if len(reader[i]) > 1 and reader[i][1] in ["ADD","EDIT","FIND","FIND_CAT"]:
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
        text = '\n'.join(response[i:i + 40])
        update.message.reply_text(text)

def comm_stats(update: Update, context: CallbackContext):
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
                if len(row) < 9:
                    row += [''] * (9 - len(row))
                logs.append(row[:9])  # Сохранение только первых 9 значений

        # Создание DataFrame из логов
        df = pd.DataFrame(logs,
                          columns=['timestamp', 'process', 'user_id', 'status', 'state', 'data', 'cat_id', 'comm_id',
                                   'len_stack'])

        # Проверка на наличие данных
        if df.empty:
            update.message.reply_text("📊 Статистика пока недоступна. Нет данных для анализа.")
            return

        # Преобразование нужных данных в числовой формат
        df['user_id'] = pd.to_numeric(df['user_id'], errors='coerce')
        df['cat_id'] = pd.to_numeric(df['cat_id'], errors='coerce')
        df['comm_id'] = pd.to_numeric(df['comm_id'], errors='coerce')
        df['len_stack'] = pd.to_numeric(df['len_stack'], errors='coerce')

        # Расчет основных метрик
        total_requests = len(df)  # Общее количество запросов
        process_counts = df['process'].value_counts()  # Распределение по процессам
        status_counts = df['status'].value_counts()  # Распределение по статусам
        unique_user = df['user_id'].nunique()  # Уникальные пользователи
        unique_cat = df[df['cat_id'] != 0]['cat_id'].nunique()  # Уникальные категории
        unique_comm = df[df['comm_id'] != 0]['comm_id'].nunique()  # Уникальные рекомендации

        status_counts = df['status'].value_counts()  # Распределение по статусам

        # Топ-5 категорий
        popular_cats = df[df['cat_id'] != 0]['cat_id'].value_counts().head(5)

        # Топ-5 пользователей
        popular_users = df[df['user_id'] != 0]['user_id'].value_counts().head(5)

        # Формирование текстового отчета
        report = (
            f"📊 Статистика процессов:\n"
            f"📊Уникальных пользователей: {unique_user}\n\n"
            f"📊Уникальных категорий: {unique_cat}\n"
            f"📊 Уникальных рекомендаций: {unique_comm}\n"
            f"🏙️ Топ-5 категорий:\n"
            f"🏙️ Топ-5 пользователей:\n"
        )

        # Добавление информации о поиске в категориях
        if not popular_cats.empty:
            for cat_id, count in popular_cats.items():
                fname = fname_catid(cat_id)
                report += f"  - {fname}: {count}\n"
        else:
            report += "  Нет данных о запросах в категориях\n"

        # Добавление информации о поиске юзерами
        if not popular_users.empty:
            for user_id, count in popular_users.items():
                fname = user_name(user_id)
                report += f"  - {fname}: {count}\n"
        else:
            report += "  Нет данных о запросах пользоваьтелей\n"

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
        if not popular_cats.empty:
            plt.figure(figsize=(10, 6))  # Размер графика
            # Построение столбчатой диаграммы
            popular_cats.plot(kind='bar', color='skyblue')
            plt.title('Топ категорий')  # Заголовок
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
        elif "INSERT INTO" in query.upper():
            result = cursor.lastrowid
        else:
            result = None
        print(f"result={result} из {query}")

        conn.commit()
        conn.close()
        return result

    except Exception as e:
        print(f"Ошибка базы данных: {e}\n"
              f"{query}"
              f"{params}")
    return None

def list_cat(lev:int=0, parent_id:int=0, cat_id:int=0, user_id:int=0):
    str_res = ""
    res = execute_query("SELECT id, name FROM categories WHERE (parent_id = ?) and (0 = ? or id = ?)",
                        (parent_id,cat_id,cat_id), fetchall = True)
    if res:
        for result in res:
            count_comm_all = count_cat_comment(result[0], 0)
            rec = f", рекомендаций {count_comm_all}"
            if user_id !=0:
                count_comm = count_cat_comment(result[0], user_id)
                rec = rec+f",({count_comm_all})"
            str_res = str_res + "\n" + ("🔻"*lev)+fname_cat(result)+rec
            if have_subcategory(result[0]):
                lev1 = lev+1
                str_res1 = list_cat(lev1, result[0], 0, user_id )
                str_res = str_res + str_res1
        #str_res = str_res + "\n"

    return str_res

def list_comm(lev:int=0, parent_id:int=0, cat_id:int=0):
    str_res = ""
    res = execute_query("SELECT id, name FROM categories WHERE (parent_id = ?) and (0 = ? or id = ?)",
                        (parent_id,cat_id,cat_id), fetchall = True)
    if res:
        for result in res:
            str_res = str_res + "\n" + ("🔻"*lev)+fname_cat(result)
            commres = execute_query("SELECT id, name FROM comments WHERE category_id = ?", (result[0],),
                                        fetchall=True)
            if commres:
                for commresult in commres:
                    str_res = str_res + "\n" + ("®️" * (lev+1)) + fname_cat(commresult)

            if have_subcategory(result[0]):
                lev1 = lev+1
                str_res1 = list_comm(lev1, result[0], 0)
                str_res = str_res + str_res1

    return str_res

def update_comm_name(comm_id, new_name):
    # логика изменения названия рекомендации в БД
    execute_query("UPDATE comments SET name = ? WHERE id = ?", (new_name, comm_id,))
    return comm_id

def update_comm_comm(comm_id, new_comm):
    # логика изменения рекомендации в БД
    execute_query("UPDATE comments SET comment = ? WHERE id = ?", (new_comm, comm_id,))
    return comm_id

def update_cat_name(cat_id, new_name):
    # логика изменения названия категории в БД
    execute_query("UPDATE categories SET name = ? WHERE id = ?", (new_name, cat_id,))
    return cat_id

def add_comm(comm_name, comm_comment, cat_id:int, usr_id:int):
    # логика добавления рекомендации в БД
    dt_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    comm_id = execute_query("INSERT INTO comments (name, comment, category_id, user_id, dt) VALUES (?, ?, ?, ?, ?)", (comm_name, comm_comment,cat_id, usr_id, dt_now, ))
    return comm_id

def add_category(cat_name, parent_id):
    # логика добавления категории в БД
    cat_id = execute_query("INSERT INTO categories (name, parent_id) VALUES (?, ?)", (cat_name, parent_id,))
    return cat_id

def delete_comment(comm_id):
    # логика удаления рекомендации из БД
    comm = comm_commid(comm_id)
    execute_query("DELETE FROM comments WHERE id = ?", (comm_id,))
    # prnt_id = execute_query("SELECT id,name,user_id,category_id,comment FROM comments WHERE category_id = ? ", (comm[3],), fetchone = True)
    # return prnt_id

def count_cat_comment(cat_id:int, user_id:int=0):

    mas_cat_id = all_subcategory(cat_id)
    if user_id == 0:
        params = mas_cat_id
        sql = f"""
        SELECT COUNT(*) FROM comments
        WHERE (category_id IN ({','.join(['?'] * len(mas_cat_id))}))
        """
    else:
        params = mas_cat_id + [user_id, ]
        sql = f"""
        SELECT COUNT(*) FROM comments
        WHERE (category_id IN ({','.join(['?'] * len(mas_cat_id))}))
          AND (user_id = ?)
        """

    result = execute_query(sql, params, fetchone=True)
    return result[0] if result else 0


def delete_category(cat_id, user_id):
    # логика удаления категории из БД
    if count_cat_comment(cat_id, user_id) == count_cat_comment(cat_id, 0):
        #все рекомендации - свои, удалять можно
        mas_cat_id = all_subcategory(cat_id)
        params = mas_cat_id

        sql = f"""
        DELETE FROM comments
        WHERE (category_id IN ({','.join(['?'] * len(mas_cat_id))}))
         """
        execute_query(sql, params)
        return True
    else:
        return False

def user_name(user_id:int):
    comm = execute_query("SELECT id, name FROM users WHERE id = ?", (user_id,),
                            fetchone=True)
    if comm:
        return f"{comm[1]}(id={comm[0]})"
    else:
        return ""

def exist_cat( name:str, prnt:int, cat_id):
    exists = execute_query("SELECT id FROM categories WHERE LOWER(name) = ? and parent == ? and id != ?",
            (name.lower(), prnt, cat_id, ), fetchone=True )
    return bool(exists)

def fname_cat(comm):
    return f"{comm[1]}(id={comm[0]})"

def comm_commid(comm_id:int):
    comm = execute_query("SELECT id, name, user_id, category_id, comment FROM comments WHERE id = ?", (comm_id,),
                            fetchone=True)
    return comm

def fname_commid(comm_id:int):
    comm = comm_commid(comm_id)
    if comm:
        return f"{comm[1]}(id={comm[0]})"
    else:
        print(f"fname_commid id={comm_id} comm=None")
        return ""

def fname_catid(cat_id:int):
    comm = execute_query("SELECT id, name FROM categories WHERE id = ?", (cat_id,),
                            fetchone=True)
    return f"{comm[1]}(id={comm[0]})"

def get_user_id_from_tg( tg_id:int):
    comm = execute_query("SELECT id,name FROM users WHERE telegram_id = ?", (tg_id,), fetchone=True)
    return comm[0] if comm else 0

def parent(cat_id:int):
    comm = execute_query("SELECT parent_id FROM categories WHERE id = ?", (cat_id,),
                         fetchone=True)
    return comm[0] if comm else 0

def all_subcategory(cat_id:int):
    arr = [cat_id]
    results = execute_query("SELECT id, name, parent_id FROM categories WHERE parent_id = ?",
                            (cat_id,), fetchall=True)
    for res in results:
        arr.extend( all_subcategory(res[0]) )

    return arr

def have_subcategory(cat_id:int):
    results = execute_query("SELECT id, name, parent_id FROM categories WHERE parent_id = ?", (cat_id,),
                            fetchone=True)
    return bool(results)

def have_comments(cat_id:int):
    results = execute_query("SELECT id, name FROM comments WHERE category_id = ?", (cat_id,),
                            fetchone=True)
    return bool(results)

def have_near(cat_id:int):
    results = execute_query(
        "SELECT c.id as id, c.name as name, c.parent_id as parent_id FROM categories c "
        "INNER JOIN categories cat ON (c.parent_id = cat.parent_id) WHERE c.id != cat.id and cat.id = ?", (cat_id,), fetchall=True)

    return bool(results)
########################## конец вспомогательные функции работы с базой данных
########################## клавиатуры на разные случаи

def keyboard_for_id(id:int, process:str):
    fname = fname_catid(id)
    keyboard = [
        [InlineKeyboardButton(f"Список подкатегорий", callback_data="listsub_" + str(id))],
        [InlineKeyboardButton(f"Список рекомендаций", callback_data="listcomm_" + str(id))],
    ]

    prnt = parent(id)
    if prnt != 0:
        fprnt = fname_catid(prnt)
        keyboard.append([InlineKeyboardButton(f"Выбрать родителя - '{fprnt}'", callback_data="parent_" + str(prnt))])

    if have_subcategory(id):
        keyboard.append( [InlineKeyboardButton(f"Выбрать подкатегорию", callback_data="subcategory_"+str(id))] )

    if have_near(id):
       keyboard.append([InlineKeyboardButton(f"Выбрать рядом", callback_data="near_" + str(id))] )

    if process == "FIND_CAT":
        keyboard.append([InlineKeyboardButton(f"Добавить рядом", callback_data="addnear_" + str(id))])
        keyboard.append([InlineKeyboardButton(f"Добавить подкатегорию", callback_data="addsub_" + str(id))])
        keyboard.append([InlineKeyboardButton(f"Удалить категорию", callback_data="del_" + str(id))])
    else:
        keyboard.append([InlineKeyboardButton(f"Завершить выбор на {fname}", callback_data="thiscat_" + str(id))])

    reply_markup = keyboard_add(keyboard, to_main = True, ret = True)

    return reply_markup

def keyboard_comment_id(id:int, user_id:int):
    comm = comm_commid(id)
    fname = fname_commid(id)
    cat_id = comm[3]
    fname_cat = fname_catid(cat_id)
    keyboard = [
        [InlineKeyboardButton(f"Посмотреть рекомендацию в категории {fname}", callback_data=f"lookcomm_{id}")],
        [InlineKeyboardButton(f"Добавить рекомендацию в категории {fname_cat}", callback_data=f"addcomm_{cat_id}")]
        ]
    if comm[2] == user_id:
        keyboard.append([InlineKeyboardButton(f"Изменить наименование рекомендации {fname}", callback_data=f"editname_{id}")])
        keyboard.append([InlineKeyboardButton(f"Изменить текст рекомендации {fname}", callback_data=f"editcomm_{id}")])
        keyboard.append([InlineKeyboardButton(f"Удалить рекомендацию {fname}", callback_data=f"delcomm_{id}")])

    reply_markup = keyboard_add(keyboard, to_main = True, ret = True)

    return reply_markup

def keyboard_comment_choose(cat_id, keyword):

    keyboard = [
                 [InlineKeyboardButton("Возврат", callback_data="return_")]
               ]
    prm = '%'+keyword.lower()+'%'
    mas_cat_id = all_subcategory(cat_id)
    params = mas_cat_id + [prm,prm,]
    sql = f"""
    SELECT id, name, comment, user_id FROM comments
    WHERE (category_id IN ({','.join(['?'] * len(mas_cat_id))}))
    AND ((LOWER(name) LIKE ?) OR (LOWER(comment) LIKE ?))
    """
    results = execute_query(sql, params, fetchall=True)
    if results:
        for comm in results:
            fname = fname_cat(comm)
            keyboard.append([InlineKeyboardButton(f"{fname}", callback_data="comment_" + str(comm[0]))])

    reply_markup = keyboard_add(keyboard, to_main = True, ret = True)

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

    elif data.startswith("parent_"):
        cat_id = int(data[len("parent_"):])

        results = execute_query(
            "SELECT c.id as id, c.name as name, c.parent_id as parent_id FROM categories c "
            "INNER JOIN categories cat ON (c.id = cat.parent_id) WHERE cat.id = ?", (cat_id,), fetchall=True)

        for comm in results:
            fname = fname_cat(comm)
            txt = txt +"\n"+f"{fname}"
            keyboard.append([InlineKeyboardButton(f"{fname}", callback_data="choose_" + str(comm[0]))])

    reply_markup = keyboard_add(keyboard, to_main = True, ret = True)
    return reply_markup

def keyboard_main_menu():

    buttons = [
        [InlineKeyboardButton("Все категории", callback_data="LIST_CAT")],
        [InlineKeyboardButton("Действия над категориями", callback_data="FIND_CAT")],
        [InlineKeyboardButton("Найти рекомендации в категории", callback_data="FIND")],
        [InlineKeyboardButton("Добавить рекомендацию в категории", callback_data="ADD")],
        [InlineKeyboardButton("Отредактировать рекомендацию в категории", callback_data="EDIT")],
        [InlineKeyboardButton("Завершить", callback_data="END")]
    ]
    return InlineKeyboardMarkup(buttons)

def keyboard_add(buttons, to_main:bool=False, ret:bool=False):
    if to_main:
        buttons.append([
            InlineKeyboardButton("В главное меню", callback_data="TO_MAIN")
        ])
    if ret:
        buttons.append([
            InlineKeyboardButton("Возврат", callback_data="RETURN")
        ])
    return InlineKeyboardMarkup(buttons)

def keyboard_state_buttons(options, add_back=True):
    buttons = []
    for opt in options:
        buttons.append([InlineKeyboardButton(opt.get('name'), callback_data=opt.get('callback'))])
    if add_back:
        reply_markup = keyboard_add( buttons, True,True )
    else:
        reply_markup = InlineKeyboardMarkup(buttons)

    return reply_markup
########################### конец клавиатуры

def get_missing_vars(next_status, current_dict):
    required = fsm_proc.state_vars[next_status]
    return [v for v in required if v not in current_dict or current_dict[v] is None]

# --- Хендлеры ---

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
        execute_query("UPDATE users SET dt_last = ? WHERE id = ?", (dt_now, users[0],))
        user_id = users[0]

        update.message.reply_text(f"Добро пожаловать, {user_name}! Ты уже бывал!")

    fsm_proc = FSM_proc(user_id,user_name,telegram_id)
    Init_Fsm(fsm_proc)
    context.user_data["fsm_proc"] = fsm_proc

    reply_markup = keyboard_main_menu()
    message_text = (
        "Выберите действие:\n\n"
        "Доступные команды:\n"
        "/add  - Добавить рекомендацию\n"
        "/edit - Изменить свою рекомендацию\n"
        "/list_cat - Все категории\n"
        "/find_cat - Операции с категорией\n"
        "/find - Найти рекомендации\n"
        "/end - завершить"
    )
    text = update.message.text.strip()

    if update.message:
        update.message.reply_text(message_text, reply_markup=reply_markup)
    elif update.callback_query:
        update.callback_query.answer()
        update.callback_query.edit_message_text(message_text, reply_markup= reply_markup)

    return 1

def process_callback(update: Update, context: CallbackContext):

    fsm_proc = context.user_data.get("fsm_proc")
    user_id = fsm_proc.user_id
    process = fsm_proc.process

    query = update.callback_query
    query.answer()
    data = query.data

    strvar = lambda x: "None" if x is None else x

    process = strvar(fsm_proc.process)
    status = strvar(fsm_proc.status)
    state_status = strvar(fsm_proc.state_status)

    #query.edit_message_text(f"p_cback data={data} process ={process} status ={status} ss={state_status} ")

    if data == "RETURN":
        while True:
            fsm_proc.back_stack()
            if fsm_proc.status is None:
                query.edit_message_text("Главное меню:", reply_markup=keyboard_main_menu())
                return 1
            else:
                # Вызываем обработку текущего статуса после возврата (возврат только в кнопки!)
                state_status = fsm_proc.state_status
                if state_status == 1:
                    data = fsm_proc.data #подменили data
                    break

    if data == "TO_MAIN":
        fsm_proc.process = None
        fsm_proc.status = None
        fsm_proc.dict = {}
        fsm_proc.stack = []
        query.edit_message_text("Главное меню:", reply_markup=keyboard_main_menu())
        return 1

    elif data == "LIST_CAT":

        if fsm_proc.process is None:
            lstcat = list_cat(0, 0, 0, user_id)
        else:
            cat_id = fsm_proc.dict.get('cat_id')
            if cat_id is None:
                lstcat = list_cat(0, 0, 0, user_id)
            else:
                prnt = parent(cat_id)
                lstcat = list_cat(0, prnt, cat_id, user_id)

        reply_markup = keyboard_add([], to_main = True)

        query.edit_message_text(f"Список категорий:"+lstcat, reply_markup=reply_markup)
        return 1

    if data in ( "ADD", "EDIT", "FIND", "FIND_CAT"):

        fsm_proc.forward_stack( data, {}, state_status = None, data = None )
        process_name = fsm_proc.processes_name[fsm_proc.process]
        state_data = f"{process_name}: Введите id категории или слово для ее поиска:"
        if data in ("ADD", "EDIT", "FIND"):
            fsm_proc.forward_stack("FIND_CAT", {'keyword':''}, state_status = 2, data = state_data )

        # query.edit_message_text(f"{state_data}")
        #
        # return 2
        reply_markup = keyboard_state_buttons([],True)
        query.edit_message_text(f"{state_data}", reply_markup=reply_markup)
        return 3

    elif data.startswith("thiscat_"):

        cat_id = int(data[len("thiscat_"):])
        fname = fname_catid(cat_id)

        if fsm_proc.process == "ADD":
            fsm_proc.forward_stack("FIND_CAT_ONE", {'cat_id': cat_id}, state_status = 1, data = data)

            # Автоматический переход к вводу наименования рекомендации
            reply_markup = keyboard_state_buttons([], True)

            process_name = fsm_proc.processes_name[fsm_proc.process]
            state_data = f"{process_name}: Укажите теперь наименование рекомендации:"
            fsm_proc.forward_stack("ADD_NAME", {'cat_id': cat_id, 'name':'', 'comment':'' },
                                   state_status = 2, data = state_data)

            query.edit_message_text(f"{state_data}", reply_markup = reply_markup)

            return 3

        elif fsm_proc.process == "EDIT" or fsm_proc.process == "FIND":
            if fsm_proc.status != "FIND_COMM":
                fsm_proc.forward_stack("FIND_CAT_ONE", {'cat_id': cat_id}, state_status = 1, data = data)

            # Автоматический переход к вводу ключевого слова
            reply_markup = keyboard_state_buttons([], True)

            process_name = fsm_proc.processes_name[fsm_proc.process]
            state_data = f"{process_name}: Укажите теперь id или слово в рекомендации для подбора:"

            fsm_proc.forward_stack("FIND_COMM", {'cat_id':cat_id, 'keyword': ''}, state_status = 2, data = state_data)

            query.edit_message_text(f"{state_data}", reply_markup = reply_markup)

            return 3

        else:
            reply_markup = keyboard_state_buttons([], True)
            update.message.reply_text(
                f"{process_name}: Неожиданность: оказался статус {fsm_proc.status} вместо FIND_CAT_ONE???",
                reply_markup=reply_markup)

            return 1

    elif data.startswith("choose_"):

        cat_id = int(data[len("choose_"):])
        fname = fname_catid(cat_id)

        reply_markup = keyboard_for_id(cat_id, fsm_proc.process)

        process_name = fsm_proc.processes_name[fsm_proc.process]
        state_data = f"{process_name}: Варианты действий c категорией:'{fname}'"
        fsm_proc.forward_stack("FIND_CAT_ONE", {'cat_id': cat_id}, state_status=1, data=data)

        query.edit_message_text(f"{state_data}", reply_markup=reply_markup)

        return 1

    elif data.startswith("subcategory_") or data.startswith("near_") or data.startswith("parent_"):

            reply_markup = keyboard_choose(data)
            process_name = fsm_proc.processes_name[fsm_proc.process]
            query.edit_message_text(f"{process_name}: Выберите категорию", reply_markup=reply_markup)

            fsm_proc.forward_stack("CHOOSE_CAT_ID", {}, state_status = None, data = None)

            return 1

    # Обработка редактирования, добавления, удаления
    elif data.startswith("edit_") or data.startswith("addnear_") or data.startswith("addsub_"):

        if data.startswith("edit_"):
            cat_id = int(data.replace("edit_", "", 1))
        elif data.startswith("addnear_"):
            cat_id = int(data.replace("addnear_", "", 1))
        else:
            cat_id = int(data.replace("addsub_", "", 1))

        reply_markup = keyboard_state_buttons([],True)
        process_name = fsm_proc.processes_name[fsm_proc.process]
        state_data = f"{process_name}: Укажите новое название категории:"
        query.edit_message_text(f"{state_data}",reply_markup = reply_markup)
        # Кнопки 'Сохранить' и 'Отказаться' будут после ввода названия

        fsm_proc.forward_stack("EDIT_CAT", {'data':data,'name': ''}, state_status = 2, data = state_data)

        return 3

    elif data.startswith("del_"):
        cat_id = int(data.replace("del_", "", 1))
        fname = fname_catid(cat_id)

        reply_markup = keyboard_state_buttons([{'name':"Подтвердить",'callback':f"confdel_{cat_id}"}],
                                          True)

        # keyboard = [
        #     [InlineKeyboardButton("Подтвердить", callback_data=f"confdel_{cat_id}")],
        #     [InlineKeyboardButton("Отказаться", callback_data=f"cancdel_{cat_id}")]
        # ]
        process_name = fsm_proc.processes_name[fsm_proc.process]
        query.edit_message_text(
            f"{process_name}: Подтверждаете удаление категорию {fname}?",
            reply_markup=reply_markup
        )
        fsm_proc.forward_stack("DEL_CAT", {'cat_id': cat_id}, state_status = 1, data = data)

        return 1

    elif data.startswith("confdel_"):
        cat_id = int(data.replace("confdel_", "", 1))
        fname = fname_catid(cat_id)

        reply_markup = keyboard_add([], True, False)

        process_name = fsm_proc.processes_name[fsm_proc.process]

        if delete_category(cat_id, user_id):
            query.edit_message_text(f"{process_name}: Категория  {fname} удалена!", reply_markup=reply_markup)
            fsm_proc.back_stack()
        else:
            query.edit_message_text(f"{process_name}: {fname} удалить нельзя: есть чужие рекомендации!", reply_markup=reply_markup)
            fsm_proc.back_stack()

        return 1

    # elif data.startswith("cancdel_"):
    #     cat_id = int(data.replace("cancdel_", "", 1))
    #     fname = fname_catid(cat_id)
    #
    #     reply_markup = keyboard_state_buttons([], True )
    #
    #     fsm_proc.back_stack()
    #     process_name = fsm_proc.processes_name[fsm_proc.process]
    #     query.edit_message_text(f"{process_name}: Выберите операцию над {fname}", reply_markup=reply_markup  )
    #
    #     return 1

    elif data.startswith("confcommname_"):
        comm_id = int(data.replace("confcommname_", "", 1))

        update_comm_name(comm_id, fsm_proc.dict.get('name'))
        fsm_proc.back_stack()

        fname = fname_commid(comm_id)
        reply_markup = keyboard_comment_id(comm_id)

        process_name = fsm_proc.processes_name[fsm_proc.process]
        query.edit_message_text(f"{process_name}: Выберите действие с {fname}!", reply_markup=reply_markup )

        return 1

    elif data.startswith("confcommcomm_"):

        comm_id = int(data.replace("confcommcomm_", "", 1))

        update_comm_name(comm_id, fsm_proc.dict.get('comment'))
        fsm_proc.back_stack()

        fname = fname_commid(comm_id)
        reply_markup = keyboard_comment_id(comm_id)
        process_name = fsm_proc.processes_name[fsm_proc.process]
        query.edit_message_text(f"{process_name}: Выберите действие с {fname}!", reply_markup=reply_markup)

        return 1

    # elif data.startswith("canccommcomm_"):
    #
    #     comm_id = int(data.replace("canccommcomm_", "", 1))
    #
    #     fsm_proc.back_stack()
    #
    #     fname = fname_commid(comm_id)
    #     reply_markup = keyboard_comment_id(comm_id)
    #     process_name = fsm_proc.processes_name[fsm_proc.process]
    #     query.edit_message_text(f"{process_name}: Выберите действие с {fname}!", reply_markup=reply_markup)
    #
    #     return 1

    elif data.startswith("comment_"):

        comm_id = int(data[len("comment_"):])
        fname = comm_commid(comm_id)

        reply_markup = keyboard_comment_id(comm_id, user_id)
        process_name = fsm_proc.processes_name[fsm_proc.process]
        query.edit_message_text(f"{process_name}: Действия с рекомендацией '{fname}'", reply_markup=reply_markup)

        fsm_proc.forward_stack("FIND_COMM_ONE", {'comm_id': comm_id}, state_status = 1, data = data)

        return 1

    elif data.startswith("delcomm_"):
        comm_id = int(data.replace("delcomm_", "", 1))
        fname = fname_commid(comm_id)

        reply_markup = keyboard_state_buttons([{'name':"Подтвердить",'callback':f"confcommdel_{comm_id}"}],
                                          True)
        process_name = fsm_proc.processes_name[fsm_proc.process]
        query.edit_message_text(
            f"{process_name}: Удаляем рекомендацию {fname}?",
            reply_markup = reply_markup
        )

        fsm_proc.forward_stack("DEL_COMM", {'comm_id': comm_id}, state_status = 1, data = data)

        return 1

    elif data.startswith("confcommdel_"):

        comm_id = int(data.replace("confcommdel_", "", 1))

        fname = fname_commid(comm_id)

        delete_comment(comm_id)

        fsm_proc.back_stack()

        reply_markup = keyboard_add([], False, True)

        process_name = fsm_proc.processes_name[fsm_proc.process]
        query.edit_message_text(f"{process_name}: Рекомендация {fname} удалена!", reply_markup=reply_markup)

        return 1

    elif data.startswith("canccommdel_"):
        comm_id = int(data.replace("canccommdel_", "", 1))
        fname = fname_commid(comm_id)

        fsm_proc.back_stack()
        reply_markup = keyboard_comment_id(comm_id, user_id)
        process_name = fsm_proc.processes_name[fsm_proc.process]
        query.edit_message_text(
            f"{process_name}: Действия с рекомендацией '{fname}'",
            reply_markup=reply_markup
        )
        return 1

    elif data.startswith("listsub_"):

        cat_id = int(data.replace("listsub_", "", 1))
        prnt_id = parent(cat_id)

        listcat = list_cat(0, prnt_id, cat_id, user_id)

        reply_markup = keyboard_state_buttons([], True)

        fsm_proc.forward_stack("LIST_CAT", {'cat_id': cat_id}, state_status=1, data=data)

        query.edit_message_text(f"{listcat}", reply_markup=reply_markup)

        return 1

    elif data.startswith("listcomm_"):

        cat_id = int(data.replace("listcomm_", "", 1))
        prnt_id = parent(cat_id)

        listcomm = list_comm(0, prnt_id, cat_id)

        reply_markup = keyboard_state_buttons([], True)

        #fsm_proc.forward_stack("LIST_COMM", {'cat_id': cat_id}, state_status=1, data=data)

        query.edit_message_text(f"{listcomm}", reply_markup=reply_markup)

        return 1

    elif data.startswith("editname_"):

        comm_id = int(data.replace("editname_", "", 1))
        fname = fname_commid(comm_id)

        reply_markup = keyboard_state_buttons([], True)
        process_name = fsm_proc.processes_name[fsm_proc.process]
        state_data = f"{process_name}: Измените название {fname}:"
        query.edit_message_text(f"{state_data}", reply_markup = reply_markup)
        # Кнопки 'Сохранить' и 'Отказаться' будут после ввода названия

        fsm_proc.forward_stack("EDIT_COMM_NAME", {'comm_id': comm_id}, state_status = 2, data = state_data)

        return 3

    elif data.startswith("editcomm_"):
        comm_id = int(data.replace("editcomm_", "", 1))

        comm = comm_commid(comm_id)
        fname = fname_commid(comm_id)

        reply_markup = keyboard_state_buttons([], True)
        process_name = fsm_proc.processes_name[fsm_proc.process]
        state_data =  (f"{process_name}: Вот ваша рекомендация :\n"
                       f"{comm[4]}\n"
                       f"Измените рекомендацию:")
        query.edit_message_text(f"{state_data}", reply_markup = reply_markup)
        fsm_proc.forward_stack("EDIT_COMM_COMM", {'data': data}, state_status = 2, data = state_data)

        return 3

    elif data.startswith("lookcomm_"):

        comm_id = int(data.replace("lookcomm_", "", 1))

        comm = comm_commid(comm_id)
        fname = fname_commid(comm_id)
        process_name = fsm_proc.processes_name[fsm_proc.process]

        reply_markup = keyboard_state_buttons([], True)
        query.edit_message_text(f"{process_name}: Вот ваша рекомендация по {fname}: {comm[4]}", reply_markup=reply_markup )

        return 1

    elif data.startswith("addcomm_"):

        cat_id = int(data.replace("addcomm_", "", 1))
        fname = fname_catid(cat_id)

        reply_markup = keyboard_state_buttons([], True)

        process_name = fsm_proc.processes_name[fsm_proc.process]
        state_data =  (f"{process_name}: Введите название своей рекомендации в категории {fname}")

        query.edit_message_text(f"{state_data}", reply_markup = reply_markup)

        fsm_proc.forward_stack("ADD_NAME", {'cat_id':cat_id,'name':'','comment':''}, state_status = 2, data = state_data )

        return 3

def handle_input(update: Update, context: CallbackContext):

    text = update.message.text.strip()

    fsm_proc = context.user_data.get("fsm_proc")
    user_id = fsm_proc.user_id
    telegram_id = fsm_proc.telegram_id
    user_name = fsm_proc.user_name

    strvar = lambda x: "None" if x is None else x

    process = strvar(fsm_proc.process)
    status = strvar(fsm_proc.status)
    state_status = strvar(fsm_proc.state_status)
    data = strvar(fsm_proc.data)

    #update.message.reply_text(f"handle_input text={text} process ={process} status ={status} ss={state_status} data={data}")

    if text.lower() == "/list_cat":

        if fsm_proc.process is None:
            lstcat = list_cat(0, 0, 0, user_id)
        else:
            cat_id = fsm_proc.dict.get('cat_id')
            if cat_id is None:
                lstcat = list_cat(0, 0, 0, user_id)
            else:
                prnt = parent(cat_id)
                lstcat = list_cat(0, prnt, cat_id, user_id)

        reply_markup = keyboard_add([], to_main=True)

        query.edit_message_text(f"Список категорий:" + lstcat, reply_markup=reply_markup)
        return 1

    elif text.lower() in ("/add","/edit","/find","/find_cat"):

        fsm_proc.process = text[1:].upper()
        fsm_proc.status = text[1:].upper()
        fsm_proc.dict = {}
        fsm_proc.stack = []

        # if text.lower() in ("/add","/edit","/find"):
        #     fsm_proc.process = None
        #     fsm_proc.status = None
        #     fsm_proc.dict = {}
        #     fsm_proc.stack = []
        #     fsm_proc.forward_stack(text[1:].upper(), state_status=None, data=None)

        process_name = fsm_proc.processes_name[fsm_proc.process]
        state_data = f"{process_name}: Введите id категории или слово для ее поиска"
        fsm_proc.forward_stack("FIND_CAT", {'keyword':''}, state_status=2, data=state_data)

        reply_markup = keyboard_state_buttons([],True)
        update.message.reply_text(f"{state_data}", reply_markup=reply_markup)
        return 3

    if fsm_proc.status == "FIND_CAT":
        # здесь обработка поиска по keyword
        keyword = text
        fsm_proc.dict['keyword'] = text
        try:
            cat_id = int(keyword)
            fname = fname_catid(cat_id)
            categories = execute_query("SELECT id, name, parent_id FROM categories WHERE id = ?", (cat_id,),
                                       fetchone=True)
            if categories:
                reply_markup = keyboard_for_id(cat_id,fsm_proc.process)
                state_data = f"choose_{cat_id}"
                process_name = fsm_proc.processes_name[fsm_proc.process]
                update.message.reply_text(f"{process_name}: Варианты действий c категорией '{fname}'", reply_markup=reply_markup)
                fsm_proc.forward_stack("FIND_CAT_ONE", {'cat_id': cat_id}, state_status=1, data=state_data)

                return 1
        except ValueError:
            pass

        results = execute_query("SELECT id, name, parent_id FROM categories WHERE LOWER(name) LIKE ?",
                                ('%'+keyword.lower()+'%',), fetchall=True)
        if not results:

            process_name = fsm_proc.processes_name[fsm_proc.process]
            reply_markup = keyboard_state_buttons([], True)
            update.message.reply_text(f"{process_name}: Не нашли категорий по слову '{keyword}'. Введите другое", reply_markup=reply_markup)

            return 3

        elif len(results) == 1:
            comm = results[0]
            fname = fname_cat(comm)
            reply_markup = keyboard_for_id(comm[0],fsm_proc.process)
            process_name = fsm_proc.processes_name[fsm_proc.process]
            update.message.reply_text(f"{process_name}: Варианты действий c категорией '{fname}'", reply_markup=reply_markup)

            state_data = f"choose_{comm[0]}"
            fsm_proc.forward_stack("FIND_CAT_ONE", {'cat_id': comm[0]}, state_status=1, data=state_data)

            return 1

        else:

            opt = []
            for comm in results:
                fname = fname_cat(comm)
                opt.append({'name':fname,'callback':f"choose_{comm[0]}"})

            reply_markup = keyboard_state_buttons(opt,True)
            process_name = fsm_proc.processes_name[fsm_proc.process]
            update.message.reply_text(f"{process_name}: Выберите категорию!", reply_markup=reply_markup)

            fsm_proc.forward_stack("CHOOSE_CAT_ID", {}, state_status=None, data=None)

            return 1

    elif fsm_proc.status == "EDIT_CAT":
        # здесь обработка ввода name

        data = fsm_proc.dict.get('data')
        process_name = fsm_proc.processes_name[fsm_proc.process]

        pref = "Добавлена категория "
        if data.startswith("edit_"):
            cat_id = int(data.replace("edit_", "", 1))
            # Проверка на существование имени
            new_name = text.strip()
            if exist_cat( new_name, parent(cat_id), cat_id):
                pref = "Такая категория уже есть!"
            else:
                update_cat_name(cat_id, text)
                pref = "Изменена категория "

        elif data.startswith("addnear_"):
            cat_id = int(data.replace("addnear_", "", 1))
            cat_id = add_category(text, parent(cat_id) )
        else:
            cat_id = int(data.replace("addsub_", "", 1))
            cat_id = add_category(text, cat_id )

        fsm_proc.back_stack()

        if fsm_proc.status == "FIND_CAT_ONE":
            reply_markup = keyboard_for_id(cat_id,fsm_proc.process)
            fname = fname_catid(cat_id)
            update.message.reply_text(f"{process_name}: {pref} '{fname}' Что дальше?", reply_markup=reply_markup)

        else:
            reply_markup = keyboard_state_buttons([],True)
            update.message.reply_text(f"{process_name}: Неожиданность: оказался статус {fsm_proc.status} вместо FIND_CAT_ONE???", reply_markup = reply_markup)

        return 1

    elif fsm_proc.status == "FIND_COMM":

        user_id = fsm_proc.user_id
        keyword = text
        fsm_proc.dict['keyword'] = text
        cat_id = fsm_proc.dict.get('cat_id')
        fname = fname_catid(cat_id)
        #print(f"FIND_COM keyword={keyword} cat_id = {cat_id}" )
        try:
            comm_id = int(keyword)
            fnamecomm = fname_commid(comm_id)
            mas_cat_id = all_subcategory(cat_id)
            params = mas_cat_id + [comm_id, comm_id, ]
            sql = f"""
            SELECT id, name, comment, user_id FROM comments
            WHERE (category_id IN ({','.join(['?'] * len(mas_cat_id))}))
            AND (LOWER(name) LIKE ? OR LOWER(comment) LIKE ?)
            """
            comm = execute_query(sql, params, fetchone=True)

            if comm:
                reply_markup = keyboard_comment_id(comm[0],fsm_proc.user_id)
                state_data = f"comment_{comm[0]}"
                reply_markup = keyboard_state_buttons([], True)

                update.message.reply_text(f"Нашли {fnamecomm}:", reply_markup=reply_markup)
                fsm_proc.forward_stack("FIND_COMM_ONE", {'comm_id': comm[0]}, state_status=1, data=state_data)

                return 1
        except ValueError:
            pass

        prm = '%'+keyword.lower()+'%'
        mas_cat_id = all_subcategory(cat_id)
        params = mas_cat_id + [prm, prm, ]
        sql = f"""
        SELECT id, name, comment, user_id FROM comments
        WHERE (category_id IN ({','.join(['?'] * len(mas_cat_id))}))
          AND ((LOWER(name) LIKE ?) OR (LOWER(comment) LIKE ?))
        """
        results = execute_query(sql, params, fetchall=True)

        if not results:
            reply_markup = keyboard_state_buttons([], True)

            update.message.reply_text(f"В рекомендациях по {fname} нет ничего похожего на '{keyword}'", reply_markup=reply_markup)

            return 1

        elif len(results) == 1:
            comm = results[0]
            fnamecomm = fname_commid(comm[0])
            state_data = f"comment_{comm[0]}"
            reply_markup = keyboard_state_buttons([{'name': f"{fnamecomm}", 'callback': state_data}], True)

            update.message.reply_text(f"Нашли одну:", reply_markup=reply_markup)
            fsm_proc.forward_stack("FIND_COMM_ONE", {'comm_id': comm[0]}, state_status=1, data=state_data)

            return 1

        else:

            reply_markup = keyboard_comment_choose(cat_id, keyword)
            update.message.reply_text("Выберите рекомендацию:", reply_markup=reply_markup)

            fsm_proc.forward_stack("CHOOSE_COMM_ID", {}, state_status=None, data=None)

            return 1

    elif fsm_proc.status == "ADD_NAME":
        # здесь обработка ввода name

        if fsm_proc.dict.get('name') == '':
            fsm_proc.dict['name'] = text

            process_name = fsm_proc.processes_name[fsm_proc.process]
            state_data = f"{process_name}: Введите текст рекомендации для {text}"

            fsm_proc.forward_stack("ADD_NAME", {'name':text}, 2, state_data )

            reply_markup = keyboard_state_buttons([],True)
            update.message.reply_text(state_data, reply_markup=reply_markup)
            return 3
        else:
            fsm_proc.dict['comment'] = text
            comm_name = fsm_proc.dict.get('name')
            cat_id = fsm_proc.dict.get('cat_id')
            comm_id = add_comm( comm_name, text, cat_id, user_id )

            fname = fname_catid(cat_id)
            fnamecomm = fname_commid(comm_id)
            state_data = f"comment_{comm_id}"
            reply_markup = keyboard_state_buttons([], True)

            process_name = fsm_proc.processes_name[fsm_proc.process]
            update.message.reply_text(f"{process_name}: В категорию {fname} добавили рекомендацию {fnamecomm}", reply_markup=reply_markup)
            fsm_proc.back_stack()
            #fsm_proc.forward_stack("FIND_COMM_ONE", {'comm_id': comm_id}, state_status=1, data=state_data)

            return 1

    elif fsm_proc.status == "EDIT_COMM_NAME":
        # здесь обработка ввода name

        comm_id = fsm_proc.dict.get('comm_id')
        update_comm_name(comm_id,text)

        fnamecomm = fname_commid(comm_id)
        fsm_proc.back_stack()

        if fsm_proc.status == "FIND_COMM_ONE":

            reply_markup = keyboard_state_buttons([], add_back=True)
            process_name = fsm_proc.processes_name[fsm_proc.process]
            update.message.reply_text(f"{process_name}: Название изменено на '{fnamecomm}'", reply_markup=reply_markup)

            return 1

        else:
            process_name = fsm_proc.processes_name[fsm_proc.process]
            reply_markup = keyboard_state_buttons([],True)
            update.message.reply_text(f"{process_name}: Неожиданность: оказался статус {fsm_proc.status} "
                                      f"вместо FIND_COMM_ONE???",reply_markup = reply_markup)

            return 1

    elif fsm_proc.status == "EDIT_COMM_COMM":
        # здесь обработка ввода comment

        comm_id = fsm_proc.dict.get('comm_id')
        update_comm_comm(comm_id, text)

        fnamecomm = fname_commid(comm_id)
        fsm_proc.back_stack()

        if fsm_proc.status == "FIND_COMM_ONE":

            reply_markup = keyboard_state_buttons([], add_back=True)
            process_name = fsm_proc.processes_name[fsm_proc.process]
            update.message.reply_text(f"{process_name}: Измененная редакция '{fnamecomm}':\n"
                                      f"'{text}'", reply_markup=reply_markup)

            return 1

        else:
            process_name = fsm_proc.processes_name[fsm_proc.process]
            reply_markup = keyboard_state_buttons([],True)
            update.message.reply_text(f"{process_name}: Неожиданность: оказался статус {fsm_proc.status}"
                                      f" вместо FIND_COMM_ONE???", reply_markup = reply_markup)

            return 1

    else:
        reply_markup = keyboard_state_buttons([], True)
        update.message.reply_text(
            f"Не умею обрабатывать ввод данных процесса {fsm_proc.process}\n"
            f"в статусе {fsm_proc.status}\n"
            f"text={text}", reply_markup = reply_markup )
        return 1


# --- MAIN ---
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      CommandHandler("log_last", log_last),
                      CommandHandler("comm_stats", comm_stats),
                      CommandHandler("add", handle_input),
                      CommandHandler("edit", handle_input),
                      CommandHandler("find", handle_input),
                      CommandHandler("find_cat", handle_input)
                      ],
        states={
            1: [CallbackQueryHandler(process_callback)],
            2: [MessageHandler(Filters.text & ~Filters.command, handle_input)],
            3: [CallbackQueryHandler(process_callback),
                MessageHandler(Filters.text & ~Filters.command, handle_input)]
        },
        fallbacks=[CommandHandler('start', start)],
        allow_reentry=True
    )
    #dp.add_handler(CommandHandler("comm_stats", comm_stats))

    dp.add_handler(conv)
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

