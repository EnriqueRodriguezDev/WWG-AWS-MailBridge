# app/core/auth_controller.py
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import settings
from app.db.oracle import execute_query

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


async def load_jwt_credentials() -> tuple[str, str]:
    """
    Lee usuario y password encriptado desde wws.lval con tu helper execute_query.
    """
    sql = """
      SELECT
        MAX(CASE WHEN descrip = 'JWTUSER' THEN codlval END) AS usuario,
        MAX(CASE WHEN descrip = 'JWTPASS' THEN codlval END) AS password
      FROM ACSELD.lval
     WHERE tipolval = :tipolval
       AND stslval  = :stslval
    """
    rows = await execute_query(
        sql,
        {
            "tipolval": settings.DB_JWT_TIPOLVAL,
            "stslval": settings.DB_STS_LVAL
        }
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se encontraron credenciales JWT en la base de datos"
        )
    row = rows[0]
    return row["USUARIO"], row["PASSWORD"]


async def authenticate_user(username: str, password: str) -> bool:
    db_user, db_pass = await load_jwt_credentials()
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