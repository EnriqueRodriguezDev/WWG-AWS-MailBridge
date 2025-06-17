# app/core/config.py

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # → Oracle

    ORACLE_INSTANT_CLIENT_DIR: str

    API_V1_PREFIX:         str = "/api/v1"

    DB_PORT:               int
    DB_HOST:               str
    DB_USER:               str
    DB_PASSWORD:           str
    DB_SERVICE_NAME:       str

    # → AWS / SQS / S3
    DB_AWS_TIPOLVAL:       str
    DB_AWS_KEY:            str
    DB_AWS_SECRET:         str
    DB_AWS_REGION:         str
    DB_AWS_QUEUE:          str
    DB_AWS_BUCKET:         str
    DB_AWS_S3_PREFIX:             str
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

settings = Settings()
