#Настрой с помощью декоратора вывод приветственного сообщения пользователю твоего бота при написании им команды `/start`;
#Пропиши команду, которая запускает работу бота, используя метод `bot.polling()` ;
#Напиши программу, чтобы бот реагировал на любые сообщения стандартным ответом, и протестируй ее работу;
#Напиши программу, чтобы бот реагировал на определённые слова внутри текста, и протестируй ее работу;
#Создай функцию, подсчитывающую количество слов, символов и символов без пробелов в сообщениях пользователя, и протестируй ее работу;
#Напиши программу, чтобы по команде от пользователя: `/random_dish`, бот присыл случайно выбранное
# блюдо, и протестируй ее работу. Каждый раз должно подбираться новое случайное значение из списка,
# состоящего из минимум 10 элементов.

import random
import telebot

bot = telebot.TeleBot("7661416982:AAHuQxJsWj4RNzjV6nyh_PGQBH3yTaWNsRA")

menu = ["Каша овсяная","Омлет","Блинчики с мясом","Блинчики с творогом","Рагу с говядиной","Суп сырный","Борщ украинский","Котлеты куриные на пару","Уха из семги","Красная икра","Крабы","Пиво с раками"]
# Блок А: Пользователь вводит ответ
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    bot.send_message(chat_id,
                     f"Привет, дорогой друг! Напиши мне что-нибудь\n"
                     "Учти, что по команде /up фраза я верну твою фразу большими буквами\n"
                     "по команде /down фраза я верну твою фразу маленькими буквами\n"
                     "по команде /stat фраза я верну количество слов, символов и символов без пробелов во фразе\n"
                     "по команде /menu я верну одно случайное блюдо из заранее созданного списка\n"
                     "в прочей твоей фразе я допишу вначале, что не понял смысла фразы <фраза>"
                     )

@bot.message_handler(commands=['up'])
def up_handler(message):
    chat_id = message.chat.id
    chat_answer = message.text
    chat_answer = chat_answer.upper()

    bot.send_message(chat_id, chat_answer)

@bot.message_handler(commands=['down'])
def down_handler(message):
    chat_id = message.chat.id
    chat_answer = message.text
    chat_answer = chat_answer.lower()

    bot.send_message(chat_id, chat_answer)

@bot.message_handler(commands=['stat'])
def stat_handler(message):
    chat_id = message.chat.id
    chat_ans = message.text
    chat_answer = chat_ans[len('stat')+2:]
    chat_answer = chat_answer.strip()
    chat_answer1 = chat_answer.replace(" ","")
    count_words = len(chat_answer.split(" "))
    count_symbol = len(chat_answer)
    count_symbol1 = len(chat_answer1)
    bot.send_message(chat_id, f"во фразе {chat_answer} слов {count_words} всего симоволов {count_symbol} в т.ч. не пробелов {count_symbol1}")

@bot.message_handler(commands=['menu'])
def menu_handler(message):
    global menu
    chat_id = message.chat.id
    ans = random.choice(menu)

    bot.send_message(chat_id, f"Предлагаю {ans}")

@bot.message_handler(func=lambda message: True)
def handle_ans_input(message):
    chat_id = message.chat.id
    chat_answer = message.text

     # Отправляем сообщение с кнопками
    bot.send_message(chat_id, f"Не понял смысла фразы {chat_answer}!")

bot.polling(none_stop=True)
