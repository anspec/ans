# Создай разного вида кнопки для своего Telegram бота.
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
# 4. Тестирование
# - Запусти бота и проверь:
#     - При команде `/start` отображается приветственное сообщение и обе клавиатуры.
#     - При нажатии на «Показать погоду» выводит сообщение: «Функция в разработке» с кнопкой «Назад».
#     - При нажатии на «Информацию» отправляет текст: «Это учебный бот».
#     - Кнопка «Отправить контакт» запрашивает доступ к номеру телефона.
#     - Кнопка «Перейти на сайт» открывает сайт в браузере.

from pytz import timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater,CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters, ConversationHandler

from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

# Импорт pytz для работы с таймзонами


def create_main_menu_keyboard():
  keyboard = [
      [InlineKeyboardButton("🛍 Показать погоду", callback_data='weather'),
       InlineKeyboardButton("👤 Информация", callback_data='info')],
  ]
  return InlineKeyboardMarkup(keyboard)

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


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_text(
          f"👋 Привет, {user.first_name}! Потести в тг мои кнопки!",
          reply_markup=create_main_menu_keyboard()
  )


def handle_contact(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Спасибо за отправку контакта!")


def handle_text(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Вы отправили текст!")


def main():
#    token = "7661416982:AAHuQxJsWj4RNzjV6nyh_PGQBH3yTaWNsRA"
    TOKEN = "7567816356:AAFaUrQ0zD0VzQmW44C2_I8PGy7XRX7xBXE"
    OPENWEATHER_API_KEY: str = "d468b09e4ed93a30bb7c724708b1e800"
    CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
    # Определение состояний для бота (Conversation Handler)
    WAIT_CITY, SHOW_INFO = range(2)  # Состояние диалога: ожидание города и показ информаци


    # Создаем объект планировщика с использованием pytz для таймзоны
#scheduler = AsyncIOScheduler()
# Создаем планировщик
    scheduler = AsyncIOScheduler()
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher

    # Настройка ConversationHandler для управлением диалогом погоды
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_click, pattern='^weather$')],
        states={
            WAIT_CITY:[MessageHandler(Filters.text & ~Filters.command, get_weather)], #Ожидание города
            SHOW_INFO:[CallbackQueryHandler(button_click)] #Состояние показа информации
        },
        fallbacks=[CommandHandler('cancel',cancel)], #Резеврный обработчик отмены
        allow_reentry=True #Разрешение на повторный диалог
    )
    dispatcher.add_handler(conv_handler)#Диалог погоды
    dispatcher.add_handler(CommandHandler("start",start))#через /start
    dispatcher.add_handler(CallbackQueryHandler(button_click, pattern='^(currency|back_to_menu|close)$'))#через кнопку
    updater.start_polling()
    logger.info("Бот запущен и готов к работе")
    updater.idle()


#application = scheduler.token(token).post_init(lambda app: app.job_queue.set_scheduler(scheduler)).build()

# application = async.token(token).post_init(lambda app: app.job_queue.set_scheduler(scheduler)).build()

#   application.add_handler(CommandHandler('start', start))
#   application.add_handler(CallbackQueryHandler(button_click))
#   application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
#   application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
#
# #  scheduler.start()  # Не забываем запустить планировщик
#   application.run_polling()


if __name__ == '__main__':  # Исправлено условие для запуска
  main()

