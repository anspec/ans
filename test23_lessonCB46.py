import requests #Для выполнения HTTP-запросов к внешним API
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,KeyboardButton,ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext,MessageHandler,Filters,ConversationHandler

TOKEN = "7567816356:AAFaUrQ0zD0VzQmW44C2_I8PGy7XRX7xBXE"
OPENWEATHER_API_KEY: str = "d468b09e4ed93a30bb7c724708b1e800"

# 1. Inline-кнопки
# - Создай под приветственным сообщением меню с 2мя inline-кнопками:
#     - Кнопка «Показать погоду» с callback_data='weather'.
#     - Кнопка «Информация» с callback_data='info'.
# - Напиши функцию button_click, которая:
#     - При нажатии на «Погоду» выводит сообщение: «Функция в разработке» с кнопкой «Назад».
#     - При нажатии на «Информацию» отправляет текст: «Это учебный бот».
# 2. Reply-кнопки с запросом контакта
# - Создай Reply-клавиатуру с кнопками:
#     - «Мой профиль» (обычная текстовая кнопка).
#     - «Отправить контакт» (кнопка с `request_contact=True`).
# - Добавь параметры:
#     - `resize_keyboard=True` (автоматический размер кнопок).
#     - `one_time_keyboard=True` (скрыть клавиатуру после нажатия).
# 3. Кнопка с URL
# - Добавь в главное меню inline-кнопку «Перейти в магазин», которая открывает ссылку https://zerocoder.ru/
# - Настрой, чтобы кнопка отображалась в одной строке с кнопкой «Информация»
# Меню профиля

def create_main_menu_keyboard():
  keyboard = [
      [InlineKeyboardButton("🛍 Показать погоду", callback_data='weather')],
      [InlineKeyboardButton("👤 Информация", callback_data='info'),
       InlineKeyboardButton("👤 Перейти в магазин", url='https://zerocoder.ru/')],
      [InlineKeyboardButton("👤 Контакт", callback_data='contact')],
  ]
  return InlineKeyboardMarkup(keyboard)

def create_reply_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 Мой профиль", callback_data='my_profile')],
        [InlineKeyboardButton("📱 Отправить контакт", callback_data='edit_phone')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Reply-клавиатура для ввода данных
def create_data_input_keyboard(input_type: str):
    if input_type == 'phone':
        return ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Отправить номер", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
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
        reply_markup=create_main_menu_keyboard())

  elif data == 'back_to_menu':
    context.user_data['awaiting_input'] = 'phone'
    query.message.reply_text(
        "Назад",
        reply_markup=create_main_menu_keyboard())

  elif data == 'contact':
    query.message.reply_text(
        text="Выберите действие:",
        reply_markup=create_reply_keyboard())

  elif data == 'my_profile':
      profile = context.user_data['profile']
      query.message.reply_text(
          text=f"📝 Ваш профиль:\nИмя: {profile['name']}\nТелефон: {profile.get('phone', 'не указан')}",
          #    text="Обновленный профиль:",
          reply_markup=create_main_menu_keyboard()
      )

  elif data == 'edit_phone':
      context.user_data['awaiting_input'] = 'phone'
      query.message.reply_text(
          "📱 Нажмите кнопку ниже, чтобы поделиться номером:",
          reply_markup=create_data_input_keyboard('phone'))


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    context.user_data['profile'] = {
        'name': user.first_name,
        'phone': None
    }
    update.message.reply_text(
          f"👋 Привет, {user.first_name}! Потести в тг мои кнопки!",
          reply_markup=create_main_menu_keyboard()
    )

def handle_contact(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('awaiting_input') == 'phone':
        phone_number = update.message.contact.phone_number
        context.user_data['profile']['phone'] = phone_number
        profile = context.user_data['profile']
        # update.message.reply_text(
        #     "✅ Номер успешно сохранен!",
        #     reply_markup=ReplyKeyboardRemove()
        # )
        update.message.reply_text(
        text=f"📝 Ваш профиль:\nИмя: {profile['name']}\nТелефон: {profile.get('phone', 'не указан')}",
        #    text="Обновленный профиль:",
            reply_markup=create_profile_keyboard()
        )

def handle_text(update: Update, context: CallbackContext) -> None:
    if context.user_data.get('awaiting_input') == 'name':
        new_name = update.message.text
        context.user_data['profile']['name'] = new_name
        context.user_data.pop('awaiting_input', None)
        profile = context.user_data['profile']
        update.message.reply_text(
            f"✅ Имя изменено на {new_name}!",
            reply_markup=ReplyKeyboardRemove()
        )
    elif context.user_data.get('awaiting_input') == 'phone':
        new_phone = update.message.text
        context.user_data['profile']['phone'] = new_phone
        context.user_data.pop('awaiting_input', None)
        profile = context.user_data['profile']
        update.message.reply_text(
            f"✅ Телефон изменен на {new_phone}!",
            reply_markup=ReplyKeyboardRemove()
        )
    update.message.reply_text(
        text=f"📝 Ваш профиль:\nИмя: {profile['name']}\nТелефон: {profile.get('phone', 'не указан')}",
     #   text="Обновленный профиль:",
        reply_markup=create_profile_keyboard()
    )

def main():
    TOKEN = "7661416982:AAHuQxJsWj4RNzjV6nyh_PGQBH3yTaWNsRA"
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))      #через /start
    dispatcher.add_handler(CallbackQueryHandler(button_click))
    dispatcher.add_handler(MessageHandler(Filters.contact, handle_contact))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command,handle_text))

    # dispatcher.add_handler(CommandHandler("start",start))#через /start
    # dispatcher.add_handler(CallbackQueryHandler(button_click, pattern='^(currency|back_to_menu|close)$'))#через кнопку

    updater.start_polling()
    #logger.info("Бот запущен и готов к работе")
    updater.idle()

if __name__=='__main__':
    main()

