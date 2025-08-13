from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
    MessageHandler,
    Filters
)

def create_main_menu_keyboard():
  keyboard = [
      [InlineKeyboardButton("🛍 Показать погоду", callback_data='weather'),
       InlineKeyboardButton("👤 Информация", callback_data='info')],
  ]
  return InlineKeyboardMarkup(keyboard)

def start(update: Update, context: CallbackContext) -> None:
  user = update.effective_user
  update.message.reply_text(
      f"👋 Привет, {user.first_name}! Потести в тг мои кнопки!",
      reply_markup=create_main_menu_keyboard()
  )

def button_click(update: Update, context: CallbackContext) -> None:
  query = update.callback_query
  query.answer()
  data = query.data

  if data == 'weather':
    keyboard_back = [
        [InlineKeyboardButton("Назад", callback_data='back_to_menu')],
    ]
    query.message.reply_text(
        "Показать погоду",
        reply_markup=InlineKeyboardMarkup(keyboard_back)
    )

  elif data == 'info':
    query.message.reply_text(
        "Это учебный бот",
    )

  elif data == 'back_to_menu':
    context.user_data['awaiting_input'] = 'phone'
    query.message.reply_text(
        "Назад",
        reply_markup=create_main_menu_keyboard()
    )

def main():
  token = "7661416982:AAHuQxJsWj4RNzjV6nyh_PGQBH3yTaWNsRA"
  updater = Updater(token)
  dispatcher = updater.dispatcher
  dispatcher.add_handler(CommandHandler("Start",start))
  dispatcher.add_handler(CallbackQueryHandler(button_click))
  updater.start_polloing()
  print("Бот запущен")
  updater.idle()
#
if __name__ == "__main__":
  main()

