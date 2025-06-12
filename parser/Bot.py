import telebot
import sqlite3

TOKEN = "7895943641:AAH1yl525hfyw0sA4kV1RK4GnU6bqHCffIU"
bot = telebot.TeleBot(TOKEN)
DB_path = "product.db"

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Я бот, который выдаёт товары с WB!")

@bot.message_handler(commands=['product'])
def product(message):
  parts = message.text.split()
  if len(parts) != 2:
    bot.send_message(message.chat.id, "Неверный формат команды! Верный формат - /product <ID>")
    return
  try:
    product_id = int(parts[1])
  except:
    bot.send_message(message.chat.id, "ID должен быть числом!")
    return

  conn = sqlite3.connect(DB_path)
  cursor = conn.cursor()

  cursor.execute("SELECT name, image_path FROM product_list WHERE id = ?", (product_id,))

  result = cursor.fetchone()
  conn.close()

  if result:
    name, image_path = result
    if result:
      name, image_path = result
      with open(image_path, "rb") as image:
        bot.send_photo(message.chat.id, image)
        bot.send_message(message.chat.id,name)
    else:
      bot.send_message(message.chat.id, "Результат по данному запросу не был найден")

bot.polling()