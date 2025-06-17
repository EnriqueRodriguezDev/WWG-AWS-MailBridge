from typing import List, Optional

from pydantic import EmailStr, BaseModel, HttpUrl


class EmailRequest(BaseModel):
    from_email: EmailStr
    to:         List[EmailStr]
    cc:         List[EmailStr]      = []
    bcc:        List[EmailStr]      = []
    subject:    str
    body:       Optional[str]       = None
    html_body:  Optional[str]       = None
    attachments: List[str]         = []

class FileItem(BaseModel):
    filename:   str
    blob:       bytes
    id_proceso: int

'''class UploadRequest(BaseModel):
    files: Optional[List[FileItem]] = None'''

class UploadRequest(BaseModel):
    filename: str
    blob: bytes
    id_proceso: int