# app/api/v1/endpoints/credentials_controller.py
from typing     import List
import oracledb
from fastapi    import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.oracle import execute_query, call_proc_update
from app.schemas.Credentials import CredentialMetadata, UpdateCredentialOut
from app.core.security   import get_current_user

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

# Parámetros de cada grupo
GROUPS = {
    settings.DB_AWS_TIPOLVAL:
        [
            settings.DB_AWS_QUEUE,
            settings.DB_AWS_SECRET,
            settings.DB_AWS_KEY,
            settings.DB_AWS_BUCKET,
            settings.DB_AWS_REGION,
            settings.DB_AWS_S3_PREFIX
        ],
    settings.DB_JWT_TIPOLVAL:
        [
            settings.DB_USER_JWT,
            settings.DB_PASS_JWT
        ]
}

GROUP_LABELS = {
    settings.DB_AWS_TIPOLVAL: "AWS Configuración",
    settings.DB_JWT_TIPOLVAL: "Credenciales Usuario API MailBridge"
}

def make_group_router(tipolval: str) -> APIRouter:
    grp = APIRouter(
        prefix=f"/credentials/{tipolval.lower()}",
        tags=[GROUP_LABELS[tipolval]]
    )

    @grp.get("/", response_model=List[CredentialMetadata])
    async def list_group():
        rows = await execute_query(
            """
            SELECT descrip, desclong
              FROM ACSELD.lval
             WHERE tipolval = :tv
               AND stslval  = 'ACT'
            """,
            {"tv": tipolval}
        )
        return [
            CredentialMetadata(
                tipolval=tipolval,
                descrip = r["DESCRIP"],
                detail  = r["DESCLONG"] or ""
            )
            for r in rows
        ]

    @grp.post("/update", response_model=UpdateCredentialOut)
    async def update_group(
        descrip: str = Query(..., enum=GROUPS[tipolval]),
        value:   str = Query(...),
    ):
        # TODO AGREGAR CONDICION QUE SI ES CLAVE DEL USUARIO JWT DEBE TENER UNA CLAVE DIFERENTE A LA ANTERIOR Y FUERTE
        if len(value) > 99:
            raise HTTPException(
               status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
               detail="La longitud máxima es 99 caracteres"
            )

        try:
            filas = await call_proc_update(
                "ACSELD.P_UPDATE_LVAL",
                [tipolval, descrip, "S", value]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error en P_UPDATE_LVAL: {e}"
            )
        ok = filas > 0
        code = status.HTTP_200_OK
        message = "Actualización exitosa" if ok else "No se modificaron registros"

        return UpdateCredentialOut(
            rows_affected=filas,
            ok=ok,
            code=code,
            message=message
        )

    return grp

router.include_router(make_group_router("AWSCONF"))
router.include_router(make_group_router("MJWTCRED"))

# TODO: GENERAL PROTEGER LOS ENDPOINTS DE SQL INYECCION EN ORACLE
# TODO: VERIFICAR SOBRE TODO EN EL HTML_BODY, BODY, CAMPOS DEL CORREO Y CREDENCIALES
