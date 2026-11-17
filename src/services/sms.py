import logging

import smsaero

from src.services.auth import phone_digits

logger = logging.getLogger(__name__)

# Текст до 70 символов — одна SMS (кириллица). Источник (название и сайт) обязателен при бесплатной
# подписи SmsAero, иначе операторы могут блокировать. Латиница и кириллица — в разных словах:
# смешение в одном слове SmsAero отклоняет.
CODE_TEXT = "Код для входа в Стирка ON: {code}. stirkaon.com"


class SMSSendError(Exception):
    """Ошибка при отправке SMS через SmsAero."""


class SMSService:
    def __init__(self, email: str, api_key: str, sign: str = ""):
        self._email = email
        self._api_key = api_key
        # Пусто — библиотечная подпись «Sms Aero» (по документации SmsAero — только для тестов).
        self._sign = sign or None

    async def send_sms(self, phone: str, text: str) -> None:
        api = smsaero.SmsAero(self._email, self._api_key)
        try:
            result = await api.send_sms(int(phone_digits(phone)), text, sign=self._sign)
        except smsaero.SmsAeroException as e:
            raise SMSSendError(str(e)) from e
        finally:
            await api.close_session()
        # Библиотека возвращает data из ответа: для одного номера — словарь сообщения.
        msg = result[0] if isinstance(result, list) and result else result
        if not isinstance(msg, dict) or "id" not in msg:
            raise SMSSendError(f"Неожиданный ответ SmsAero: {result}")
        # id — для поиска в кабинете и sms/status; статус 8 — сообщение ушло на модерацию.
        logger.info(
            "SMS отправлено: id=%s, статус=%s (%s), подпись=%s, стоимость=%s",
            msg.get("id"), msg.get("status"), msg.get("extendStatus"), msg.get("from"), msg.get("cost"),
        )

    async def send_verification_code(self, phone: str, code: str) -> None:
        await self.send_sms(phone, CODE_TEXT.format(code=code))
