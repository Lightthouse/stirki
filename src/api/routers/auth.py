from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db
from src.repositories.client import ClientRepository
from src.schemas.auth import RequestCodeIn, VerifyCodeIn, AuthTokenOut, ClientOut
from src.services.auth import generate_verification_code

router = APIRouter()


@router.post("/request-code")
async def request_code(
    body: RequestCodeIn,
    session: AsyncSession = Depends(get_db),
):
    repo = ClientRepository(session)
    client = await repo.get_by_phone(body.phone)

    if not client:
        client = await repo.create(body.phone)

    code = generate_verification_code()
    await repo.set_verification_code(client, code)

    # MVP: возвращаем код в ответе (потом заменить на SMS)
    return {"message": "Код отправлен", "code": code}


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

    token = await repo.verify_code(client, body.code)
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
