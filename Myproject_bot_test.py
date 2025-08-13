from array import ArrayType
import requests  # Для выполнения HTTP-запросов к API
import logging  # Для настройки системы логирования
import csv  # Для работы с CSV-файлами (чтение/запись)
from datetime import datetime  # Для работы с датой и временем
import pandas as pd  # Для анализа и обработки данных
import matplotlib.pyplot as plt  # Для создания графиков и визуализации данных
from io import BytesIO  # Для работы с бинарными потоками в памяти
import os  # Для взаимодействия с файловой системой
import time #для замера времени
import sqlite3
from dotenv import load_dotenv #config.env
from fontTools.misc.bezierTools import namedtuple
from threading import Thread

# Импорт компонентов Telegram API
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, \
    ConversationHandler

# Логирование
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv("config.env")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
print(TOKEN)

# Состояния для ConversationHandler
FIND_CAT_KWORD, FIND_CAT_ACTIONS,FIND_CAT_DOING = range(3)

# Функция для обработки команды /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Добро пожаловать! Используйте /find_cat для поиска категории.")

# Функция для обработки команды /find_cat
def find_cat(update: Update, context: CallbackContext):
    """Обработчик команды /find_cat."""
    update.message.reply_text("Введите id или ключевое слово для поиска категории:")
    return FIND_CAT_KWORD

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    query = update.callback_query
    query.answer()

    if query.data == "find_cat":
        return process_find_cat_start(update, context)
    elif query.data == "Cancel":
        return cancel(update, context)

def process_find_cat_start(update: Update, context: CallbackContext) -> int:
    #update.callback_query.message.reply_text("Введите ID или ключевое слово для поиска категории:")
    update.callback_query.message.reply_text("Введите имитацию: 1-нашли единственнуюили\2-нашли много\0-не нашли ни одной")
    return FIND_CAT_KWORD

# Функция для обработки ключевого слова для поиска категории
def find_cat_kword(update: Update, context: CallbackContext):
    """Поиск категорий по ключевому слову."""
    update.message.reply_text(F"Пришло в find_cat_kword {update.message.text}")
    keyword = update.message.text

    return FIND_CAT_ACTIONS

def handle_find_cat_kword(update: Update, context: CallbackContext) -> int:

    msg = update.message.text
    context.user_data["keyword"] = msg.strip()
    #пытаемся найти категорию по id или ключевому слову.
    #в результате - варианты: нашли единственную\нашли много\не нашли ни одной
    #если нашли единственную - варианты: подтвердить\выбрать рядом\выбрать подкатегорию\выбрать главные
    #если нашли много - варианты - выбрать из них одну
    #не нашли ни одной

    if msg == "1":
        keyboard = [
            [InlineKeyboardButton("Подтвердить", callback_data="ok"),
             InlineKeyboardButton("Выбрать рядом", callback_data="near"),
             InlineKeyboardButton("Выбрать подкатегорию", callback_data="sub")
             InlineKeyboardButton("Показать главные категории ", callback_data="list")
             ]
        ]
    elif msg == "2":
        keyboard = [
            [InlineKeyboardButton("Выбрать одну из", callback_data="near")
            ]
        ]
    elif msg == "0":
        #update.message.reply_text("Пожалуйста, для поиска категории введите корректный ID или ключевое слово!")
        return STATE_C2

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выберите операцию:", reply_markup=reply_markup)
    return FIND_CAT_ACTIONS

    except FIND_CAT_ACTIONS:
        update.message.reply_text("Пожалуйста, для поиска категории введите корректный ID или ключевое слово!")
        return STATE_C2


