from pytz import timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater,CommandHandler, CallbackQueryHandler, CallbackContext
import requests as rq  #Для выполнения HTTP-запросов к внешним API
import logging #Для настройки системы логирования

#Настройка системы логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',#Формат записи логов
    level=logging.INFO #Уровень логирования
)
logger = logging.getLogger(__name__)#Создание объекта логгера для теккущего модуля
#Константы
TOKEN = "7567816356:AAFaUrQ0zD0VzQmW44C2_I8PGy7XRX7xBXE"
# OPENWEATHER_API_KEY: str = "d468b09e4ed93a30bb7c724708b1e800"
# CBR_API_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
#Определение состояний для бота (Conversation Handler)
WAIT_CITY, SHOW_INFO = range(2)  #Состояние диалога: ожидание города и показ информаци

#city="Moscow"
api_key = "d468b09e4ed93a30bb7c724708b1e800"
city = input("введите город ")
url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
response = rq.get(url)
print(response.status_code)

if response.status_code==200:
    data = response.json()
    print(data)
    print(f"Погода в городе {city}")
    print(f"Температура {round(data['main']['temp'],1)} K")
    print(f"Погода {data['weather'][0]['description']}")
    print(f"Влажность {data['main']['humidity']}%")
elif response.status_code==404:
    print(f"Город {city} не найден!")
