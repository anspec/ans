import random
import telebot
from telebot import types
from datetime import datetime
import threading
import time
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


bot = telebot.TeleBot("7661416982:AAHuQxJsWj4RNzjV6nyh_PGQBH3yTaWNsRA")

# первоначальный массив для хранения вопросов для их дальнейшего исключения
X_questions = []
for quest in questions:
    X_questions.append(quest)

# Массив для хранения вопросов (они будут не по порядку)
X_quest = {}
# Массив для хранения ответов
X_answer = {}

# Блок А: Пользователь вводит ответ
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    X_quest[chat_id] = []  # Инициализация массива вопросов для каждого пользователя
    X_answer[chat_id] = []  # Инициализация массива ответов для каждого пользователя

    question = random.choice(X_questions)
    X_quest[chat_id].append(question)
    X_questions.remove(question)

    bot.send_message(chat_id, question["question"])

@bot.message_handler(func=lambda message: True)
def handle_ans_input(message):
    chat_id = message.chat.id
    chat_answer = message.text

    # Создаем инлайн-клавиатуру
    markup = InlineKeyboardMarkup()
    for ans in question["options"]:
        markup.add(InlineKeyboardButton(ans, callback_data=ans))

    markup.add(InlineKeyboardButton("Закончить", callback_data="finish"))

    # Отправляем сообщение с кнопками
    bot.send_message(chat_id, "Выберите верный ответ!", reply_markup=markup)

# Обработка инлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    chat_id = call.message.chat.id
    X_answer[chat_id].append(call.data)

    if call.data != "finish" and len(X_questions)>0:
        # Блок А: Возвращаем пользователя для ввода нового вопроса, предыдущий удаляем чтобы не повторять
        question = random.choice(X_questions)
        bot.send_message(chat_id, question["question"])

    else:
        # Блок Б: Вычисляем количество верных ответов и количество вопросов
        total_question = len(questions)
        total_answer = len(X_quest.get(chat_id, []))  # Количество вопросов, на которые ответил пользователь
        #total_answer = len(X_quest[chat_id])
        good_answer = 0

        # Подсчет правильных ответов
        good_answer = 0
        for i, question in enumerate(X_quest.get(chat_id, [])):  # Перебираем вопросы пользователя
            if i < len(X_answer.get(chat_id, [])):  # Проверяем, что индекс ответа существует
                if question["answer"] == X_answer[chat_id][i]:  # Сравниваем ответ
                    good_answer += 1

        #for question in X_quest[chat_id]:
        #    if question["answer"] == X_answer[chat_id][X_quest[chat_id].index(question)]:
        #        good_answer+=1
        bot.send_message(chat_id, f"Всего вопросов было {total_question} ответил на {total_answer} из них верно на {good_answer}")

        # Очищаем массивы вопросов и ответов для данного пользователя
        X_quest.pop(chat_id, None)
        X_answer.pop(chat_id, None)


bot.polling(none_stop=True)
