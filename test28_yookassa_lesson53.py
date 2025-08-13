# Импорт обработчика предварительных платежных запросов Telegram
from telegram.ext import PreCheckoutQueryHandler

# Импорт стандартных библиотек
import os  # Работа с операционной системой и переменными окружения
import logging  # Логирование событий
import time  # Измерение времени выполнения
import requests  # HTTP-запросы к API
import datetime  # Работа с датой и временем

# Импорт компонентов Telegram API
from telegram import (
    Update,  # Объект обновления от Telegram
    ReplyKeyboardMarkup,  # Клавиатура с кнопками
    KeyboardButton,  # Кнопка клавиатуры
    LabeledPrice,  # Цена для платежей
    InlineKeyboardMarkup,  # Инлайн-клавиатура
    InlineKeyboardButton  # Кнопка инлайн-клавиатуры
)
from telegram.ext import (
    Updater,  # Ядро для работы с Telegram API
    CommandHandler,  # Обработчик команд (начинающихся с /)
    CallbackContext,  # Контекст выполнения
    MessageHandler,  # Обработчик текстовых сообщений
    Filters  # Фильтры для обработчиков
)

# Импорт для работы с .env файлами
from dotenv import load_dotenv

# Импорт SDK ЮKassa
from yookassa import Configuration, Payment  # Конфигурация и платежи ЮKassa

# Загрузка переменных окружения из .env файла
load_dotenv("config.env")

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат сообщений
    level=logging.INFO  # Уровень логирования
)
logger = logging.getLogger(__name__)  # Создание логгера для текущего модуля

# Глобальный словарь для хранения подписок (в реальном проекте используйте БД)
subscriptions = {}


