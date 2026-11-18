import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_current_client, get_db
from src.models.client import Client
from src.repositories.client import ClientRepository, TooManyVerifyAttemptsError
from src.schemas.auth import RequestCodeIn, RequestCodeOut, VerifyCodeIn, AuthTokenOut, ClientOut, UpdateClientIn
from src.repositories.system_settings import get_system_settings
from src.services.auth import generate_verification_code, is_debug_phone, is_mobile_phone
from src.services.sms import SMSSendError, SMSService
from src.settings import SmsAeroSettings

logger = logging.getLogger(__name__)

router = APIRouter()

# Минимальный интервал между запросами кода на один номер (антифлуд / анти-SMS-бомбинг).
# Намеренно чуть меньше 60-секундного таймера на фронте (LoginPage.startTimer(60)):
# запас на джиттер setInterval / сетевую задержку, чтобы мгновенный клик по «Отправить
# повторно» сразу после таймера не упирался в 429.
RESEND_INTERVAL_SECONDS = 58

_sms_settings = SmsAeroSettings()

sms_service = SMSService(
    email=_sms_settings.SMSAERO_EMAIL,
    api_key=_sms_settings.SMSAERO_API_KEY,
    sign=_sms_settings.SMSAERO_SIGN,
)


@router.post("/request-code", response_model=RequestCodeOut)
async def request_code(
    body: RequestCodeIn,
    session: AsyncSession = Depends(get_db),
):
    sys_settings = await get_system_settings(session)
    debug_phone = is_debug_phone(body.phone, sys_settings)
    if not debug_phone and not is_mobile_phone(body.phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Введите номер мобильного телефона полностью",
        )

    repo = ClientRepository(session)
    client = await repo.get_by_phone(body.phone)

    # Новый номер: без согласия с офертой код не шлём (требование SMS-сервиса) и клиента не создаём —
    # фронтенд покажет шаг регистрации и запросит код снова. Ответ выдаёт, зарегистрирован ли номер;
    # это осознанно: иначе нельзя пускать зарегистрированных без галочек.
    registered = client is not None and client.is_registered
    if not registered and not body.offer_accepted:
        return RequestCodeOut(message="Нужна регистрация", registration_required=True)

    if client is not None and client.verification_sent_at is not None:
        elapsed = (datetime.now(timezone.utc) - client.verification_sent_at).total_seconds()
        if elapsed < RESEND_INTERVAL_SECONDS:
            wait = max(1, int(RESEND_INTERVAL_SECONDS - elapsed))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Повторно запросить код можно через {wait} сек",
            )

    if not client:
        client = await repo.create(body.phone)

    code = generate_verification_code()
    await repo.set_verification_code(client, code)

    # Вход по SMS выключен в админке или номер отладочный — SMS не шлём, код показывается на странице.
    if debug_phone and sys_settings.sms_enabled:
        # След в логе: вход без SMS при включённом входе по SMS должен быть виден.
        logger.warning("Код для отладочного номера %s показан на странице", body.phone)
    if not sys_settings.sms_enabled or debug_phone:
        return RequestCodeOut(message="Код отправлен", code=code)

    try:
        await sms_service.send_verification_code(body.phone, code)
    except SMSSendError as e:
        logger.error("Не удалось отправить SMS на %s: %s", body.phone, e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Не удалось отправить SMS. Попробуйте позже.",
        )

    return RequestCodeOut(message="Код отправлен")


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

    # Запоминаем до проверки кода: verify_code ставит is_verified, и новый клиент выглядел бы
    # зарегистрированным раньше, чем сохранены его email и согласия.
    registering = not client.is_registered
    # Проверяем до кода, чтобы не сжечь код из-за незаполненной формы.
    if registering and (not body.offer_accepted or body.email is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Укажите email и примите условия оферты",
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

    # Согласия и email фиксируем только после подтверждения номера — значит, их дал владелец телефона.
    # При обычном входе их не трогаем: email и согласие на рассылку остаются как при регистрации.
    if registering:
        await repo.set_consents(client, body.offer_accepted, body.sms_marketing_consent)
        await repo.update(client, email=body.email)

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
