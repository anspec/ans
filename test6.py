import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot("7661416982:AAHuQxJsWj4RNzjV6nyh_PGQBH3yTaWNsRA")

# Массив для хранения введенных чисел
X = {}


# Блок А: Пользователь вводит число
@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    X[chat_id] = []  # Инициализация массива чисел для каждого пользователя
    bot.send_message(chat_id, "Введите число:")


@bot.message_handler(func=lambda message: True)
def handle_number_input(message):
    chat_id = message.chat.id

    # Проверяем, является ли введенное значение числом
    try:
        number = float(message.text)  # Преобразуем введенное сообщение в число
        if chat_id not in X:
            X[chat_id] = []
        X[chat_id].append(number)  # Сохраняем число в массив

        # Создаем инлайн-клавиатуру
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Продолжить", callback_data="continue"))
        markup.add(InlineKeyboardButton("Закончить", callback_data="finish"))

        # Отправляем сообщение с кнопками
        bot.send_message(chat_id, "Продолжим ввод еще ?", reply_markup=markup)

    except ValueError:
        bot.send_message(chat_id, "Пожалуйста, введите число.")


# Обработка инлайн-кнопок
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id

    if call.data == "continue":
        # Блок А: Возвращаем пользователя для ввода нового числа
        bot.send_message(chat_id, "Введите еще одно число:")

    elif call.data == "finish":
        # Блок Б: Вычисляем сумму чисел
        total_sum = sum(X.get(chat_id, []))
        bot.send_message(chat_id, f"Сумма всех чисел: {total_sum}")

        # Очищаем массив для данного пользователя
        X.pop(chat_id, None)


bot.polling(none_stop=True)
