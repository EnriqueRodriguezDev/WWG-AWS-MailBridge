# app/core/dependencies.py
from fastapi import HTTPException, status, Query
from app.core.config import settings

def _perform_database_access_check(database_name: str):
    """
    Lógica central para validar que el acceso a la base de datos
    corresponda al entorno de la aplicación actual (PROD vs QA).
    Lanza HTTPException si el acceso es denegado.
    """
    # 1. Validar que la base de datos solicitada exista en las configuraciones
    if database_name not in settings.AVAILABLE_DATABASES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La base de datos '{database_name}' no es una opción válida."
        )

    # 2. Control de acceso por entorno
    if settings.APP_ENV == "prod":
        if database_name not in settings.PROD_DATABASES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: No se puede acceder a la base de datos '{database_name}' "
                       f"desde un entorno de PRODUCCIÓN."
            )
    elif settings.APP_ENV == "qa":
        if database_name not in settings.QA_DATABASES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado: No se puede acceder a la base de datos '{database_name}' "
                       f"desde un entorno de QA."
            )
    elif settings.APP_ENV == "dev" or settings.APP_ENV == "local":
        # En entornos de desarrollo/local, podrías ser más flexible.
        # Aquí, permitimos acceso a todas las bases de datos disponibles para facilidad de desarrollo.
        pass
    else:
        # Esto es un caso de "APP_ENV" desconocido/no configurado.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de configuración: Entorno de aplicación '{settings.APP_ENV}' no reconocido."
        )


# Dependencia de FastAPI para usar con parámetros de consulta (Query)
async def check_database_access_query_param(database: str = Query(..., description="Nombre de la base de datos")):
    """
    Dependencia que valida el acceso a la base de datos cuando el parámetro 'database'
    viene como un query parameter.
    """
    _perform_database_access_check(database)
    return database