class RussianAI:
    """Класс для работы с российскими AI-провайдерами (YandexGPT, SberAI)"""

    def __init__(self):
        """Инициализация AI-ассистента с провайдером по умолчанию"""
        self.provider = os.getenv("DEFAULT_PROVIDER", "yandexgpt")  # Провайдер по умолчанию
        self.conversation_history = []  # История диалога
        self.set_provider(self.provider)  # Настройка провайдера

    def set_provider(self, provider: str) -> bool:
        """Настройка провайдера AI (YandexGPT или SberAI)"""
        self.provider = provider.lower()  # Приведение к нижнему регистру
        self.conversation_history = []  # Сброс истории при смене провайдера

        # Настройка для YandexGPT
        if self.provider == "yandexgpt":
            self.api_key = os.getenv("YANDEX_API_KEY")  # API-ключ
            self.folder_id = os.getenv("YANDEX_FOLDER_ID")  # Идентификатор каталога
            self.model = os.getenv("YANDEX_MODEL", "yandexgpt-lite")  # Модель (по умолчанию lite)
            self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"  # URL API

            # Проверка обязательных переменных
            if not self.api_key or not self.folder_id:
                logger.error("Не заданы YANDEX_API_KEY или YANDEX_FOLDER_ID")
                return False

        # Настройка для SberAI
        elif self.provider == "sberai":
            self.api_key = os.getenv("SBER_API_KEY")  # API-ключ
            self.model = os.getenv("SBER_MODEL", "GigaChat:latest")  # Модель (по умолчанию последняя)
            self.base_url = "https://api.gigachat.dev/v1/chat/completions"  # URL API

            # Проверка обязательной переменной
            if not self.api_key:
                logger.error("Не задан SBER_API_KEY")
                return False
        else:
            logger.error(f"Неизвестный провайдер: {provider}")
            return False

        logger.info(f"Используется провайдер: {self.provider.upper()}({self.model})")
        return True

    def add_message(self, role: str, content: str) -> None:
        """Добавление сообщения в историю диалога"""
        self.conversation_history.append({"role": role, "content": content})

    def generate_response(self, user_input: str, user_id: int) -> str:
        """
        Генерация ответа AI с проверкой подписки
        :param user_input: Входное сообщение пользователя
        :param user_id: ID пользователя для проверки подписки
        :return: Ответ AI или сообщение о необходимости подписки
        """
        # Проверка наличия активной подписки
        if not self.check_subscription(user_id):
            return ("❌ Доступ ограничен. Для использования бота необходимо оформить подписку.\n\n"
                    "/buy - купить подписку (200 руб/мес)")

        # Добавление пользовательского сообщения в историю
        self.add_message("user", user_input)

        try:
            # Выбор соответствующего API
            if self.provider == "yandexgpt":
                return self._yandex_request()
            elif self.provider == "sberai":
                return self._sber_request()
        except Exception as e:
            return f"Ошибка API ({self.provider}): {str(e)}"

    def _yandex_request(self) -> str:
        """Запрос к YandexGPT API"""
        # Формирование заголовков запроса
        headers = {
            "Authorization": f"Api-Key {self.api_key}",  # Аутентификация
            "Content-Type": "application/json",  # Тип содержимого
            "x-folder-id": self.folder_id  # Идентификатор каталога
        }

        # Преобразование истории сообщений в формат Yandex API
        yandex_messages = []
        for msg in self.conversation_history:
            yandex_messages.append({
                "role": msg['role'],
                "text": msg['content']
            })

        # Формирование тела запроса
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{self.model}",  # URI модели
            "completionOptions": {
                "stream": False,  # Отключение потоковой передачи
                "temperature": 0.7,  # Креативность ответов
                "maxTokens": 2000  # Максимальное количество токенов
            },
            "messages": yandex_messages  # История сообщений
        }

        try:
            # Отправка POST-запроса
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30  # Таймаут 30 секунд
            )

            # Обработка HTTP ошибок
            if response.status_code != 200:
                logger.error(f"Ошибка {response.status_code}: {response.text}")
                return f"Ошибка API: {response.text}"

            # Извлечение данных ответа
            data = response.json()
            ai_reply = data['result']['alternatives'][0]['message']['text']  # Текст ответа
            self.add_message("assistant", ai_reply)  # Сохранение ответа в историю
            return ai_reply

        except Exception as e:
            return f"Ошибка соединения: {str(e)}"

    def _sber_request(self) -> str:
        """Запрос к SberAI (GigaChat) API"""
        # Первый этап: получение токена доступа
        auth_response = requests.post(
            "https://api.gigachat.dev/v1/oauth/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": self.api_key,
                "scope": "GIGACHAT_API_PERS"
            }
        )

        # Обработка ошибок аутентификации
        if auth_response.status_code != 200:
            logger.error(f"Ошибка аутентификации SberAI: {auth_response.text}")
            return "Ошибка аутентификации SberAI"

        # Извлечение токена доступа
        auth_data = auth_response.json()
        access_token = auth_data['access_token']

        # Формирование заголовков для основного запроса
        headers = {
            "Authorization": f"Bearer {access_token}",  # Токен доступа
            "Content-Type": "application/json"
        }

        # Формирование тела запроса
        payload = {
            "model": self.model,  # Идентификатор модели
            "messages": self.conversation_history,  # История диалога
            "temperature": 0.7,  # Креативность ответов
            "max_tokens": 2000  # Максимальное количество токенов
        }

        # Отправка запроса к API
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=30  # Таймаут 30 секунд
        )

        # Обработка ошибок API
        if response.status_code != 200:
            logger.error(f"Ошибка SberAI: {response.status_code} - {response.text}")
            return f"Ошибка SberAI: {response.text}"

        # Извлечение и сохранение ответа
        data = response.json()
        ai_reply = data['choices'][0]['message']['content']  # Текст ответа
        self.add_message("assistant", ai_reply)  # Сохранение в историю
        return ai_reply

    def clear_history(self) -> bool:
        """Очистка истории диалога"""
        self.conversation_history = []
        logger.info("История диалога очищена")
        return True

    def check_subscription(self, user_id: int) -> bool:
        """
        Проверка активной подписки пользователя
        :param user_id: ID пользователя Telegram
        :return: True если подписка активна, False если нет
        """
        # Получение данных о подписке
        sub = subscriptions.get(user_id)
        # Проверка наличия и срока действия подписки
        if sub and sub['end_date'] > datetime.datetime.now():
            return True
        return False


# Инициализация глобального экземпляра AI ассистента
ai_assistant = RussianAI()

