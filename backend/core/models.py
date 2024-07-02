import asyncio
from typing import Annotated
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import BaseModel, Field

from backend.core.crypto import get_password_hash, verify_password


class JWTUser(BaseModel):
    id: str
    email: str


class LoginData(BaseModel):
    email: str
    password: str


class RegisterData(BaseModel):
    email: str
    nickname: str
    password: str


class PasswordData(BaseModel):
    password: str


class User(Document):
    id: UUID = Field(default_factory=uuid4)
    nickname: str
    email: Annotated[str, Indexed(unique=True)]
    password_hash: str | None = None

    class Settings:
        name = "users"

    @classmethod
    async def create_user(cls, email: str, nickname: str, password: str) -> "User":
        from backend.courses.models import UserProgress

        user = User(nickname=nickname, email=email, password_hash=get_password_hash(password))
        await asyncio.gather(
            user.insert(),
            UserProgress(id=user.id).insert(),
        )

        return user

    @classmethod
    async def by_email(cls, email: str) -> "User":
        return await cls.find_one(cls.email == email)

    def set_password(self, password: str):
        self.password_hash = get_password_hash(password)

    def verify_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return verify_password(password, self.password_hash)


core_models = [User]
