class SendMessageException(Exception):
    """Ошибка отпрваки сообщения."""
    pass


class GetAPIAnswerException(Exception):
    """Ошибка получения ответа от API."""
    pass


class CheckResponseException(Exception):
    """Ошибка проверки ответа."""
    pass


class ParseStatusException(Exception):
    """Ошибка парсинга статуса."""
    pass