def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    # Формирование приветственного сообщения
    help_text = (
        "Привет! Я российский AI-ассистент. Могу ответить на ваши вопросы с помощью:\n"
        f"YandexGPT ({ai_assistant.model if ai_assistant.provider == 'yandexgpt' else 'доступен через /yandex'})\n"
        f"SberAI ({ai_assistant.model if ai_assistant.provider == 'sberai' else 'доступен через /sber'})\n\n"
        "Доступные команды:\n"
        "/yandex - использовать YandexGPT\n"
        "/sber - использовать SberAI\n"
        "/clear - очистить историю диалога\n"
        "/buy - купить подписку (200 руб/мес)\n\n"
        "Просто отправьте мне сообщение с вашим вопросом"
    )

    # Создание клавиатуры
    keyboard = [
        [KeyboardButton("/yandex"), KeyboardButton("/sber")],
        [KeyboardButton("/clear"), KeyboardButton("/buy")]
    ]

    # Отправка сообщения с клавиатурой
    update.message.reply_text(
        help_text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,  # Автоматическое изменение размера
            one_time_keyboard=False  # Постоянное отображение
        )
    )


def switch_to_yandex(update: Update, context: CallbackContext) -> None:
    """Переключение на YandexGPT"""
    if ai_assistant.set_provider("yandexgpt"):
        update.message.reply_text(
            f"✅ Переключено на YandexGPT ({ai_assistant.model})",
            reply_markup=create_keyboard()
        )
    else:
        update.message.reply_text("❌ Не удалось переключиться на YandexGPT")


def switch_to_sber(update: Update, context: CallbackContext) -> None:
    """Переключение на SberAI"""
    if ai_assistant.set_provider("sberai"):
        update.message.reply_text(
            f"✅ Переключено на SberAI ({ai_assistant.model})",
            reply_markup=create_keyboard()
        )
    else:
        update.message.reply_text("❌ Не удалось переключиться на SberAI")


def clear_history(update: Update, context: CallbackContext) -> None:
    """Очистка истории диалога"""
    if ai_assistant.clear_history():
        update.message.reply_text(
            "🗑️ История диалога очищена",
            reply_markup=create_keyboard()
        )
    else:
        update.message.reply_text("❌ Не удалось очистить историю")


def buy_subscription(update: Update, context: CallbackContext) -> None:
    """Покупка подписки через ЮKassa"""
    try:
        user_id = update.message.from_user.id

        # Проверка активной подписки
        if ai_assistant.check_subscription(user_id):
            update.message.reply_text("✅ У вас уже есть активная подписка!")
            return

        # Параметры платежа
        price = int(os.getenv("SUBSCRIPTION_PRICE", 20000))  # Сумма в копейках (200 руб)
        provider_token = os.getenv("TELEGRAM_PROVIDER_TOKEN")  # Токен платежного провайдера

        logger.info(f"Creating payment for user {user_id}, price: {price}, provider: {provider_token}")

        # Отправка счета пользователю
        context.bot.send_invoice(
            chat_id=update.effective_chat.id,  # ID чата
            title="Премиум подписка на AI-ассистент",  # Название товара
            description="Доступ ко всем функциям бота на 30 дней",  # Описание
            payload=f"subscription_{user_id}",  # Уникальный идентификатор платежа
            provider_token=provider_token,  # Токен платежной системы
            currency="RUB",  # Валюта
            prices=[LabeledPrice("Подписка", price)],  # Цены
            start_parameter="subscription"  # Параметр запуска
        )
    except Exception as e:
        logger.exception("Ошибка в buy_subscription")
        update.message.reply_text("❌ Ошибка при создании платежа. Попробуйте позже.")


def successful_payment(update: Update, context: CallbackContext) -> None:
    """Обработка успешного платежа"""
    try:
        user_id = update.message.from_user.id
        payment_info = update.message.successful_payment  # Данные платежа

        logger.info(f"Успешный платеж получен: {payment_info}")

        # Расчет даты окончания подписки
        end_date = datetime.datetime.now() + datetime.timedelta(
            days=int(os.getenv("SUBSCRIPTION_DAYS", 30)))

        # Сохранение данных о подписке
        subscriptions[user_id] = {
            'start_date': datetime.datetime.now(),  # Дата начала
            'end_date': end_date,  # Дата окончания
            'status': 'active'  # Статус
        }

        # Уведомление пользователя
        update.message.reply_text(
            f"🎉 Подписка успешно активирована до {end_date.strftime('%d.%m.%Y')}!\n\n"
            "Теперь вы можете использовать все возможности бота!"
        )
    except Exception as e:
        logger.exception("Ошибка в successful_payment")
        update.message.reply_text(
            "❌ Ошибка активации подписки. Пожалуйста, свяжитесь с поддержкой."
        )


