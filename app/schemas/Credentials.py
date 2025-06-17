from pydantic import BaseModel, Field


class CredentialMetadata(BaseModel):
    tipolval: str = Field(..., description="Grupo de configuración (TIPOLVAL)")
    descrip:  str = Field(..., description="Clave dentro del grupo (DESCRIP)")
    detail:   str = Field(..., description="DESCLONG: descripción extendida")

class UpdateCredentialIn(BaseModel):
    tipolval:  str = Field(..., description="Grupo TIPOLVAL")
    descrip:   str = Field(..., description="Clave DESCRIP dentro del grupo")
    value:     str = Field(..., max_length=100, description="Nuevo valor")

class UpdateCredentialOut(BaseModel):
    rows_affected: int = Field(..., description="Número de filas actualizadas (0 = nada)")
    ok:             bool  = Field(..., description="Verdadero si la operación fue exitosa")
    code:          int   = Field(..., description="Código de respuesta HTTP o interno")
    message:       str   = Field(..., description="Mensaje descriptivo del resultado")
