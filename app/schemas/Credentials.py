from typing import Literal
from pydantic import BaseModel, Field
from app.core.config import settings

DatabaseLiteral = Literal[tuple(settings.AVAILABLE_DATABASES)]

class CredentialMetadata(BaseModel):
    tipolval: str = Field(..., description="Grupo de configuración (TIPOLVAL)")
    codlval:  str = Field(..., description="Clave dentro del grupo (CODLVAL)")
    detail:   str = Field(..., description="DESCLONG: descripción extendida")

class UpdateCredentialIn(BaseModel):
    database: DatabaseLiteral
    tipolval:  str = Field(..., description="Grupo TIPOLVAL")
    codlval:   str = Field(..., description="Clave CODLVAL dentro del grupo")
    value:     str = Field(..., max_length=100, description="Nuevo valor")

class UpdateCredentialOut(BaseModel):
    rows_affected: int = Field(..., description="Número de filas actualizadas (0 = nada)")
    ok:             bool  = Field(..., description="Verdadero si la operación fue exitosa")
    code:           int   = Field(..., description="Código de respuesta HTTP o interno")
    message:        str   = Field(..., description="Mensaje descriptivo del resultado")