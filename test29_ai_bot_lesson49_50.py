# Импорт необходимых библиотек
import os  # Для работы с операционной системой и переменными окружения
import logging  # Для настройки системы логирования
import time  # Для замера времени выполнения операций
import requests  # Для отправки HTTP-запросов к API нейросетей
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton  # Компоненты для работы с Telegram API
from telegram.ext import (
    Updater, CommandHandler, CallbackContext,
    MessageHandler, Filters
)  # Основные компоненты фреймворка для Telegram ботов
from dotenv import load_dotenv  # Для загрузки переменных окружения из .env файла

# Загрузка переменных окружения из файла .env
load_dotenv("config.env")

# Настройка системы логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат записи логов
    level=logging.INFO  # Уровень логирования (INFO и выше)
)
# Создание логгера для текущего модуля
logger = logging.getLogger(__name__)


# Класс для работы с российскими AI-провайдерами
class RussianAI:
    # Конструктор класса
    def __init__(self):
        # Получение провайдера по умолчанию из переменных окружения
        self.provider = os.getenv("DEFAULT_PROVIDER", "yandexgpt")
        # Инициализация истории диалога как пустого списка
        self.conversation_history = []
        # Настройка выбранного провайдера
        self.set_provider(self.provider)

    # Метод для переключения между нейросетевыми провайдерами
    def set_provider(self, provider: str):
        """Переключает между российскими нейросетями"""
        # Приведение названия провайдера к нижнему регистру
        self.provider = provider.lower()
        # Сброс истории диалога при смене провайдера
        self.conversation_history = []

        # Настройка параметров для YandexGPT
        if self.provider == "yandexgpt":
            # Получение API-ключа из переменных окружения
            self.api_key = os.getenv("YANDEX_API_KEY")
            # Получение идентификатора каталога Yandex Cloud
            self.folder_id = os.getenv("YANDEX_FOLDER_ID")
            # Получение модели (по умолчанию "yandexgpt-lite")
            self.model = os.getenv("YANDEX_MODEL", "yandexgpt-lite")
            # URL API YandexGPT
            self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

            # Проверка наличия обязательных ключей
            if not self.api_key or not self.folder_id:
                # Запись ошибки в лог
                logger.error("Не заданы YANDEX_API_KEY и YANDEX_FOLDER_ID")
                return False  # Возврат статуса ошибки

        # Настройка параметров для SberAI (GigaChat)
        elif self.provider == "sberai":
            # Получение API-ключа SberAI
            self.api_key = os.getenv("SBER_API_KEY")
            # Получение модели (по умолчанию "GigaChat:latest")
            self.model = os.getenv("SBER_MODEL", "GigaChat:latest")
            # URL API SberAI
            self.base_url = "https://api.gigachat.dev/v1/chat/completions"

            # Проверка наличия API-ключа
            if not self.api_key:
                logger.error("Не задан SBER_API_KEY")
                return False

        # Обработка неизвестного провайдера
        else:
            logger.error(f"Неизвестный провайдер: {provider}")
            return False

        # Запись информации о выбранном провайдере в лог
        logger.info(f"Используется провайдер: {self.provider.upper()} ({self.model})")
        return True  # Успешное завершение настройки

    # Метод для добавления сообщения в историю диалога
    def add_message(self, role: str, content: str):
        """Добавляет сообщение в историю"""
        # Добавление сообщения в формате {"role": role, "content": content}
        self.conversation_history.append({"role": role, "content": content})

    # Основной метод для генерации ответа на пользовательский ввод
    def generate_response(self, user_input: str):
        """Генерирует ответ через API выбранного провайдера"""
        # Добавление сообщения пользователя в историю
        self.add_message("user", user_input)

        try:
            # Выбор соответствующего метода API в зависимости от провайдера
            if self.provider == "yandexgpt":
                return self._yandex_request()
            elif self.provider == "sberai":
                return self._sber_request()
        # Обработка исключений при работе с API
        except Exception as e:
            return f"🚨 Ошибка API ({self.provider}): {str(e)}"

    # Приватный метод для работы с API YandexGPT
    def _yandex_request(self):
        """Запрос к YandexGPT API"""
        # Формирование заголовков HTTP-запроса
        headers = {
            "Authorization": f"Api-Key {self.api_key}",  # API-ключ для аутентификации
            "Content-Type": "application/json",  # Тип содержимого
            "x-folder-id": self.folder_id  # Идентификатор каталога
        }

        # Преобразование истории диалога в формат, требуемый API YandexGPT
        yandex_messages = []
        for msg in self.conversation_history:
            yandex_messages.append({
                "role": msg["role"],
                "text": msg["content"]  # Yandex использует "text" вместо "content"
            })

        # Формирование тела запроса (payload)
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",  # URI модели
            "completionOptions": {
                "stream": False,  # Режим без потоковой передачи
                "temperature": 0.7,  # Креативность ответов
                "maxTokens": 2000  # Максимальное количество токенов в ответе
            },
            "messages": yandex_messages  # История диалога
        }

        try:
            # Отправка POST-запроса к API YandexGPT
            response = requests.post(
                self.base_url,  # URL API
                headers=headers,  # Заголовки
                json=payload,  # Тело запроса в формате JSON
                timeout=30  # Таймаут запроса (30 секунд)
            )

            # Проверка статуса ответа
            if response.status_code != 200:
                # Логирование ошибки при ненормальном статусе
                logger.error(f"Ошибка {response.status_code}: {response.text}")
                return f"Ошибка API: {response.text}"

            # Парсинг JSON-ответа
            data = response.json()
            # Извлечение текста ответа из структуры данных
            ai_reply = data["result"]["alternatives"][0]["message"]["text"]
            # Добавление ответа ассистента в историю диалога
            self.add_message("assistant", ai_reply)
            return ai_reply  # Возврат сгенерированного ответа

        # Обработка исключений при выполнении запроса
        except Exception as e:
            return f"Ошибка соединения: {str(e)}"

    # Приватный метод для работы с API SberAI (GigaChat)
    def _sber_request(self):
        """Запрос к SberAI (GigaChat) API"""
        # Первый этап: аутентификация для получения токена доступа
        auth_response = requests.post(
            "https://api.gigachat.dev/v1/oauth/token",  # URL для аутентификации
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": self.api_key,  # Использование API-ключа в качестве JWT
                "scope": "GIGACHAT_API_PERS"  # Область доступа
            }
        )

        # Проверка успешности аутентификации
        if auth_response.status_code != 200:
            logger.error(f"Ошибка аутентификации SberAI: {auth_response.text}")
            return "Ошибка аутентификации SberAI"

        # Извлечение данных аутентификации
        auth_data = auth_response.json()
        # Получение токена доступа
        access_token = auth_data["access_token"]

        # Формирование заголовков для основного запроса
        headers = {
            "Authorization": f"Bearer {access_token}",  # Использование токена доступа
            "Content-Type": "application/json"
        }

        # Формирование тела основного запроса
        payload = {
            "model": self.model,  # Идентификатор модели
            "messages": self.conversation_history,  # История диалога
            "temperature": 0.7,  # Креативность ответов
            "max_tokens": 2000  # Максимальное количество токенов в ответе
        }

        # Отправка POST-запроса к API SberAI
        response = requests.post(
            self.base_url,  # URL API
            headers=headers,  # Заголовки
            json=payload,  # Тело запроса
            timeout=30  # Таймаут запроса
        )

        # Проверка статуса ответа
        if response.status_code != 200:
            logger.error(f"Ошибка SberAI: {response.status_code} - {response.text}")
            return f"Ошибка SberAI: {response.text}"

        # Парсинг JSON-ответа
        data = response.json()
        # Извлечение текста ответа
        ai_reply = data["choices"][0]["message"]["content"]
        # Добавление ответа ассистента в историю диалога
        self.add_message("assistant", ai_reply)
        return ai_reply  # Возврат сгенерированного ответа

    # Метод для очистки истории диалога
    def clear_history(self):
        """Очищает историю диалога"""
        # Сброс истории до пустого списка
        self.conversation_history = []
        logger.info("История диалога очищена")  # Логирование события
        return True  # Подтверждение успешного выполнения


