import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.client import Client


TOKEN_LIFETIME = timedelta(days=60)


class ClientRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_phone(self, phone: str) -> Client | None:
        result = await self.session.execute(select(Client).where(Client.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> Client | None:
        result = await self.session.execute(
            select(Client).where(
                Client.auth_token == token,
                Client.is_verified == True,  # noqa: E712
                Client.auth_token_expires_at > func.now(),
            )
        )
        client = result.scalar_one_or_none()
        if client:
            client.auth_token_expires_at = datetime.now(timezone.utc) + TOKEN_LIFETIME
            await self.session.commit()
        return client

    async def create(self, phone: str) -> Client:
        client = Client(phone=phone)
        self.session.add(client)
        await self.session.commit()
        await self.session.refresh(client)
        return client

    async def set_verification_code(self, client: Client, code: str) -> None:
        client.verification_code = code
        client.verification_expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=5
        )
        await self.session.commit()

    async def verify_code(self, client: Client, code: str) -> str | None:
        """Verify code and return auth token if valid, None otherwise."""
        if not client.verification_code or not client.verification_expires_at:
            return None
        if client.verification_code != code:
            return None
        if datetime.now(timezone.utc) > client.verification_expires_at:
            return None

        token = str(uuid.uuid4())
        client.auth_token = token
        client.auth_token_expires_at = datetime.now(timezone.utc) + TOKEN_LIFETIME
        client.is_verified = True
        client.verification_code = None
        client.verification_expires_at = None
        await self.session.commit()
        return token

    async def update(
        self,
        client: Client,
        *,
        name: str | None = None,
        email: str | None = None,
        street: str | None = None,
        house: str | None = None,
        apartment: int | None = None,
        entrance: int | None = None,
        floor: int | None = None,
        comment: str | None = None,
    ) -> Client:
        if name is not None:
            client.name = name
        if email is not None:
            client.email = email
        if street is not None:
            client.street = street
        if house is not None:
            client.house = house
        if apartment is not None:
            client.apartment = apartment
        if entrance is not None:
            client.entrance = entrance
        if floor is not None:
            client.floor = floor
        if comment is not None:
            client.comment = comment
        await self.session.commit()
        await self.session.refresh(client)
        return client
