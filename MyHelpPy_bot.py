import random
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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

# Создаем бота
bot = telebot.TeleBot("7661416982:AAHuQxJsWj4RNzjV6nyh_PGQBH3yTaWNsRA")

# Для хранения данных пользователей
user_data = {}

# /start - Начало работы
@bot.message_handler(commands=['start'])
def start_handler(message):
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
