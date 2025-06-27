from typing import List, Optional, Dict, Literal
from pydantic import EmailStr, BaseModel
from app.core.config import settings

DatabaseLiteral = Literal[tuple(settings.AVAILABLE_DATABASES)]

class EmailRequest(BaseModel):
    database: DatabaseLiteral
    from_email: EmailStr
    to:         List[EmailStr]
    cc:         List[EmailStr]      = []
    bcc:        List[EmailStr]      = []
    subject:    str
    body:       Optional[str]       = None
    html_body:  Optional[str]       = None
    attachments: List[str]         = []
    tags:        Dict[str, str]        = {}

class FileItem(BaseModel):
    database: DatabaseLiteral
    filename:   str
    blob:       bytes
    id_proceso: int

class UploadRequest(BaseModel):
    database: DatabaseLiteral
    filename: str
    blob: bytes
    id_proceso: int