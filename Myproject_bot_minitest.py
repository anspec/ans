import os  # Для взаимодействия с файловой системой
from dotenv import load_dotenv #config.env
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler

load_dotenv("config.env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print(TOKEN)

# Определяем состояния для ConversationHandler
STATE_S, STATE_C1, STATE_C2, STATE_D1, STATE_D2, STATE_R = range(6)

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("A", callback_data="A"),
         InlineKeyboardButton("B", callback_data="B"),
         InlineKeyboardButton("Cancel", callback_data="Cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text(
        "Привет! Выберите команду или используйте команды /А или /В.",
        reply_markup=reply_markup
        )
    elif update.callback_query:
            update.callback_query.message.reply_text(
                "Привет! Выберите команду или используйте команды /A или /B.",
                reply_markup=reply_markup
            )
    return STATE_S

def button_handler(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    if query.data == "A":
        return process_a_start(update, context)
    elif query.data == "B":
        return process_b_start(update, context)
    elif query.data == "Cancel":
        return cancel(update, context)

def process_a_start(update: Update, context: CallbackContext) -> int:
    update.callback_query.message.reply_text("Введите число C1:")
    return STATE_C1

def process_b_start(update: Update, context: CallbackContext) -> int:
    update.callback_query.message.reply_text("Введите число D1:")
    return STATE_D1

def handle_c1(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data["C1"] = float(update.message.text)
        update.message.reply_text("Введите число C2:")
        return STATE_C2
    except ValueError:
        update.message.reply_text("Пожалуйста, введите допустимое число.")
        return STATE_C1

def handle_c2(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data["C2"] = float(update.message.text)
        keyboard = [
            [InlineKeyboardButton("+", callback_data="add"), InlineKeyboardButton("-", callback_data="sub")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Выберите операцию:", reply_markup=reply_markup)
        return STATE_R

    except ValueError:
        update.message.reply_text("Пожалуйста, введите допустимое число.")
        return STATE_C2

def handle_d1(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data["D1"] = float(update.message.text)
        update.message.reply_text("Введите число D2:")
        return STATE_D2
    except ValueError:
        update.message.reply_text("Пожалуйста, введите допустимое число.")
        return STATE_D1

def handle_d2(update: Update, context: CallbackContext) -> int:
    try:
        context.user_data["D2"] = float(update.message.text)
        keyboard = [
            [InlineKeyboardButton("*", callback_data="mul"), InlineKeyboardButton("/", callback_data="div")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Выберите операцию:", reply_markup=reply_markup)
        return STATE_R

    except ValueError:
        update.message.reply_text("Пожалуйста, введите допустимое число.")
        return STATE_D2

def calculation_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    if query.data == "add":
        result = context.user_data["C1"] + context.user_data["C2"]
        query.edit_message_text(f"Результат: {context.user_data['C1']} + {context.user_data['C2']} = {result}")
    elif query.data == "sub":
        result = context.user_data["C1"] - context.user_data["C2"]
        query.edit_message_text(f"Результат: {context.user_data['C1']} - {context.user_data['C2']} = {result}")
    elif query.data == "mul":
        result = context.user_data["D1"] * context.user_data["D2"]
        query.edit_message_text(f"Результат: {context.user_data['D1']} * {context.user_data['D2']} = {result}")
    elif query.data == "div":
        try:
            result = context.user_data["D1"] / context.user_data["D2"]
            query.edit_message_text(f"Результат: {context.user_data['D1']} / {context.user_data['D2']} = {result}")
        except ZeroDivisionError:
            query.edit_message_text("Ошибка: деление на ноль!")

    # Возвращаемся к состоянию стартового экрана
    return start(update, context)


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Операция отменена.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE_S: [CallbackQueryHandler(button_handler, pattern="^(A|B|Cancel)$")],
            STATE_C1: [MessageHandler(Filters.text & ~Filters.command, handle_c1)],
            STATE_C2: [MessageHandler(Filters.text & ~Filters.command, handle_c2)],
            STATE_D1: [MessageHandler(Filters.text & ~Filters.command, handle_d1)],
            STATE_D2: [MessageHandler(Filters.text & ~Filters.command, handle_d2)],
            STATE_R: [CallbackQueryHandler(calculation_handler, pattern="^(add|sub|mul|div)$")],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    dispatcher.add_handler(conv_handler)


    # CallbackQueryHandler для обработки кнопок
    dispatcher.add_handler(CallbackQueryHandler(calculation_handler, pattern="^(add|sub|mul|div)$"))
    dispatcher.add_handler(CallbackQueryHandler(button_handler, pattern="^(A|B)$"))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
   main()

   # class Categories():
   #     def __init__(self):
   #         cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
   #             id INTEGER PRIMARY KEY AUTOINCREMENT,
   #             name TEXT NOT NULL,
   #             active BOOLEAN,
   #             parent_id INTEGER
   #         )
   #         ''')
   #         conn.commit()
   #
   #     def is_exist_category(self, category_id:int) -> bool:
   #         try:
   #             cursor.execute("SELECT * FROM categories WHERE active=True and id = ?", (category_id,))
   #             row = cursor.fetchone()
   #             if row:
   #                 return True
   #             else:
   #                 return False
   #         except e:
   #             print(f"Ощибка в базе данных {e}")
   #             return False
   #
   #     def add_category(self, name:str, parent_id:int) -> int:
   #         #Обеспечиваем иерархию категорий
   #         try:
   #             if parent_id == 0:
   #                 cursor.execute("INSERT INTO categories (name, active, parent_id) VALUES (?, ?, ?)",
   #                                (name, True, parent_id))
   #             elif self.is_exist_category( parent_id ):
   #                 cursor.execute("INSERT INTO categories (name, active, parent_id) VALUES (?, ?, ?)",
   #                                    (name, True, parent_id))
   #
   #             else:
   #                 cursor.execute("INSERT INTO categories (name, active, parent_id) VALUES (?, ?, ?)",
   #                                    (name, True, 0))
   #                 print(f"Указан некорректный id = {parent_id} родителя при создании категории {name}. Установлен без иерархии")
   #
   #             id = cursor.lastrowid
   #
   #             conn.commit()
   #         except e:
   #             print(f"Ощибка создания категории {name} в базе данных {e}")
   #             id = 0
   #
   #         return id
   #
   #     def change_parent_for_category(self, category_id: int, parent_id: int):
   #         # Обеспечиваем иерархию категорий
   #         try:
   #             cursor.execute("SELECT * FROM categories WHERE id = ?", (parent_id,))
   #             row = cursor.fetchone()
   #             if not row:
   #                 print(f"Указан некорректный id = {parent_id} родителя при для изменения иерархии категории с id={category_id}")
   #             else:
   #                 cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
   #                 row = cursor.fetchone()
   #                 if not row:
   #                     print(f"Указан некорректный id = {category_id} категории для изменения")
   #                 else:
   #                     cursor.execute("UPDATE categories SET parent_id= ? WHERE id = ?", (parent_id,category_id,))
   #                     print("Успех!")
   #             conn.commit()
   #         except e:
   #             print(f"Ощибка в базе данных {e}")
   #
   #     def change_name_for_category(self, category_id: int, name: str):
   #         # Обеспечиваем иерархию категорий
   #         try:
   #             cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
   #             row = cursor.fetchone()
   #             if not row:
   #                 print(f"Указан некорректный id = {category_id} категории для изменения")
   #             else:
   #                 cursor.execute("UPDATE categories SET name= ? WHERE id = ?", (name,category_id,))
   #                 print("Успех!")
   #                 conn.commit()
   #         except e:
   #             print(f"Ощибка создания категории {name} в базе данных {e}")
   #
   #     def change_active_category(self, category_id:int) :
   #         cursor.execute("SELECT active FROM categories WHERE id = ?", (category_id,))
   #         row = cursor.fetchone()
   #         if row:
   #             if row.active:
   #                 cursor.execute("UPDATE categories SET active=False WHERE id = ?", (category_id,))
   #             else:
   #                 cursor.execute("UPDATE categories SET active=True WHERE id = ?", (category_id,))
   #
   #             conn.commit()
   #         else:
   #             print(f"Для выбора категрии указан некоррктный id {category_id,}")
   #
   #     def list_categories(self, parent_id:int) -> ArrayType:
   #         cursor.execute("SELECT * FROM categories WHERE active=True and parent_id = ? ORDER BY name ASC", (parent_id,))
   #         rows = cursor.fetchall()
   #
   #         arr = []
   #         for row in rows:
   #             arr.append({'id':row.id,'name':row.name})
   #
   #         return arr
   #
   #     # выбираются категории, начиная с заданной и ниже по иерархии
   #     def tree_categories(self, category_id:int) -> ArrayType:
   #
   #         arr = []
   #         id = category_id
   #         arr.append(id)
   #         arr1 = arr
   #
   #         flag = True
   #         while flag:
   #             cursor.execute("SELECT * FROM categories WHERE active=True and parent_id IN ?", (arr1,))
   #             rows = cursor.fetchall()
   #             arr1 = []
   #             for row in rows:
   #                 arr.append(row.id)
   #                 arr1.append(row.id)
   #
   #             flag = (arr1.count() == 0)
   #
   #         return arr
   #
   # class Users():
   #     def __init__(self):
   #         cursor.execute('''CREATE TABLE IF NOT EXISTS users (
   #             id INTEGER PRIMARY KEY AUTOINCREMENT,
   #             telegram_id INTEGER UNIQUE NOT NULL,
   #             name TEXT NOT NULL,
   #             dt_first DATETIME NOT NULL,         # дата и время когда зарегистрировался
   #             dt_last DATETIME NOT NULL,          # дата и время последнего входа
   #             comment TEXT,                       # комментарий
   #             last_category_id INTEGER DEFAULT 0,  # последняя выбранная категория
   #             last_keyword  TEXT DEFAULT '',       # последняя выбранная ключевая фраза
   #             result TEXT DEFAULT 'random',        #last - последние, first - первые, random - рандомные
   #             max_comments INTEGER DEFAULT 0,      # макс. количество рекомендаций при поиске (0 - все)
   #        )''')
   #
   #         self.categories = Categories()
   #
   #     # # возвращает id юзера по его telegram_id. Если его не нашли - возвратит 0
   #     # def id_user(self, telegram_id:int) -> bool:
   #     #     try:
   #     #         cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
   #     #         row = cursor.fetchone()
   #     #         if row:
   #     #             return row.id
   #     #         else:
   #     #             return 0
   #     #     except e:
   #     #         print(f"Ощибка в базе данных {e}")
   #     #         return 0
   #
   #     # возвращает id юзера по его telegram_id. Если его не нашли - возвратит 0
   #     def get_user_id(self, telegram_id:int) -> int:
   #         try:
   #             cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
   #             row = cursor.fetchone()
   #             if row:
   #                 return row.id
   #             else:
   #                 return 0
   #
   #         except e:
   #             print(f"Ощибка в базе данных {e}")
   #             return 0
   #
   #     def get_user_find_parametrs(self, user_id:int):
   #         try:
   #             cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
   #             row = cursor.fetchone()
   #             if row:
   #                 return {'max_comments':max_comments,'category_id':category_id,'result':result,'keyword':keyword}
   #             else:
   #                 return {}
   #
   #         except e:
   #             print(f"Ощибка в базе данных {e}")
   #             return  {}
   #
   #     def change_find_parametr(self, user_id:int, param:str, value:str) -> str:
   #         if param in ("max_comments","category_id"):
   #             try:
   #                 m = int( value )
   #             except:
   #                 txt = "Введите число, а не строку!"
   #                 return txt
   #         elif param == "result":
   #             val = value.strip().lower()
   #             if not (val in ('last','first''random')):
   #                 txt = "Введите last или first или random"
   #                 return txt
   #
   #         try:
   #             txt = "Успех!"
   #             if param == "max_comments":
   #                 cursor.execute("UPDATE Users SET max_comments = ? WHERE id = ?", (m, user_id,))
   #                 conn.commit()
   #             elif param == "last_category_id":
   #                 cursor.execute("UPDATE Users SET last_category_id = ? WHERE id = ?", (m, user_id,))
   #                 conn.commit()
   #             elif param == "result":
   #                 cursor.execute("UPDATE Users SET result = ? WHERE id = ?", (value.strip().lower(), user_id,))
   #                 conn.commit()
   #             elif param == "last_keyword":
   #                 cursor.execute("UPDATE Users SET last_keyword = ? WHERE id = ?", (value, user_id,))
   #                 conn.commit()
   #             else:
   #                 txt = f"{param} указан некорректно. Нужно указать max_comments или last_category_id или result или last_keyword"
   #
   #         except e:
   #             txt = f"Проблема с базой данных {e}"
   #
   #         return txt
   #
   #     def append_user(self, telegram_id:int, name:str) -> int:
   #         try:
   #             id = self.get_user_id(telegram_id)
   #
   #             if id != 0:
   #                 return id
   #             else:
   #                 cursor.execute("INSERT INTO users (telegram_id, name, dt_first, dt_last ) "
   #                                "VALUES (?, ?, ?, ?)",
   #                                (telegram_id, name, datetime.now().isoformat(), datetime.now().isoformat()))
   #                 conn.commit()
   #                 id = cursor.lastrowid
   #                 return id
   #
   #         except e:
   #             print(f"Ощибка в базе данных {e}")
   #             return 0
   #
   # class Comments():
   #     def __init__(self):
   #         cursor.execute('''CREATE TABLE IF NOT EXISTS comments (
   #             id INTEGER PRIMARY KEY AUTOINCREMENT,
   #             user_id INTEGER
   #             category_id INTEGER
   #             name TEXT NOT NULL,
   #             comment TEXT NOT NULL,
   #             dt DATATIME NOT NULL,     # дата и время когда изменил запись
   #         )
   #         ''')
   #         conn.commit()
   #
   #         self.users = Users()
   #
   #     def add_comment(self,user_id:int,category_id:int,name:str,comment:str):
   #         cursor.execute("INSERT INTO comments (user_id,category_id,name,comment,dt) VALUES (?, ?, ?, ?, ?)",
   #                        (user_id, category_id, name, comment, datetime.now().isoformat(), ))
   #         conn.commit()
   #
   #     def find_comments(self,user_id:int,from_user_id:int=0) -> str:
   #
   #         if from_user_id > 0 and self.users.is_exist_user(from_user_id):
   #             # Создаем временную таблицу для параметров
   #             cursor.execute("""
   #                 DROP TABLE IF EXISTS temp_params_from_user;
   #                 CREATE TEMP TABLE temp_params_from_user (from_user_id INTEGER)
   #                 """)
   #             cursor.execute("INSERT INTO temp_params_from_user (from_user_id) VALUES (?)", (from_user_id,))
   #
   #             # Используем временную таблицу в запросе
   #             cursor.execute("""
   #             CREATE VIEW IF NOT EXISTS from_comments AS
   #             SELECT c.* FROM comments c, temp_params_from_user p WHERE c.user_id = p.from_user_id
   #             """)
   #         else:
   #             cursor.execute("""
   #              CREATE VIEW IF NOT EXISTS from_comments AS
   #              SELECT c.* FROM comments c
   #              """)
   #
   #         # получаем параметры поиска result и max_comments потом - last_category_id,last_keyword
   #         params = self.users.get_user_find_parametrs(user_id)
   #         max_comments = params.get('max_comments', 0)
   #         result = params.get('result', 'random')
   #
   #         if max_comments > 0 and (result == 'first' or result == 'last'):
   #             # Создаем временную таблицу для параметров
   #             cursor.execute("""
   #                 DROP TABLE IF EXISTS temp_params_max_comments;
   #                 CREATE TEMP TABLE temp_params_max_comments (max_comments INTEGER)
   #             """)
   #
   #             cursor.execute("INSERT INTO temp_params_max_comments (max_comments) VALUES (?)", (max_comments,))
   #
   #             # Используем временную таблицу в запросе
   #             if result == 'first':
   #               cursor.execute("""
   #               CREATE VIEW IF NOT EXISTS max_comments AS
   #               SELECT c.* FROM from_comments c, temp_params_max_comments p ORDER BY dt ASC LIMIT p.max_comments
   #               """)
   #             else:
   #                 cursor.execute("""
   #                  CREATE VIEW IF NOT EXISTS max_comments AS
   #                  SELECT c.* FROM from_comments c, temp_params_max_comments p ORDER BY dt DSC LIMIT p.max_comments
   #                  """)
   #
   #         else:
   #             cursor.execute("""
   #                CREATE VIEW IF NOT EXISTS max_comments AS
   #                SELECT c.* FROM from_comments c
   #                """)
   #
   #         #получаем параметры поиска last_category_id
   #         last_category_id = params.get('last_category_id',0)
   #
   #         if last_category_id > 0 :
   #             #Получаем массив с подкатегориями
   #             arr_category_id = self.categories.tree_categories(last_category_id)
   #
   #             # Создаем временную таблицу для параметров
   #             cursor.execute("""
   #                  DROP TABLE IF EXISTS temp_params_category_id;
   #                  CREATE TEMP TABLE temp_params_category_id (category_id INTEGER)
   #              """)
   #             for cat_id in arr_category_id:
   #                 cursor.execute("INSERT INTO temp_params_category_id (category_id) VALUES (?)", (cat_id,))
   #
   #             # Используем временную таблицу в запросе
   #             cursor.execute("""
   #              CREATE VIEW IF NOT EXISTS category_id AS
   #              SELECT c.* FROM max_comments c
   #              INNER JOIN temp_params_category_id p ON c.category_id = p.category_id
   #              """)
   #         else:
   #             cursor.execute("""
   #               CREATE VIEW IF NOT EXISTS category_id AS
   #               SELECT c.* FROM max_comments c
   #               """)
   #
   #         # получаем параметры поиска keyword
   #         keyword = params.get('last_keyword', '')
   #         arr_keyword = []
   #         arr_keyword1 = keyword.split()
   #         for kword1 in arr_keyword1:
   #             arr_keyword2 = kword1.split(';')
   #             for kword2 in arr_keyword2:
   #                 arr_keyword3 = kword2.split(',')
   #                for kword3 in arr_keyword3:
   #                    if kword3.count()>0:
   #                         arr_keyword.append(kword3)
   #
   #         if len(arr_keyword) > 0:
   #             len_arr = len(arr_keyword)
   #             # Создаем временную таблицу для параметров
   #             cursor.execute("""
   #                   DROP TABLE IF EXISTS temp_params_keyword;
   #                   CREATE TEMP TABLE temp_params_keyword (keyword TEXT, len_arr INT)
   #               """)
   #             for kword in arr_keyword:
   #                 cursor.execute("INSERT INTO temp_params_category_id (keyword,len_arr) VALUES (?,?)", (kword,len_arr))
   #
   #             # Используем временную таблицу в запросе: вначале создаем временную таблицу с id тех рекомендаций,
   #             # в которых есть все слова без разделителей ';',',',' '
   #             cursor.execute("""
   #                CREATE VIEW IF NOT EXISTS comments_id_kword AS
   #                SELECT c.id AS id, COUNT(p.keyword) AS cnt, MAX(p.len_arr) AS len_arr FROM category_id c
   #                INNER JOIN temp_params_keyword p ON (c.name || ' ' || c.comment LIKE '%' || p.keyword || '%')
   #                GROUP BY
   #                     c.id
   #                HAVING
   #                     HAVING COUNT(p.keyword) = MAX(p.len_arr)
   #                """)
   #             cursor.execute("""
   #                 CREATE VIEW IF NOT EXISTS comments_kword AS
   #                 SELECT c.* FROM category_id c
   #                 INNER JOIN comments_id_kword c_id ON (c.id = c_id.id)
   #                  """)
   #         else:
   #             cursor.execute("""
   #                 CREATE VIEW IF NOT EXISTS comments_kword AS
   #                 SELECT c.* FROM category_id c
   #                 """)
   #         cursor.execute("""
   #               SELECT c.user_id, c.category_id, c.name AS name, c.comment AS comment, c.dt AS dat, usr.name AS user, usr.comment AS about_user, cat.name AS category FROM comments_kword c
   #                     INNER JOIN user usr ON (c.user_id = usr.id)
   #                     INNER JOIN categories cat ON (c.category_id = cat.id)
   #                """)
   #         rows = cursor.fetchall()
   #         if max_comments > 0:
   #             if max_comments > len(rows):
   #                 max_comments = len(rows)
   #         else:
   #             max_comments = len(rows)
   #
   #         i = 0
   #         arr_int = []
   #         while i < max_comments:
   #             arr_int.append(i)
   #             i = i + 1
   #
   #         # Осталось учесть случай когда result='random'
   #         if result == 'random':
   #             random.shuffle(arr_int)
   #
   #         txt = ""
   #         for i in range(len(arr_int)):
   #             txt = txt + f"{rows[arr_int[i]]}" + "\n"
   #
   #         return txt

