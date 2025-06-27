import base64
import os
from typing import List, Dict, Any, Optional

import oracledb
from fastapi import APIRouter, Body, Depends, Query, Request
from app.core.config import settings
from app.core.dependencies import _perform_database_access_check, check_database_access_query_param
from app.core.security import get_current_user
from app.helpers.aws_helper import AwsHelper, ALLOWED_FILE_EXTENSIONS
from app.schemas.EmailRequest import EmailRequest, UploadRequest
from services.lval_service import LvalConfig
from utils.fix_html_body import fix_html_body
from app.core.http_erros import HttpErrors

router = APIRouter(
    dependencies=[Depends(get_current_user)]
)

CLIENT_LIB_DIR = os.getenv("ORACLE_INSTANT_CLIENT_DIR")
if not os.path.isdir(CLIENT_LIB_DIR):
    raise RuntimeError(f"Ruta de Instant Client inválida: {CLIENT_LIB_DIR}")
oracledb.init_oracle_client(lib_dir=CLIENT_LIB_DIR)

AWS_BUCKET: str
AWS_PREFIX_S3: str


@router.post("/upload", response_model=List[Dict[str, Any]])
async def upload_and_process_blob(
        payload: UploadRequest = Body(...),
) -> List[Dict[str, Any]]:
    """
    Recibe un solo blob + id_proceso en JSON:
      { filename: str, blob: bytes (base64), id_proceso: int }
    O si falta alguno, hace el SELECT y usa id_proceso=1.
    Devuelve metadata con id_documento, id_proceso y size en KB.
    """
    _perform_database_access_check(payload.database)

    files: List[Dict[str, Any]] = []
    if payload.filename and payload.blob is not None and payload.id_proceso is not None:
        files.append({
            "filename": payload.filename,
            "blob": payload.blob,
            "id_proceso": payload.id_proceso,
        })

    if not files:  # Si después de procesar el payload, la lista sigue vacía
        raise HttpErrors.bad_request(detail="No se proporcionaron archivos válidos para procesar.")

    total_bytes = sum(len(f["blob"]) for f in files)
    if total_bytes > 8 * 1024 * 1024:
        raise HttpErrors.bad_request(detail="La carga total de archivos supera el límite de 8 MB.")

    try:
        lval = await LvalConfig.load(settings.DB_AWS_TIPOLVAL, db_name=payload.database)
        AWS_BUCKET = lval.get(settings.DB_AWS_BUCKET)
        AWS_PREFIX_S3 = lval.get(settings.DB_AWS_S3_PREFIX)

        if not all([AWS_BUCKET, AWS_PREFIX_S3]):
            raise ValueError("Configuración de Bucket S3 o prefijo de S3 no encontrada en LVAL.")

        metadata = await AwsHelper.upload_blobs_to_s3(files,
                                                      bucket=AWS_BUCKET,
                                                      prefix=AWS_PREFIX_S3,
                                                      database=payload.database)
        for item, finfo in zip(metadata, files):
            item["id_documento"] = item.get("key")
            item["id_proceso"] = finfo["id_proceso"]
            size_bytes = item.get("size", 0)
            item["size"] = f"{int(size_bytes / 1024)}kb"

        return metadata
    except HttpErrors as e:
        raise e
    except Exception as e:
        raise HttpErrors.internal_server_error(detail=f"Error inesperado al procesar la carga: {e}")


@router.post("/upload-raw-blob", response_model=List[Dict[str, Any]])
async def upload_raw_blob(
        request: Request,
        filename: str = Query(..., description="Nombre del archivo (e.g., 'documento.pdf')"),
        id_proceso: int = Query(..., description="ID del proceso asociado al archivo"),
        database: str = Depends(check_database_access_query_param)
) -> List[Dict[str, Any]]:
    """
    Recibe el BLOB (contenido binario) directamente en el cuerpo de la solicitud HTTP.
    El filename y id_proceso se pasan como query parameters.
    """
    content_type = request.headers.get("Content-Type")
    if not content_type or not content_type.startswith("application/"):
        raise HttpErrors.bad_request(detail="Content-Type debe ser 'application/pdf' o similar.")

    raw_pdf_bytes = await request.body()

    if not raw_pdf_bytes:
        raise HttpErrors.bad_request(detail="El cuerpo de la solicitud está vacío.")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise HttpErrors.bad_request(
            detail=f"Tipo de archivo no permitido para '{filename}'. "
                   f"Extensiones válidas: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
        )

    files: List[Dict[str, Any]] = [{
        "filename": filename,
        "blob": raw_pdf_bytes,
        "id_proceso": id_proceso,
    }]

    try:
        lval = await LvalConfig.load(settings.DB_AWS_TIPOLVAL, db_name=database)
        AWS_BUCKET = lval.get(settings.DB_AWS_BUCKET)
        AWS_PREFIX_S3 = lval.get(settings.DB_AWS_S3_PREFIX)

        if not all([AWS_BUCKET, AWS_PREFIX_S3]):
            raise ValueError("Configuración de Bucket S3 o prefijo de S3 no encontrada en LVAL.")

        metadata = await AwsHelper.upload_blobs_to_s3(files,
                                                      bucket=AWS_BUCKET,
                                                      prefix=AWS_PREFIX_S3,
                                                      database=database)
        for item, finfo in zip(metadata, files):
            item["id_documento"] = item.get("key")
            item["id_proceso"] = finfo["id_proceso"]
            size_bytes = item.get("size", 0)
            item["size"] = f"{int(size_bytes / 1024)}kb"

        return metadata
    except HttpErrors as e:
        raise e
    except Exception as e:
        raise HttpErrors.internal_server_error(detail=f"Error inesperado al subir el blob: {e}")


@router.post("/send-email")
async def send_email_with_html(request: EmailRequest = Body(...)) -> Dict[str, Any]:
    """
    Envía un email usando html_body.
    Los tipos coinciden exactamente con EmailRequest.
    """

    _perform_database_access_check(request.database)

    try:
        use_html = bool(request.html_body and request.html_body.strip())

        fixed_html = fix_html_body(request.html_body) if request.html_body else None

        message_id = await AwsHelper.send_email(
            from_addr=request.from_email,
            to_addrs=request.to,
            cc=request.cc,
            bcc=request.bcc,
            subject=request.subject,
            body=None if use_html else request.body,
            html_body=fixed_html if use_html else None,
            attachments=request.attachments,
            tags=request.tags,
            database=request.database
        )

        return message_id

    except HttpErrors as e:
        raise e
    except Exception as e:
        raise HttpErrors.internal_server_error(detail=f"Error inesperado al enviar el email: {e}")