import requests #Для выполнения HTTP-запросов к внешним API
import logging #Для настройки системы логирования
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup,KeyboardButton,ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext,MessageHandler,Filters,ConversationHandler
import os #для работы с ОС и окружением
import time #для замера времени
from dotenv import load_dotenv #config.env

load_dotenv()

#Настройка системы логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',#Формат записи логов
    level=logging.INFO #Уровень логирования
)
logger = logging.getLogger(__name__)

class RussianAI():
    def __init__(self):
        self.provider = os.getenv(DEFAULT_PROVIDER,"yandexgpt")
        self.conversation_history = []
        self.set_provider = self.provider

    def set_provider(self, provider:str):
        self.provider = self.provider.lower()
        if self.provider == "yandexgpt": #получение api-ключа из env
            self.api_key = os.getenv("YANDEX_API_KEY")
            self.api_folder = os.getenv("YANDEX_FOLDER_ID")
            self.api_model = os.getenv("YANDEX_MODEL")
            self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/vqcompletion"
            if not self.api_key or not self.api_folder:
                logger.error("Не заданы YANDEX_API_KEY или YANDEX_FOLDER_ID")
                return False

    def add_message(self, role:str, content:str):
        self.conversation_history.append({'role':role,'content':content})           # - для добавления сообщений в чат

    def generate_response(self, user_input:str):
        #для генерации ответа на пользовательский ввод
        self.add_message({'role':'user', 'content':user_input})

        try:
            if self.provider == "yandexgpt":
                self._yandex_request()
        except Exception as e:
            return f"Ощибка API ({self.provider}) {str(e)}"

    def _yandex_request(self):
        #формирование заголовка http запроса для работы с YandexGPT
        headers = {
            "Authorization": f"Api-key {self.api_key}",
            "Content-type": "application/json",
            "x-folder-id":  self.folder_id
        }
        yandex_msg = []
        for msg in self.conversation_history:
            yandex_msg.append({'role':msg.role,'text':msg.content})

        #тело запроса
        payload = {
            "modeur1":f"gpt{self.folder_id}/{self.model}",
            "completionOptions":{
                "steam":False, #режим потока передачи
                "temperature":0.7,  #Креативность ответов
                "maxToken":2000
            }, "messages": yandex_msg # история диалога}
        }
        try:
            response = requests.post(
                self.base_url,               #URL_API
                headers = headers,           #Заголовки
                json = payload,              #Тело запроса в формате json
                timeout = 30                 #Таймаут 30 сек.
            )
            if response.status_code != 200:
                logger.error(f"Ошибка{response.status_code} {response.text}")
                return f"Ошибка Api: {response.text}"

            data = response.json()
            ai_reply = data['result']['alternatives'][0]['message']['text']
            self.add_message('assistant',ai_reply)
            return ai_reply

        except Exception as e:
            return f"Ошибка {str(e)}"

# - `_request_sber()` - для работы с SberAI

    def clear_history(self):
        self.conversation_history.clear()


