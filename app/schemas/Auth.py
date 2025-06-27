from dataclasses import field
from typing import Literal
from pydantic import BaseModel, Field, validator, field_validator  # Importamos 'validator'
import re # Importamos 're' para usar expresiones regulares
from app.core.config import settings

DatabaseLiteral = Literal[tuple(settings.AVAILABLE_DATABASES)]

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 30

class LoginRequest(BaseModel):
    database: DatabaseLiteral
    username: str
    password: str = Field(
        ...,
        min_length=MIN_PASSWORD_LENGTH,
        max_length=MAX_PASSWORD_LENGTH,
        description=f"La contraseña debe tener entre {MIN_PASSWORD_LENGTH} y {MAX_PASSWORD_LENGTH} caracteres, "
                    "incluir al menos una mayúscula, una minúscula, un número y un símbolo."
    )

    @field_validator('password')
    def password_complexity(cls, v):
        if not re.search(r"[a-z]", v):
            raise ValueError('La contraseña debe contener al menos una letra minúscula.')
        if not re.search(r"[A-Z]", v):
            raise ValueError('La contraseña debe contener al menos una letra mayúscula.')
        if not re.search(r"\d", v):
            raise ValueError('La contraseña debe contener al menos un número.')
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]", v):
            raise ValueError('La contraseña debe contener al menos un carácter especial (!@#$%^&*()_+-=[]{};\':"\\|,.<>/?~`).')
        return v


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class TokenPayload(BaseModel):
    sub: str
    exp: int