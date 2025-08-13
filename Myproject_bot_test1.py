import os  # Для взаимодействия с файловой системой
from dotenv import load_dotenv #config.env
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler
import random

load_dotenv("config.env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print(TOKEN)

# States
START, FIND_CAT, FIND_CAT_ONE, FIND_CAT_MANY, CANCEL = range(5)


def start(update: Update, context: CallbackContext) -> int:
    #print("старт")
    keyboard = [
        [InlineKeyboardButton("FindCat", callback_data="find_cat")],
        [InlineKeyboardButton("End", callback_data="end")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    elif update.callback_query:
        update.callback_query.message.reply_text("Выберите действие:", reply_markup=reply_markup)

    return START

def button_handler(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()

    print(f"query.data={query.data}")
    if query.data == "find_cat":
        return find_cat(update, context)
    elif query.data == "end":
        return end(update, context)
    elif query.data.startswith("choose"):
        return start(update, context)
    elif query.data.startswith("edit"):
        return start(update, context)
    else:
        return start(update, context)


# --- FindCat Process ---
def find_cat(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    print(f"update.callback_query={update.callback_query}")
    if query:
        query.answer()
        query.edit_message_text("Введите ID или ключевое слово (find_cat):")
    else:
        update.message.reply_text("Введите ID или ключевое слово (find_cat):")
    return FIND_CAT

def handle_cat_input(update: Update, context: CallbackContext) -> int:

    #query = update.callback_query
    #query.answer()

    random_choice = random.randint(0, 3)
    #Варианты: 0 - Отказ
    #          1 - Нашли 1 категорию, она устраивает, нужно выбрать действие с ней
    #          2 - Нашли 1 категорию, она не устраивает, по ней нужно формировать список
    #          3 - Нашли много категорий, из которых нужно выбрать 1 для дальнейших действий
    print(f"random_choice={random_choice}")
    #update.message.reply_text(f"handle_cat_input: query.data={query.data} random_choice={random_choice}")
    if random_choice == 0:
        return start(update, context)
    elif random_choice == 1:
        #update.message.reply_text("Нашли единственную категорию.")
        keyboard = [
            [InlineKeyboardButton("Использовать", callback_data="choose_0")],
            [InlineKeyboardButton("Использовать родителя", callback_data="choose_parent")],
            [InlineKeyboardButton("Редактировать", callback_data="edit_0")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Выберите действие(1):", reply_markup=reply_markup)
        return FIND_CAT_ONE
    elif random_choice == 2:
        #update.message.reply_text("Нашли единственную категорию.")
        keyboard = [
             [InlineKeyboardButton("Выбрать подкатегорию", callback_data="subcategory")],
             [InlineKeyboardButton("Выбрать из категорий рядом", callback_data="near")],
             [InlineKeyboardButton("Выбрать главные категории", callback_data="main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Выберите действие(3):", reply_markup=reply_markup)
        return FIND_CAT_MANY
    elif random_choice == 3:
        #update.message.reply_text("Нашли много категорий.")
        keyboard = [
            [InlineKeyboardButton("Выбрать 1", callback_data="choose_1")],
            [InlineKeyboardButton("Выбрать 2", callback_data="choose_2")],
            [InlineKeyboardButton("Выбрать 3", callback_data="choose_3")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Выберите действие(4):", reply_markup=reply_markup)

        return FIND_CAT_ONE

    else:
        update.message.reply_text("Не нашли ни одной категории. Попробуйте снова.")
        return FIND_CAT

def find_cat_one(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    data = query.data

    if data.startswith("choose"):
        query.edit_message_text("Процесс завершен. Возвращаемся в начало.")
        # Возвращаемся к состоянию стартового экрана
        return start(update, context)
        #return START

    elif data.startswith("edit"):
        query.edit_message_text("Процесс завершен. Возвращаемся в начало.")
        # Возвращаемся к состоянию стартового экрана

        return start(update, context)
        #return START

    # elif data in ["parent"]:
    #     #query.edit_message_text("Выберите действие.")
    #     return FIND_CAT_ONE
    elif data in ["subcategory", "near", "main"]:
        query.edit_message_text("Выберите категорию из списка")
        return FIND_CAT_MANY
    else:
           query.edit_message_text(f"Неизвестная команда в find_cat_one {data}.")
           return start(update, context)
           #return START

def find_cat_many(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    data = query.data
    if data in ["choose_1", "choose_2", "choose_3"]:
        query.edit_message_text("Вы выбрали одну из категорий.")
        return FIND_CAT_ONE
    elif data == "main_categories":
        query.edit_message_text("Выберите главные категории.")
        return FIND_CAT_MANY
    elif data in ["subcategory", "near"]:
        query.edit_message_text("Выберите категорию из списка")
        return FIND_CAT_MANY
    elif data in ["cancel"]:
        query.edit_message_text("Отказ")
        return CANCEL
    else:
           query.edit_message_text(f"Неизвестная команда {data}.")
           return START

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return START

def end(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Закончили.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def unknown(update: Update, context: CallbackContext):
    update.message.reply_text("Извините, я не понял эту команду.")

# --- Main Function ---
def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Регистрация обработчиков
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [CallbackQueryHandler(button_handler, pattern="^(find_cat|end)$")],
            FIND_CAT: [MessageHandler(Filters.text & ~Filters.command, handle_cat_input)],
            FIND_CAT_ONE: [CallbackQueryHandler(find_cat_one, pattern="^(choose_|edit_)*")],
            FIND_CAT_MANY: [CallbackQueryHandler(find_cat_many, pattern="^(choose_[1-3]|subcategory|near|main)$")]
            #CANCEL: [CallbackQueryHandler(cancel)]
            # FIND_CAT_CHOOSE: [CallbackQueryHandler(find_cat_one, pattern="choose*")],
            # EDIT_CAT_CHOOSE: [CallbackQueryHandler(find_cat_one, pattern="edit*")]
            },
        fallbacks=[CommandHandler('start', start), MessageHandler(Filters.command, unknown)]
     )

    #dispatcher.add_handler(CommandHandler("start", start))
    #dispatcher.add_handler(CallbackQueryHandler(button_handler))

    dispatcher.add_handler(conv_handler)

    # CallbackQueryHandler для обработки кнопок
    #dispatcher.add_handler(CallbackQueryHandler(handle_cat_input, pattern="^(choose|edit|parent|subcategory|near|choose_[1-3])|main_categories$"))
    #dispatcher.add_handler(CallbackQueryHandler(button_handler, pattern="^(FindCat)$"))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