# Создание глобального экземпляра AI-ассистента
ai_assistant = RussianAI()


# ====================== ОБРАБОТЧИКИ КОМАНД TELEGRAM ======================

# Обработчик команды /start
def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    # Формирование приветственного сообщения
    help_text = (
        "🤖 Привет! Я российский AI-ассистент. Могу ответить на ваши вопросы с помощью:\n"
        # Динамическое отображение текущей модели или инструкции
        f"• YandexGPT ({ai_assistant.model if ai_assistant.provider == 'yandexgpt' else 'доступен через /yandex'})\n"
        f"• SberAI ({ai_assistant.model if ai_assistant.provider == 'sberai' else 'доступен через /sber'})\n\n"
        "Доступные команды:\n"
        "/yandex - использовать YandexGPT\n"
        "/sber - использовать SberAI (GigaChat)\n"
        "/clear - очистить историю диалога\n\n"
        "Просто отправьте мне сообщение с вашим вопросом!"
    )

    # Создание клавиатуры с кнопками команд
    keyboard = [
        [KeyboardButton("/yandex"), KeyboardButton("/sber")],  # Первая строка
        [KeyboardButton("/clear")]  # Вторая строка
    ]

    # Отправка сообщения с клавиатурой
    update.message.reply_text(
        help_text,  # Текст сообщения
        reply_markup=ReplyKeyboardMarkup(  # Настройка клавиатуры
            keyboard,
            resize_keyboard=True,  # Автоматическое изменение размера
            one_time_keyboard=False  # Постоянное отображение
        )
    )


