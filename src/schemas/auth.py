from pydantic import BaseModel


class RequestCodeIn(BaseModel):
    phone: str


class VerifyCodeIn(BaseModel):
    phone: str
    code: str


class AuthTokenOut(BaseModel):
    token: str
    is_new_client: bool
    client: "ClientOut | None" = None


class ClientOut(BaseModel):
    id: int
    phone: str
    name: str | None
    street: str
    house: str
    apartment: int
    entrance: int
    floor: int

    model_config = {"from_attributes": True}
