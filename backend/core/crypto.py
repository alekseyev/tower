from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt

from backend.settings import settings

_hasher = PasswordHasher()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return _hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def get_password_hash(password: str) -> str:
    return _hasher.hash(password)


def encode_jwt_token(claims: dict) -> str:
    return jwt.encode(
        claims,
        key=settings.AUTH_SECRET,
        algorithm="HS256",
    )