# Обработчик команды /yandex
def switch_to_yandex(update: Update, context: CallbackContext) -> None:
    """Переключение на YandexGPT"""
    # Попытка переключения провайдера
    if ai_assistant.set_provider("yandexgpt"):
        # Успешное переключение
        update.message.reply_text(
            f"✅ Переключено на YandexGPT ({ai_assistant.model})",
            reply_markup=create_keyboard()  # Обновление клавиатуры
        )
    else:
        # Ошибка переключения
        update.message.reply_text("❌ Не удалось переключиться на YandexGPT")


# Обработчик команды /sber
def switch_to_sber(update: Update, context: CallbackContext) -> None:
    """Переключение на SberAI"""
    # Попытка переключения провайдера
    if ai_assistant.set_provider("sberai"):
        # Успешное переключение
        update.message.reply_text(
            f"✅ Переключено на SberAI ({ai_assistant.model})",
            reply_markup=create_keyboard()  # Обновление клавиатуры
        )
    else:
        # Ошибка переключения
        update.message.reply_text("❌ Не удалось переключиться на SberAI")


# Обработчик команды /clear
def clear_history(update: Update, context: CallbackContext) -> None:
    """Очистка истории диалога"""
    # Попытка очистки истории
    if ai_assistant.clear_history():
        # Успешная очистка
        update.message.reply_text(
            "🗑️ История диалога очищена!",
            reply_markup=create_keyboard()  # Обновление клавиатуры
        )
    else:
        # Ошибка очистки
        update.message.reply_text("❌ Не удалось очистить историю")


