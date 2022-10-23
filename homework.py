from dotenv import load_dotenv
import logging
import requests
import os
import time
import logging
from logging.handlers import RotatingFileHandler
import telegram.ext


load_dotenv()


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN' )
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """ отправляет сообщение в Telegram чат"""
    return bot.send_message(chad_id=TELEGRAM_CHAT_ID,text = message)

def get_api_answer(current_timestamp):
    """ делает запрос к единственному эндпоинту API-сервиса"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, params=params, headers=HEADERS)
    except Exception as error:
        logger.error(f'Ошибка при запросе к эндпоинту API:{error}')
    if response.status_code != 200:
        raise Exception('Ошибка статуса')
    return response.json()

def check_response(response):
    """ проверяет ответ API на корректность"""
    if type(response) is not dict:
        raise TypeError('не корректный тип')
    if response['homeworks'] is None:
        raise KeyError('Отсуствует ключ homeworks в API')
    if not isinstance(response['homeworks'], list):
        raise Exception(
            'не является списком'
        )
    return response['homeworks']

def parse_status(homework):
    """извлекает из информации о конкретной
    домашней работе статус этой работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError('Ошибка сервера, неверный статус')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'

def check_tokens():
    """Проверка токенов"""
    if (TELEGRAM_CHAT_ID is None or TELEGRAM_TOKEN is None
    or PRACTICUM_TOKEN is None):
        return False
    return True

def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if not check_tokens:
        logger.CRITICAL('отсуствую переменые окружения')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            message = parse_status(homeworks[0])
            current_timestamp = response.get('curretn_date')
            if message != status:
                send_message(bot, message)
                status = message
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            time.sleep(RETRY_TIME)

if __name__ == '__main__':
    main()