def precheckout_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик предварительного платежного запроса"""
    query = update.pre_checkout_query
    try:
        # Всегда подтверждаем запрос (в реальном проекте нужна проверка)
        context.bot.answer_pre_checkout_query(
            pre_checkout_query_id=query.id,
            ok=True
        )
        logger.info(f"PreCheckout подтвержден для платежа: {query.invoice_payload}")
    except Exception as e:
        logger.error(f"Ошибка в precheckout_handler: {str(e)}")
        context.bot.answer_pre_checkout_query(
            pre_checkout_query_id=query.id,
            ok=False,
            error_message="Произошла ошибка при обработке платежа"
        )


def handle_message(update: Update, context: CallbackContext) -> None:
    """Обработка текстовых сообщений с проверкой подписки"""
    user_input = update.message.text

    # Пропуск команд (начинающихся с /)
    if user_input.startswith('/'):
        return

    user_id = update.message.from_user.id

    # Показ индикатора "печатает"
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    start_time = time.time()  # Замер времени начала обработки

    try:
        # Генерация ответа с проверкой подписки
        response = ai_assistant.generate_response(user_input, user_id)
        elapsed_time = time.time() - start_time  # Расчет времени выполнения

        # Форматирование ответа с информацией о времени
        formatted_response = (
            f"{ai_assistant.provider.upper()} отвечает:\n\n"
            f"{response}\n\n"
            f"⏱ Время генерации: {elapsed_time:.2f} сек"
        )

        # Отправка ответа
        update.message.reply_text(
            formatted_response,
            reply_markup=create_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка генерации ответа: {str(e)}")
        update.message.reply_text(
            "Произошла ошибка при генерации ответа. Попробуйте позже.",
            reply_markup=create_keyboard()
        )


def create_keyboard():
    """Создание клавиатуры с командами"""
    keyboard = [
        [KeyboardButton("/yandex"), KeyboardButton("/sber")],
        [KeyboardButton("/clear"), KeyboardButton("/buy")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,  # Адаптивный размер
        one_time_keyboard=False  # Постоянное отображение
    )


def error_handler(update: Update, context: CallbackContext) -> None:
    """Глобальный обработчик ошибок"""
    logger.error(msg="Глобальная ошибка:", exc_info=context.error)

    if update and update.message:
        update.message.reply_text(
            "⚠️ Произошла системная ошибка. Разработчики уже уведомлены. Попробуйте позже."
        )


def main():
    """Основная функция запуска бота"""
    try:
        # Проверка токена бота
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.error("CRITICAL: TELEGRAM_BOT_TOKEN not set!")
            return

        # Инициализация бота
        updater = Updater(bot_token)
        dispatcher = updater.dispatcher

        # Регистрация обработчиков команд
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("yandex", switch_to_yandex))
        dispatcher.add_handler(CommandHandler("sber", switch_to_sber))
        dispatcher.add_handler(CommandHandler("clear", clear_history))
        dispatcher.add_handler(CommandHandler("buy", buy_subscription))

        # Регистрация обработчиков сообщений и платежей
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        dispatcher.add_handler(PreCheckoutQueryHandler(precheckout_handler))  # ОБЯЗАТЕЛЬНО для платежей
        dispatcher.add_handler(MessageHandler(Filters.successful_payment, successful_payment))

        # Регистрация обработчика ошибок
        dispatcher.add_error_handler(error_handler)

        # Запуск бота
        updater.start_polling()  # Запуск опроса сервера Telegram
        logger.info("🤖 Бот запущен")
        print("Бот успешно запущен!")
        updater.idle()  # Бесконечный цикл до остановки
    except Exception as e:
        logger.exception("CRITICAL ERROR IN MAIN")
        print(f"❌ Критическая ошибка: {str(e)}")


if __name__ == '__main__':
    main()