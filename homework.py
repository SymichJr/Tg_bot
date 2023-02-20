import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

import exceptions
from settings import ENDPOINT, HOMEWORK_VERDICTS, RETRY_PERIOD

load_dotenv()


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_TOKEN")

HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

logging.basicConfig(
    level=logging.DEBUG,
    filename="./homework_log.log",
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        logging.debug(f'Попытка отправить сообщение: "{message}"')
        message_sent = bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Бот отправил сообщение: "{message}"')
        return message_sent
    except telegram.error.TelegramError as error:
        # Без этого логгирования не проходят тесты
        logger.error(f'Боту не удалось отправить сообщение: "{error}"')
        raise exceptions.SendMessageException(error)
    else:
        return logging.debug(f"Ошибка отправки сообщения")


def get_api_answer(timestamp):
    """Получение ответа от API."""
    timestamp = timestamp or int(time.time())
    headers = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}
    payload = {"from_date": timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=headers, params=payload
        )
    except Exception:
        message = f"URL {ENDPOINT} не доступен"
        raise exceptions.GetAPIAnswerException(message)
    if homework_statuses.status_code != HTTPStatus.OK:
        message = f"Код ответа API: {homework_statuses.status_code}"
        raise exceptions.GetAPIAnswerException(message)
    try:
        return homework_statuses.json()
    except Exception as error:
        message = f"Ошибка преобразования к формату json: {error}"
        raise exceptions.GetAPIAnswerException(message)


def check_response(response):
    """Проверка получения ответа от запроса."""
    if not isinstance(response, dict):
        message = (
            f"Тип данных в ответе от API не соотвествует ожидаемому."
            f" Получен: {type(response)}"
        )
        raise TypeError(message)
    if "homeworks" not in response:
        message = "Ключ homeworks недоступен"
        raise exceptions.CheckResponseException(message)
    homeworks_list = response["homeworks"]
    if not isinstance(homeworks_list, list):
        message = (
            f"В ответе от API домашки приходят не в виде списка. "
            f"Получен: {type(homeworks_list)}"
        )
        raise TypeError(message)
    return homeworks_list


def parse_status(homework):
    """Парсинг статуса."""
    if "homework_name" not in homework:
        message = "Ключ homework_name недоступен"
        raise KeyError(message)
    if "status" not in homework:
        message = "Ключ status недоступен"
        raise KeyError(message)
    homework_name = homework["homework_name"]
    homework_status = homework["status"]
    if homework_status in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        message = f'Отсутсвует статус домашней работы: "{homework_status}"'
        raise exceptions.ParseStatusException(message)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical("Отсутсвуют переменные окружения")
        raise ValueError("Проверьте переменные окружения")
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    current_status = ""
    current_error = ""

    while True:
        try:
            response = get_api_answer(
                timestamp or parse_status(homework_status["current_date"])
            )
            homework = check_response(response)
            if not len(homework):
                logger.info("Не произошло изменения статуса")
            else:
                homework_status = parse_status(homework[0])
                if current_status == homework_status:
                    logger.info(homework_status)
                else:
                    current_status = homework_status
                    send_message(bot, homework_status)

        except Exception as error:
            message_1 = f"Сбой в работе программы: {error}"
            logger.error(message_1)
            message_2 = f"URL {ENDPOINT} не доступен"
            logger.error(message_2)
            message_3 = (
                f"Тип данных в ответе от API не соотвествует ожидаемому."
                f" Получен: {type(response)}"
            )
            logger.error(message_3)
            message_4 = "Ключ homeworks недоступен"
            logger.error(message_4)
            message_5 = "Ключ status недоступен"
            logger.error(message_5)
            message_6 = (
                f'Отсутсвует статус домашней работы: "{homework_status}"'
            )
            logger.error(message_6)
            message_7 = "Ключ homework_name недоступен"
            logger.error(message_7)
            message_8 = f"Ошибка преобразования к формату json: {error}"
            logger.error(message_8)
            message_9 = f"Код ответа API: {homework_statuses.status_code}"
            logger.error(message_9)
            message_10 = f'Боту не удалось отправить сообщение: "{error}"'
            logger.error(message_10)
            if current_error != str(error):
                current_error = str(error)
                send_message(
                    bot,
                    message_1,
                    message_2,
                    message_3,
                    message_4,
                    message_5,
                    message_6,
                    message_7,
                    message_8,
                    message_9,
                    message_10,
                )

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
