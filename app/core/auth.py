# app/core/auth_controller.py
import re
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.db.oracle import execute_query
from app.schemas.Auth import MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")

def validate_password_strength(password: str):
    """
    Valida la fortaleza de la contraseña.
    Lanza ValueError si la contraseña no cumple los requisitos.
    """
    if not MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH:
        raise ValueError(f"La contraseña debe tener entre {MIN_PASSWORD_LENGTH} y {MAX_PASSWORD_LENGTH} caracteres.")
    if not re.search(r"[a-z]", password):
        raise ValueError('La contraseña debe contener al menos una letra minúscula.')
    if not re.search(r"[A-Z]", password):
        raise ValueError('La contraseña debe contener al menos una letra mayúscula.')
    if not re.search(r"\d", password):
        raise ValueError('La contraseña debe contener al menos un número.')
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?~`]", password): # Asegúrate que este regex de símbolos es el mismo
        raise ValueError('La contraseña debe contener al menos un carácter especial (!@#$%^&*()_+-=[]{};\':"\\|,.<>/?~`).')
    return True

async def load_jwt_credentials(db_name: str) -> tuple[str, str]:
    """
    Lee usuario y password encriptado desde wws.lval con tu helper execute_query.
    """
    sql = """
      SELECT
        MAX(CASE WHEN codlval = 'JWTUSER' THEN Encrypt_pkg.DECRYPT(descrip) END) AS usuario,
        MAX(CASE WHEN codlval = 'JWTPASS' THEN Encrypt_pkg.DECRYPT(descrip) END) AS password
      FROM LVAL
     WHERE tipolval = :tipolval
       AND stslval  = :stslval
    """
    rows = await execute_query(
        sql,
        {
            "tipolval": settings.DB_JWT_TIPOLVAL,
            "stslval": settings.DB_STS_LVAL
        },
        db_name=db_name
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se encontraron credenciales JWT en la base de datos"
        )
    row = rows[0]
    return row["USUARIO"], row["PASSWORD"]


async def authenticate_user(db_name: str, username: str, password: str) -> bool:

    if db_name not in settings.AVAILABLE_DATABASES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La base de datos '{db_name}' no es una opción válida."
        )

    if settings.APP_ENV == "prod":
        if db_name not in settings.PROD_DATABASES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: No se puede acceder a la base de datos '{db_name}' "
                       f"desde un entorno de PRODUCCIÓN."
            )
    elif settings.APP_ENV == "qa":
        if db_name not in settings.QA_DATABASES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: No se puede acceder a la base de datos '{db_name}' "
                       f"desde un entorno de QA."
            )

    try:
        validate_password_strength(password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    db_user, db_pass = await load_jwt_credentials(db_name)
    return username == db_user and password == db_pass

def create_access_token(*, subject: str) -> tuple[str, int]:
    expire_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expire_delta
    to_encode = {"exp": expire, "sub": subject}
    encoded = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded, int(expire_delta.total_seconds())

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user = payload.get("sub")
        if user is None:
            raise JWTError()
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )