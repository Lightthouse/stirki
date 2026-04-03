SMSAERO_EMAIL = 'stepanda96@yandex.ru'
SMSAERO_API_KEY = 'Zj_TiT8QK0gWRLkz9fiw_Dd8Fmi5hLgP'

import logging
import asyncio
import smsaero



class SMSSendError(Exception):
    """Ошибка при отправке SMS через SmsAero."""


async def send_sms(phone: int, message: str) -> None:
    """
    Sends an SMS message

    Parameters:
    phone (int): The phone number to which the SMS message will be sent.
    message (str): The content of the SMS message to be sent.
    """
    api = smsaero.SmsAero(SMSAERO_EMAIL, SMSAERO_API_KEY)
    try:
        result = await api.send_sms(phone, message)
        print(result)
    finally:
        await api.close_session()


if __name__ == '__main__':
    asyncio.run(send_sms(79068225814, 'Hello, World!'))