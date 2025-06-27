# app/core/config.py
import os
from pathlib import Path
from typing import Dict, Any, Literal, List, ClassVar

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class DatabaseConfig(BaseSettings):
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_SERVICE_NAME: str

class Settings(BaseSettings):

    ORACLE_INSTANT_CLIENT_DIR: str
    API_V1_PREFIX:         str = "/api/v1"
    DB_PORT:               int

    APP_ENV: Literal["prod", "qa", "dev", "local"] = "dev"
    PROD_DATABASES: List[str] = ["SEGWW", "WWMA"]
    QA_DATABASES: List[str] = ["SEGQA", "WWMAQA"]

    AVAILABLE_DATABASES: ClassVar[List[str]] = PROD_DATABASES + QA_DATABASES

    DATABASE_CONNECTIONS: Dict[str, DatabaseConfig] = {}

    # → AWS / SQS / S3
    DB_AWS_TIPOLVAL:       str
    DB_AWS_KEY:            str
    DB_AWS_SECRET:         str
    DB_AWS_REGION:         str
    DB_AWS_QUEUE:          str
    DB_AWS_BUCKET:         str
    DB_AWS_S3_PREFIX:      str
    DB_STS_LVAL:           str

    # → JWT
    DB_JWT_TIPOLVAL:       str
    DB_USER_JWT:           str
    DB_PASS_JWT:           str
    JWT_SECRET:            str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_ALGORITHM: str

    model_config = SettingsConfigDict(
        env_file = '.env',
        env_file_encoding = "utf-8",
        extra = "ignore",
        case_sensitive = False
    )

    def __init__(self, **data: Any):
        super().__init__(**data)
        for db_name in self.AVAILABLE_DATABASES:
            host_var = f"DB_{db_name.upper()}_HOST"
            user_var = f"DB_{db_name.upper()}_USER"
            password_var = f"DB_{db_name.upper()}_PASSWORD"
            service_name_var = f"DB_{db_name.upper()}_SERVICE_NAME"

            db_host = os.getenv(host_var)
            db_user = os.getenv(user_var)
            db_password = os.getenv(password_var)
            db_service_name = os.getenv(service_name_var)

            if not all([db_host, db_user, db_password, db_service_name]):
                print(f"Advertencia: No se pudo cargar la configuración completa para la base de datos '{db_name}'.")
                print(f"Asegúrese de que las variables {host_var}, {user_var}, {password_var}, {service_name_var} están definidas en su archivo .env")
                continue

            try:
                self.DATABASE_CONNECTIONS[db_name] = DatabaseConfig(
                    DB_HOST=db_host,
                    DB_USER=db_user,
                    DB_PASSWORD=db_password,
                    DB_SERVICE_NAME=db_service_name
                )
                print(f"Configuración para '{db_name}' cargada exitosamente.")
            except Exception as e:
                print(f"Error inesperado al procesar la configuración para '{db_name}': {e}")
                print(f"Valores obtenidos: HOST={db_host}, USER={db_user}, PASS={'*' * len(db_password) if db_password else 'None'}, SERVICE_NAME={db_service_name}")

settings = Settings()
