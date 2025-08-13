import requests #Для выполнения HTTP-запросов к внешним API
import logging #Для настройки системы логирования
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,KeyboardButton,ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext,MessageHandler,Filters,ConversationHandler

# Главное меню
def create_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("👤 Профиль клиента", callback_data='profile')],
        [InlineKeyboardButton("🛍️ Каталог", callback_data='catalog')],
        [InlineKeyboardButton("📞 Контакты", callback_data='contacts')]
    ]
    return InlineKeyboardMarkup(keyboard)


# Меню профиля
def create_profile_keyboard():
    keyboard = [
        [InlineKeyboardButton("📝 Изменить имя", callback_data='edit_name')],
        [InlineKeyboardButton("📱 Изменить телефон", callback_data='edit_phone')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back_to_menu')]
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
    elif input_type == 'name':
        return ReplyKeyboardMarkup(
            [[KeyboardButton("🚫 Пропустить")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    context.user_data['profile'] = {
        'name': user.first_name,
        'phone': None
    }

    update.message.reply_text(
        f"👋 Добро пожаловать, {user.first_name}!",
        reply_markup=create_main_menu_keyboard()
    )


def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    data = query.data

    if data == 'profile':
        profile = context.user_data.get('profile', {})
        text = f"📝 Ваш профиль:\nИмя: {profile['name']}\nТелефон: {profile.get('phone', 'не указан')}"
        query.edit_message_text(text=text, reply_markup=create_profile_keyboard())

    elif data == 'edit_name':
        context.user_data['awaiting_input'] = 'name'
        query.message.reply_text(
            "📝 Введите ваше имя:",
            reply_markup=create_data_input_keyboard('name')
        )

    elif data == 'edit_phone':
        context.user_data['awaiting_input'] = 'phone'
        query.message.reply_text(
            "📱 Нажмите кнопку ниже, чтобы поделиться номером:",
            reply_markup=create_data_input_keyboard('phone')
        )

    elif data == 'back_to_menu':
        query.edit_message_text(
            text="Главное меню:",
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
            reply_markup=create_profile_keyboard()
        )


# def handle_text(update: Update, context: CallbackContext) -> None:
#     if context.user_data.get('awaiting_input') == 'name':
#         new_name = update.message.text
#         context.user_data['profile']['name'] = new_name
#         context.user_data.pop('awaiting_input', None)
#         profile = context.user_data['profile']
#         update.message.reply_text(
#             f"✅ Имя изменено на {new_name}!",
#             reply_markup=ReplyKeyboardRemove()
#         )
#     elif context.user_data.get('awaiting_input') == 'phone':
#         new_phone = update.message.text
#         context.user_data['profile']['phone'] = new_phone
#         context.user_data.pop('awaiting_input', None)
#         profile = context.user_data['profile']
#         update.message.reply_text(
#             f"✅ Телефон изменен на {new_phone}!",
#             reply_markup=ReplyKeyboardRemove()
#         )
#     update.message.reply_text(
#         text=f"📝 Ваш профиль:\nИмя: {profile['name']}\nТелефон: {profile.get('phone', 'не указан')}",
#      #   text="Обновленный профиль:",
#         reply_markup=create_profile_keyboard()
#     )


def main():
    TOKEN = "7661416982:AAHuQxJsWj4RNzjV6nyh_PGQBH3yTaWNsRA"
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(button_click))
    dispatcher.add_handler(MessageHandler(Filters.contact, handle_contact))
#
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()