# Обработчик текстовых сообщений от пользователя
def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработка пользовательских сообщений"""
    # Получение текста сообщения пользователя
    user_input = update.message.text

    # Игнорируем команды (начинающиеся с /)
    if user_input.startswith('/'):
        return

    # Отправка индикатора "печатает..." в чат
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id,  # ID текущего чата
        action="typing"  # Тип действия (показываем анимацию печати)
    )

    # Замер времени начала генерации ответа
    start_time = time.time()

    try:
        # Генерация ответа с помощью AI-ассистента
        response = ai_assistant.generate_response(user_input)
        # Расчет времени выполнения
        elapsed_time = time.time() - start_time

        # Форматирование ответа для отправки пользователю
        formatted_response = (
            f"🤖 {ai_assistant.provider.upper()} отвечает:\n\n"  # Указание провайдера
            f"{response}\n\n"  # Сгенерированный ответ
            f"⏱ Время генерации: {elapsed_time:.2f} сек"  # Время выполнения
        )

        # Отправка форматированного ответа
        update.message.reply_text(
            formatted_response,
            reply_markup=create_keyboard()  # Отправка с клавиатурой команд
        )

    # Обработка исключений при генерации ответа
    except Exception as e:
        # Логирование ошибки
        logger.error(f"Ошибка генерации ответа: {str(e)}")
        # Отправка сообщения об ошибке пользователю
        update.message.reply_text(
            "🚨 Произошла ошибка при генерации ответа. Попробуйте позже.",
            reply_markup=create_keyboard()
        )


# Функция для создания клавиатуры с командами
def create_keyboard():
    """Создает клавиатуру с командами"""
    # Определение кнопок
    keyboard = [
        [KeyboardButton("/yandex"), KeyboardButton("/sber")],  # Кнопки выбора провайдера
        [KeyboardButton("/clear")]  # Кнопка очистки истории
    ]
    # Возврат настроенной клавиатуры
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,  # Автоматическое изменение размера
        one_time_keyboard=False  # Постоянное отображение
    )


# ====================== ОСНОВНАЯ ФУНКЦИЯ ======================
def main():
    # Проверка наличия хотя бы одного API-ключа
    if not os.getenv("YANDEX_API_KEY") and not os.getenv("SBER_API_KEY"):
        # Логирование ошибки
        logger.error("Не найдены API-ключи! Проверьте .env файл")
        # Вывод сообщения об ошибке в консоль
        print("❌ ОШИБКА: Не найден ни один API ключ в .env файле!")
        print("Добавьте ключи для Yandex или SberAI")
        print("Пример .env файла:")
        print("YANDEX_API_KEY=ваш_ключ_яндекс")
        print("YANDEX_FOLDER_ID=ваш_folder_id")
        print("SBER_API_KEY=ваш_ключ_сбер")
        return  # Завершение работы при отсутствии ключей

    # Получение токена Telegram бота
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    # Проверка наличия токена
    if not TOKEN:
        logger.error("Не задан TELEGRAM_BOT_TOKEN в .env файле!")
        print("❌ ОШИБКА: Не задан TELEGRAM_BOT_TOKEN в .env файле!")
        return  # Завершение работы при отсутствии токена

    # Создание объекта Updater для работы с Telegram API
    updater = Updater(TOKEN)
    # Получение диспетчера для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Регистрация обработчиков команд:
    dispatcher.add_handler(CommandHandler("start", start))  # Обработчик /start
    dispatcher.add_handler(CommandHandler("yandex", switch_to_yandex))  # Обработчик /yandex
    dispatcher.add_handler(CommandHandler("sber", switch_to_sber))  # Обработчик /sber
    dispatcher.add_handler(CommandHandler("clear", clear_history))  # Обработчик /clear

    # Регистрация обработчика текстовых сообщений:
    # Фильтр: текстовые сообщения, не являющиеся командами
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запуск бота в режиме опроса сервера Telegram
    updater.start_polling()
    # Логирование успешного запуска
    logger.info("🤖 Российский AI-ассистент запущен и готов к работе!")
    # Вывод сообщения в консоль
    print("Бот успешно запущен. Используйте /start в Telegram для начала работы.")

    # Бесконечный цикл обработки событий
    updater.idle()


# Точка входа в программу
if __name__ == '__main__':
    main()  # Вызов основной функции