# # Функция для обработки действий с категорией
# def my_find_cat_actions(update: Update, context: CallbackContext):
#     query = update.callback_query
#     query.answer()
#     data = query.data
#     query.message.reply_text(F"пришло в find_cat_actions {query.data}")
#
#     if data.startswith("category_"):
#         category_id = int(data.split("_")[1])
#         query.edit_message_text(f"Вы выбрали категорию с ID: {category_id}")
#     elif data.startswith("goto_start"):
#         query.delete_message()
#         start(update, context)
#     elif data.startswith("goto_find_cat"):
#         query.delete_message()
#         find_cat(update, context)
#
#     return ConversationHandler.END

def process_find_cat_keyword(update: Update, context: CallbackContext):
    keyword = update.message.text
    # Логика поиска категории по ключевому слову
    update.message.reply_text(F"пришло в process_find_cat_keyword {keyword}")

    update.message.reply_text(f"Ищем категории, связанные с ключевым словом: {keyword}.")
    return FIND_CAT_ACTIONS  # Переход к следующему состоянию

def handle_find_cat_actions(update: Update, context: CallbackContext):
    keyword = update.message.text
    # Логика поиска категории по ключевому слову
    update.message.reply_text(F"пришло в handle_find_cat_actions {keyword}")

    update.message.reply_text(f"Ищем действие: {keyword}.")

    # Логика обработки действий (например, выбор категории)
    query.edit_message_text(text=f"Вы выбрали действие: {keyword}")
    return FIND_CAT_DOING  # Переход к следующему состоянию

def doing_find_actions (update: Update, context: CallbackContext):
    #keyword = update.message.text
    # Логика поиска категории по ключевому слову
    update.message.reply_text(F"пришло в doing_find_actions {update}")

    update.message.reply_text(f"Выбираем действие: {update}.")
    return ConversationHandler.END


# Функция для обработки команды /end
def end(update: Update, context: CallbackContext):
    """Обработчик команды /end."""
    query = update.callback_query
    query.answer()
    data = query.data
    query.message.reply_text(F"пришло в end {query.data}")

    update.message.reply_text("Диалог завершён. До свидания!")
    return ConversationHandler.END

# Функция для обработки команды /cancel
def cancel(update: Update, context: CallbackContext):
    """Отмена текущего действия."""
    query = update.callback_query
    query.answer()
    data = query.data
    query.message.reply_text(F"пришло в cancel {query.data}")

    update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

# Основная функция для запуска бота
def main():

    # Создание объекта Updater
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Регистрируем обработчики
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATE_S: [CallbackQueryHandler(button_handler, pattern="^(A|B|Cancel)$")],
            STATE_C1: [MessageHandler(Filters.text & ~Filters.command, handle_c1)],
            STATE_C2: [MessageHandler(Filters.text & ~Filters.command, handle_c2)],
            STATE_D1: [MessageHandler(Filters.text & ~Filters.command, handle_d1)],
            STATE_D2: [MessageHandler(Filters.text & ~Filters.command, handle_d2)],
            STATE_R: [CallbackQueryHandler(calculation_handler, pattern="^(add|sub|mul|div)$")],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    dispatcher.add_handler(conv_handler)


    # CallbackQueryHandler для обработки кнопок
    dispatcher.add_handler(CallbackQueryHandler(calculation_handler, pattern="^(add|sub|mul|div)$"))
    dispatcher.add_handler(CallbackQueryHandler(button_handler, pattern="^(A|B)$"))





    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("end", end))

    # Обработчик поиска категории
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('find_cat', find_cat)],
        states={
            FIND_CAT_KWORD: [
                MessageHandler(Filters.text & ~Filters.command, process_find_cat_keyword)
            ],
            FIND_CAT_ACTIONS: [
                CallbackQueryHandler(handle_find_cat_actions)
                ],
            FIND_CAT_DOING: [
                MessageHandler(Filters.text & ~Filters.command, doing_find_actions)
                ]
                },
        fallbacks=[CommandHandler('end', end)])

    dispatcher.add_handler(conv_handler)

    # Запуск бота
    updater.start_polling()
    logger.info("Бот запущен и готов к работе.")
    updater.idle()

# Запуск бота
if __name__ == "__main__":
    main()