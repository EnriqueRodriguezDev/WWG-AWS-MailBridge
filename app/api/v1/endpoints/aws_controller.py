import os
from typing import List, Dict, Any, Optional

import oracledb
from fastapi import APIRouter, HTTPException, Body, Depends
from app.core.config import settings
from app.core.security import get_current_user
from app.helpers.aws_helper import AwsHelper
from app.schemas.EmailRequest import EmailRequest, UploadRequest
from services.lval_service import LvalConfig
from utils.fix_html_body import fix_html_body

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
    files: List[Dict[str, Any]] = []

    # 1) Caso de payload completo
    if payload.filename and payload.blob is not None and payload.id_proceso is not None:
        files.append({
            "filename":   payload.filename,
            "blob":       payload.blob,
            "id_proceso": payload.id_proceso,
        })
    else:
        # 2) Fallback: leer de Oracle y poner id_proceso=1
        conn = oracledb.connect(
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            dsn=f"{settings.DB_HOST}/{settings.DB_SERVICE_NAME}",
        )
        cursor = conn.cursor()
        sql = """
   	 SELECT filename, blob_data
        FROM (
            SELECT 'CARNET_1157792.PDF' AS filename,
                   ACSELD.GET_FILE_BLOB('MAIL_ENVIADOS', 'CARNET_1157792.PDF') AS blob_data
            FROM dual
            UNION ALL
            SELECT 'SALDO_X_ANT_000015_16-JUN-25_1.PDF' AS filename,
                   ACSELD.GET_FILE_BLOB('MAIL_ENVIADOS', 'SALDO_X_ANT_000015_16-JUN-25_1.PDF') AS blob_data
            FROM dual
            UNION ALL
            SELECT 'RECIBO_PAGO_165300_002373.PDF' AS filename,
                   ACSELD.GET_FILE_BLOB('MAIL_ENVIADOS', 'RECIBO_PAGO_165300_002373.PDF') AS blob_data
            FROM dual
                        UNION ALL
            SELECT 'RECIBO_PAGO_165300_002373.PDF' AS filename,
                   ACSELD.GET_FILE_BLOB('MAIL_ENVIADOS', 'RECIBO_PAGO_165280_002345.PDF') AS blob_data
            FROM dual
            
            )
        """
        cursor.execute(sql)
        for filename, blob_data in cursor:
            if blob_data:
                raw = blob_data.read() if hasattr(blob_data, "read") else blob_data
                files.append({
                    "filename":   filename,
                    "blob":       raw,
                    "id_proceso": 1
                })
        cursor.close()
        conn.close()

    if not files:
        raise HTTPException(status_code=404, detail="No files to process")

    # 3) Verificar que el total no exceda 8 MB
    total_bytes = sum(len(f["blob"]) for f in files)
    if total_bytes > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="La carga total supera los 8 MB")

    lval          = await LvalConfig.load(settings.DB_AWS_TIPOLVAL)
    AWS_BUCKET    = lval.get(settings.DB_AWS_BUCKET)
    AWS_PREFIX_S3 = lval.get(settings.DB_AWS_S3_PREFIX)

    # 4) Subir a S3 y enriquecer metadata
    metadata = await AwsHelper.upload_blobs_to_s3(files, bucket=AWS_BUCKET, prefix=AWS_PREFIX_S3)
    for item, finfo in zip(metadata, files):
        item["id_documento"] = item.get("key")
        item["id_proceso"]   = finfo["id_proceso"]
        # 'size' viene en bytes, lo convertimos a KB
        size_bytes = item.get("size", 0)
        item["size"] = f"{int(size_bytes / 1024)}kb"

    return metadata


@router.post("/send-email")
async def send_email_with_html(request: EmailRequest = Body(...)) -> Dict[str, Any]:
    """
    Envía un email usando html_body.
    Los tipos coinciden exactamente con EmailRequest.
    """
    try:
        use_html = bool(request.html_body and request.html_body.strip())

        fixed_html = fix_html_body(request.html_body) if request.html_body else None

        message_id = await AwsHelper.send_email(
            from_addr   = request.from_email,
            to_addrs    = request.to,
            cc          = request.cc,
            bcc         = request.bcc,
            subject     = request.subject,
            body        = None if use_html else request.body,
            html_body   = fixed_html if use_html else None,
            attachments = request.attachments,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message_id": message_id}
