import telebot
from openai import OpenAI
from gtts import gTTS
import os

# Инициализация OpenAI клиента
client = OpenAI(
    api_key="sk-eojihWMYuwlwO4oNjNMX8DbkkkBtLg7I",
    base_url="https://api.proxyapi.ru/openai/v1",
)

# Инициализация бота с вашим токеном
bot = telebot.TeleBot("7567816356:AAFaUrQ0zD0VzQmW44C2_I8PGy7XRX7xBXE")


def chat_with_ai(initial_message):
    messages = [{"role": "user", "content": initial_message}]

    chat_completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    reply = chat_completion.choices[0].message.content
    return reply


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_message = message.text
    reply = chat_with_ai(user_message)

    # Отправка текстового ответа
    bot.send_message(message.chat.id, reply)

    # Преобразование текста в аудио
    tts = gTTS(text=reply, lang='en')
    audio_file = "response.ogg"
    tts.save(audio_file)

    # Отправка голосового сообщения
    with open(audio_file, 'rb') as audio:
        bot.send_voice(message.chat.id, audio)

    # Удаление временного аудиофайла
    os.remove(audio_file)


# Запуск бота
bot.polling()