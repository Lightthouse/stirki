import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_client, get_db
from src.models.client import Client
from src.repositories.client import ClientRepository, TooManyVerifyAttemptsError
from src.schemas.auth import RequestCodeIn, VerifyCodeIn, AuthTokenOut, ClientOut, UpdateClientIn
from src.services.auth import generate_verification_code
from src.services.baserow import BaserowService
from src.services.sms import SMSSendError, SMSService
from src.settings import AppSettings, SmsAeroSettings

logger = logging.getLogger(__name__)

router = APIRouter()

# Минимальный интервал между запросами кода на один номер (антифлуд / анти-SMS-бомбинг).
# Намеренно чуть меньше 60-секундного таймера на фронте (LoginPage.startTimer(60)):
# запас на джиттер setInterval / сетевую задержку, чтобы мгновенный клик по «Отправить
# повторно» сразу после таймера не упирался в 429.
RESEND_INTERVAL_SECONDS = 58

_app_settings = AppSettings()
_sms_settings = SmsAeroSettings()

sms_service = SMSService(
    email=_sms_settings.SMSAERO_EMAIL,
    api_key=_sms_settings.SMSAERO_API_KEY,
    sign=_sms_settings.SMSAERO_SIGN,
    test_mode=_app_settings.APP_ENV == "development",
)


@router.post("/request-code")
async def request_code(
    body: RequestCodeIn,
    session: AsyncSession = Depends(get_db),
):
    repo = ClientRepository(session)
    client = await repo.get_by_phone(body.phone)

    if client is not None and client.verification_sent_at is not None:
        elapsed = (datetime.now(timezone.utc) - client.verification_sent_at).total_seconds()
        if elapsed < RESEND_INTERVAL_SECONDS:
            wait = max(1, int(RESEND_INTERVAL_SECONDS - elapsed))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Повторно запросить код можно через {wait} сек",
            )

    is_new = not client
    if is_new:
        client = await repo.create(body.phone)

    code = generate_verification_code()
    await repo.set_verification_code(client, code)

    if is_new:
        try:
            await BaserowService().sync_client(client)
        except Exception:
            logger.exception("Не удалось синхронизировать клиента с Baserow")

    if _app_settings.APP_ENV == "development":
        logger.info("[DEV] Код подтверждения %s: %s", body.phone, code)
        return {"message": "Код отправлен", "code": code}

    try:
        await sms_service.send_verification_code(body.phone, code)
    except SMSSendError as e:
        logger.error("Не удалось отправить SMS на %s: %s", body.phone, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось отправить SMS. Попробуйте позже.",
        )

    return {"message": "Код отправлен"}


@router.post("/verify", response_model=AuthTokenOut)
async def verify_code(
    body: VerifyCodeIn,
    session: AsyncSession = Depends(get_db),
):
    repo = ClientRepository(session)
    client = await repo.get_by_phone(body.phone)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден",
        )

    try:
        token = await repo.verify_code(client, body.code)
    except TooManyVerifyAttemptsError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток. Запросите новый код.",
        )
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный или просроченный код",
        )

    is_new = not client.name or not client.street
    client_out = None if is_new else ClientOut.model_validate(client)

    return AuthTokenOut(
        token=token,
        is_new_client=is_new,
        client=client_out,
    )


@router.get("/me", response_model=ClientOut)
async def get_me(
    client: Client = Depends(get_current_client),
):
    return ClientOut.model_validate(client)


@router.patch("/me", response_model=ClientOut)
async def update_me(
    body: UpdateClientIn,
    client: Client = Depends(get_current_client),
    session: AsyncSession = Depends(get_db),
):
    repo = ClientRepository(session)
    updated = await repo.update(client, name=body.name)
    return ClientOut.model_validate(updated)
