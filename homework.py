from http import HTTPStatus
import sys
from dotenv import load_dotenv
import requests
import os
import time
import logging
from logging.handlers import RotatingFileHandler
import telegram.ext
from exceptions import SendMessageError, RequestsError, StatusCodeError


load_dotenv()


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('my_logger.log', maxBytes=50000000,
                              backupCount=5, encoding="UTF-8")
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
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
    """отправляет сообщение в Telegram чат."""
    logger.info(
        'Отправляем сообщение в чат {TELEGRAM_CHAT_ID}'
    )
    try:
        bot.send_message(
            chad_id=TELEGRAM_CHAT_ID, text=message
        )
    except Exception as message_error:
        raise SendMessageError(f'Сообщение не отправлено {message_error}')
    else:
        logger.info(
            f'Сообщение {message} отправлено в чат {TELEGRAM_CHAT_ID}'
        )


def get_api_answer(current_timestamp):
    """делает запрос к единственному эндпоинту API-сервиса."""
    logger.info('Получаем ответ от Эндопоинта API-сервиса')
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    params_requests = {
        'url': ENDPOINT,
        'params': params,
        'headers': HEADERS
    }
    try:
        response = requests.get(**params_requests)
    except Exception as error:
        raise RequestsError(
            f'Ошибка при запросе к эндпоинту API:{error}'
        )
    else:
        logger.info(
            'Получили успешно запрос преоброзовав его в .json'
        )
    if response.status_code != HTTPStatus.OK:
        raise StatusCodeError(
            'Ошибка статуса response, ожидали статус будет равен 200'
        )
    return response.json()


def check_response(response):
    """проверяет ответ API на корректность."""
    logger.info('Проверка response.json на корректность')
    if not isinstance(response, dict):
        raise TypeError(
            'в response пришел неверный тип данных'
            'ожидали что в response будет словарь'
        )
    if 'homeworks' not in response:
        raise KeyError(
            'В response отсуствует ключ homeworks'
            'ожидали, что в response будет ключ homeworks'
        )
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            'response[homeworks] не является списком'
            'ожидалось, что response[homeworks] = list'
        )
    logger.info('Проверка на корректность пройдена')
    return response['homeworks']


def parse_status(homework):
    """
    извлекает из информации о конкретной.
    домашней работе статус этой работы.
    """
    logger.info(
        'Проверям содержимое словаря response.json'
    )
    if 'homework_name' not in homework:
        raise KeyError(
            'Отсуствует ключ homework_name в homework'
        )
    if 'status' not in homework:
        raise KeyError('Отсуствует ключ status')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError('Ошибка сервера, неверный статус')
    verdict = HOMEWORK_STATUSES[homework_status]
    logger.info(
        'Проверили на присуствие homework_name,'
        'status. status имеет значение HOMEWORK_STATUSES'
    )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка токенов."""
    logger.info('Проверяем наличие важных токенов')
    if (not TELEGRAM_CHAT_ID or not TELEGRAM_TOKEN
            or not PRACTICUM_TOKEN):
        return False
    logger.info('Токены есть')
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.CRITICAL(
            'отсуствую переменые окружения PRACTICUM_TOKEN,'
            'TELEGRAM_TOKEN, TELEGRAM_CHAT_ID')
        message = 'Выход из программы'
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            current_timestamp = response.get('curretn_date')
            message = parse_status(homework)
            if message != status:
                send_message(bot, message)
                status = message
        except SendMessageError as error:
            logger.error(f'Сообщение не отправленно:{error}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
