# app/api/v1/endpoints/credentials_controller.py
from typing import List
import oracledb
import re  # Importar el módulo re para expresiones regulares

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import validate_password_strength
from app.core.config import settings
from app.core.dependencies import check_database_access_query_param
from app.db.oracle import execute_query, call_proc_update
from app.schemas.Credentials import CredentialMetadata, UpdateCredentialOut
from app.core.security import get_current_user

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

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
    async def list_group(database: str = Depends(check_database_access_query_param)):
        rows = await execute_query(
            """
            SELECT codlval, desclong
              FROM LVAL
             WHERE tipolval = :tv
               AND stslval  = 'ACT'
            """,
            {"tv": tipolval},
            db_name=database
        )
        return [
            CredentialMetadata(
                tipolval=tipolval,
                codlval=r["CODLVAL"],
                detail=r["DESCLONG"] or ""
            )
            for r in rows
        ]

    @grp.post("/update", response_model=UpdateCredentialOut)
    async def update_group(
            database: str = Depends(check_database_access_query_param),
            codlval: str = Query(..., enum=GROUPS[tipolval]),
            value: str = Query(...),
    ):
        # Validación de longitud general
        if len(value) > 99:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La longitud máxima permitida es 99 caracteres."
            )

        # VALIDACIONES ESPECÍFICAS PARA JWTPASS
        if tipolval == settings.DB_JWT_TIPOLVAL and codlval == settings.DB_PASS_JWT:
            if not (8 <= len(value) <= 30):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="La contraseña de JWT debe tener entre 8 y 30 caracteres."
                )

            try:
                validate_password_strength(value)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=str(e)
                )

            if tipolval == settings.DB_JWT_TIPOLVAL and codlval == settings.DB_PASS_JWT:

                try:
                    current_password_row = await execute_query(
                        """
                        SELECT Encrypt_pkg.DECRYPT(descrip) as CURRENT_VALUE
                        FROM LVAL
                        WHERE tipolval = :tv AND codlval = :cv
                        """,
                        {"tv": tipolval, "cv": codlval},
                        db_name=database
                    )

                except oracledb.Error as e:
                    print(f"Error de base de datos al verificar la contraseña actual: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error al verificar la contraseña actual en la base de datos. Por favor, inténtelo de nuevo."
                    )
                except Exception as e:
                    print(f"Error inesperado al verificar la contraseña actual: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Error interno al verificar la contraseña actual. Por favor, inténtelo de nuevo."
                    )

                if current_password_row and current_password_row[0]["CURRENT_VALUE"] == value:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="La nueva contraseña no puede ser igual a la contraseña actual."
                    )

        try:
            filas = await call_proc_update(
                "PR_MAILBRIDGE.P_UPDATE_LVAL",
                [tipolval, codlval, "S", value], # El "S" indica que el valor debe ser encriptado
                db_name=database
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error en PR_MAILBRIDGE.P_UPDATE_LVAL: {e}"
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