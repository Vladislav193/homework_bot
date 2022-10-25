
class SendMessageError(Exception):
    """Сообщение не отправленно."""
    pass


class RequestsError(Exception):
    """Ошибка при запросе к эндпоинту API."""
    pass