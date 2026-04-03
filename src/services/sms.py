import logging

import smsaero

logger = logging.getLogger(__name__)


class SMSSendError(Exception):
    """Ошибка при отправке SMS через SmsAero."""


class SMSService:
    def __init__(self, email: str, api_key: str, sign: str, test_mode: bool = False):
        # sign пока что не используем
        self._email = email
        self._api_key = api_key
        self._sign = sign
        self._test_mode = test_mode

    def _normalize_phone(self, phone: str) -> int:
        """Приводит номер к формату smsaero: int без + и пробелов (7XXXXXXXXXX)."""
        cleaned = phone.strip().replace("+", "").replace(" ", "").replace("-", "")
        if cleaned.startswith("8"):
            cleaned = "7" + cleaned[1:]
        print(int(cleaned))
        return int(cleaned)

    async def send_sms(self, phone: str, text: str) -> None:
        api = smsaero.SmsAero(self._email, self._api_key)
        if self._test_mode:
            api.enable_test_mode()
        try:
            result = await api.send_sms(self._normalize_phone(phone), text)
            if not result.get("success"):
                raise SMSSendError(f"SmsAero вернул ошибку: {result}")
        except smsaero.SmsAeroException as e:
            raise SMSSendError(str(e)) from e
        finally:
            await api.close_session()

    async def send_verification_code(self, phone: str, code: str) -> None:
        await self.send_sms(phone, f"Ваш код подтверждения StirkiOn: {code}")
