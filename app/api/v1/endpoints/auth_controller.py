# app/api/v1/endpoints/auth_controller.py
from fastapi import APIRouter, HTTPException, status
from app.schemas.Auth import LoginRequest, Token
from app.core.auth import authenticate_user, create_access_token

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=Token, summary="Obtener token JWT")
async def login(creds: LoginRequest):
    """
    Valida usuario/clave y retorna un JWT.
    """
    ok = await authenticate_user(creds.username, creds.password)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expires_in = create_access_token(subject=creds.username.upper())
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in
    }