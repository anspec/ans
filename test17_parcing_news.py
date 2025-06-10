import random
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from bs4 import BeautifulSoup
import sqlite3

# Вопросы и ответы
questions = [
    {
        "question": "Какой язык программирования используется для разработки этой программы?",
        "options": ["Java", "Python", "C++"],
        "answer": "Python"
    },
    {
        "question": "Как называется самая большая планета Солнечной системы?",
        "options": ["Земля", "Юпитер", "Марс"],
        "answer": "Юпитер"
    },
    {
        "question": "Какой цвет получается при смешивании синего и красного?",
        "options": ["Фиолетовый", "Зеленый", "Оранжевый"],
        "answer": "Фиолетовый"
    },
    {
        "question": "Кто написал роман 'Война и мир'?",
        "options": ["Фёдор Достоевский", "Лев Толстой", "Антон Чехов"],
        "answer": "Лев Толстой"
    },
    {
        "question": "Какой океан является самым большим на Земле?",
        "options": ["Атлантический", "Тихий", "Индийский"],
        "answer": "Тихий"
    },
    {
        "question": "Как называется столица Франции?",
        "options": ["Берлин", "Париж", "Рим"],
        "answer": "Париж"
    },
    {
        "question": "Сколько минут в одном часе?",
        "options": ["60", "100", "90"],
        "answer": "60"
    },
    {
        "question": "Как называется первая планета от Солнца?",
        "options": ["Земля", "Меркурий", "Венера"],
        "answer": "Меркурий"
    },
    {
        "question": "Как называется процесс, при котором растения вырабатывают кислород?",
        "options": ["Фотосинтез", "Испарение", "Дыхание"],
        "answer": "Фотосинтез"
    },
    {
        "question": "Какой вид искусства связан с Микеланджело?",
        "options": ["Литература", "Живопись", "Музыка"],
        "answer": "Живопись"
    }
]
# Для хранения данных пользователей
user_data = {}

# Создаем бота
bot = telebot.TeleBot("7661416982:AAHuQxJsWj4RNzjV6nyh_PGQBH3yTaWNsRA")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Я бот, чем я могу вам помочь?")

@bot.message_handler(commands=['news'])
def send_news(message):
    conn = sqlite3.connect("newstmsk.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS news (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   title TEXT,
                   link TEXT,
                   time TEXT,
                   team TEXT 
                   )''')

    cursor.execute("DELETE FROM news")
    conn.commit()

    url = "https://tomsk.ru/"
    response = requests.get(url)
    response.encoding = 'utf-8'
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        titles = soup.find_all('div', class_="post-item__info", limit=5)

        for i in range(len(titles)):  # 0, 1, 2, 3, 4
            title_div = titles[i]

            stru = {'title':'','link':'','time':'','team':''}
            for j in range(len(title_div.contents)):  # 0, 1, 2, 3, 4
                title_div_ch = title_div.contents[j]

                if title_div_ch.name == 'div':
                    stru_key = ''
                    if title_div_ch.has_attr("class"):
                       if 'post-item__categories' in title_div_ch["class"]:
                           stru_key = 'team'
                       elif 'post-item__time' in title_div_ch["class"]:
                               stru_key = 'time'
                       elif 'post-item__title' in  title_div_ch["class"]:
                               stru_key = 'title'
                       else:
                           continue
                    if stru_key != '':
                        title = title_div_ch.contents[0]
                        if title.name=='a' and title.has_attr("href"):
                            link = title["href"]
                            if link.startswith("/"):
                                link = url.rstrip("/") + link

                            if stru_key=='title':
                                stru['link'] = link
                            stru[stru_key] = title.text.strip()
                        else:
                            stru[stru_key] = title_div_ch.text.strip()

            cursor.execute("INSERT INTO news (title,link,team,time) VALUES (?,?,?,?)",
                           (stru['title'], stru['link'], stru['team'], stru['time']))
            print(f"{stru['team']}: {stru['title']} от {stru['time']} Ссылка: {stru['link']}")
            conn.commit()

            bot.send_message(message.chat.id, f"{i + 1}. тема: {stru['team']}: {stru['title']} от {stru['time']}\n Ссылка: {stru['link']}")

    else:
        print(f"Ошибка при загрузке страницы {response.status_code}")
        bot.send_message(message.chat.id, "Не удалось получить данные о новостях в Томске!")

    conn.close()

# /kviz - Начало квиза
@bot.message_handler(commands=['kviz'])
def kviz_handler(message):
    chat_id = message.chat.id
    # Инициализация данных пользователя
    user_data[chat_id] = {
        "questions": random.sample(questions, len(questions)),  # Перемешиваем список вопросов
        "current_question": None,
        "answers": [],
        "correct_count": 0
    }
    send_next_question(chat_id)

# Отправка следующего вопроса
def send_next_question(chat_id):
    user = user_data.get(chat_id)
    if not user or not user["questions"]:
        bot.send_message(chat_id, "Вопросы закончились!")
        show_results(chat_id)
        return

    # Берем следующий вопрос
    question = user["questions"].pop(0)
    user["current_question"] = question

    # Создаем инлайн-клавиатуру
    markup = InlineKeyboardMarkup()
    for option in question["options"]:
        markup.add(InlineKeyboardButton(option, callback_data=option))

    # Отправляем вопрос
    bot.send_message(chat_id, question["question"], reply_markup=markup)

# Обработка инлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_query_handler(call):
    chat_id = call.message.chat.id
    user = user_data.get(chat_id)

    if not user or not user["current_question"]:
        return

    selected_answer = call.data
    correct_answer = user["current_question"]["answer"]

    # Проверка ответа
    if selected_answer == correct_answer:
        user["correct_count"] += 1
        bot.send_message(chat_id, "Правильно!")
    else:
        bot.send_message(chat_id, f"Неправильно! Правильный ответ: {correct_answer}")

    # Переходим к следующему вопросу
    send_next_question(chat_id)

# Вывод результатов
def show_results(chat_id):
    user = user_data.get(chat_id)
    if not user:
        return

    total_questions = len(questions)
    correct_count = user["correct_count"]

    bot.send_message(chat_id, f"Игра окончена! Вы ответили правильно на {correct_count} из {total_questions} вопросов.")

# Запуск бота
bot.polling(none_stop=True)

