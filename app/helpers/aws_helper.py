import io
import json
import os
from typing import List, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
from fastapi import Form
from pydantic import EmailStr, HttpUrl

from app.core.config import settings
from services.lval_service import LvalConfig
from utils.compress_pdf_bytes import compress_pdf_bytes
from app.core.http_erros import HttpErrors

ALLOWED_FILE_EXTENSIONS = {
    ".jpg",
    ".pdf",
    ".png",
    ".jpeg",
    ".doc",
    ".docx",
    ".xlsx",
    ".xls",
    ".csv"
}

class AwsHelper:

    @staticmethod
    async def upload_blobs_to_s3(
        files: List[Dict[str, bytes]],
        bucket: str,
        prefix: str,
        database: str,
    ) -> List[Dict[str, Any]]:
        """
        Process list of dicts with keys:
          - 'filename': str
          - 'blob': bytes

        Compress PDFs, upload each to S3 in-memory,
        and return metadata list:
          [{ 'filename': str, 'url': str, 'size': int }, ...]
        """
        try:
            lval = await LvalConfig.load(settings.DB_AWS_TIPOLVAL, db_name=database)

            aws_access_key_id = lval.get(settings.DB_AWS_KEY)
            aws_secret_access_key = lval.get(settings.DB_AWS_SECRET)
            region_name = lval.get(settings.DB_AWS_REGION)

            if not all([aws_access_key_id, aws_secret_access_key, region_name, bucket, prefix]):
                raise ValueError(f"Configuración AWS S3 incompleta para la base de datos '{database}'.")

            s3 = boto3.client(
                "s3",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )

            results: List[Dict[str, Any]] = []
            for item in files:
                filename = item.get("filename")
                blob = item.get("blob")
                if not filename or blob is None:
                    continue

                ext = os.path.splitext(filename)[1].lower()
                if ext not in ALLOWED_FILE_EXTENSIONS:
                    raise HttpErrors.bad_request(
                        detail=f"Tipo de archivo no permitido para '{filename}'. "
                               f"Extensiones válidas: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
                    )
                print(f'ext f{ext}')

                data = blob
                size: int = len(blob)

                if ext == ".pdf":
                    data, size = compress_pdf_bytes(blob)

                key = f"{prefix}{filename}"
                s3.upload_fileobj(io.BytesIO(data), bucket, key)
                uri = f"s3://{bucket}/{key}"

                results.append({
                    'filename': filename,
                    'url': uri,
                    'size': size
                })

            return results
        except ClientError as e:
            if "NoSuchBucket" in str(e):
                raise HttpErrors.not_found(detail=f"Bucket S3 '{bucket}' no encontrado o no accesible: {e}")
            elif "AccessDenied" in str(e):
                raise HttpErrors.forbidden(detail=f"Permiso denegado para S3. Revise sus credenciales o políticas de Bucket: {e}")
            else:
                raise HttpErrors.internal_server_error(detail=f"Error del cliente S3 al subir archivos: {e}")
        except ValueError as e:
            raise HttpErrors.internal_server_error(detail=f"Error de configuración AWS: {e}")
        except Exception as e:
            raise HttpErrors.internal_server_error(detail=f"Error interno del servidor al subir a S3: {e}")

    @staticmethod
    async def send_email(from_addr: EmailStr,
                         to_addrs: List[EmailStr],
                         cc: Optional[List[EmailStr]] = None,
                         bcc: Optional[List[EmailStr]] = None,
                         subject: str = None,
                         body: Optional[str] = None,
                         html_body: Optional[str] = None,
                         attachments: Optional[List[str]] = None,
                         tags: Optional[Dict[str, str]] = None,
                         database: str = None) -> Dict[str, Any]:
        """
        Encola un mensaje para envío vía SQS, incluyendo las URLs de S3 generadas.
        """
        try:
            lval = await LvalConfig.load(settings.DB_AWS_TIPOLVAL, db_name=database)

            aws_access_key_id = lval.get(settings.DB_AWS_KEY)
            aws_secret_access_key = lval.get(settings.DB_AWS_SECRET)
            region_name = lval.get(settings.DB_AWS_REGION)
            queue_name = lval.get(settings.DB_AWS_QUEUE)

            if not all([aws_access_key_id, aws_secret_access_key, region_name, queue_name]):
                raise ValueError(f"Credenciales AWS SQS o nombre de cola incompletos para la base de datos '{database}'.")

            sqs = boto3.client(
                "sqs",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name
            )

            try:
                QUEUE_URL:str = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
            except ClientError as e:
                if "NonExistentQueue" in str(e):
                    raise HttpErrors.not_found(detail=f"La cola SQS '{queue_name}' no existe: {e}")
                elif "AccessDenied" in str(e):
                    raise HttpErrors.forbidden(detail=f"Permiso denegado para acceder a la cola SQS '{queue_name}': {e}")
                else:
                    raise HttpErrors.internal_server_error(detail=f"Error al obtener URL de la cola SQS: {e}")

            message_attributes = {}
            if tags:
                for name, value in tags.items():
                    message_attributes[name] = {
                        "DataType":    "String",
                        "StringValue": str(value)
                    }

            msg = {
                "from": from_addr,
                "to": to_addrs,
                "cc": cc or [],
                "bcc": bcc or [],
                "subject": subject,
                "body": body or "",
                "html_body": html_body or "",
                "attachments": attachments or [],
            }

            resp = sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(msg, ensure_ascii=False),
                MessageAttributes=message_attributes or None,
            )
            return resp
        except ClientError as e:
            raise HttpErrors.internal_server_error(detail=f"Error del cliente SQS al enviar email: {e}")
        except ValueError as e:
            raise HttpErrors.internal_server_error(detail=f"Error de configuración AWS/SQS: {e}")
        except Exception as e:
            raise HttpErrors.internal_server_error(detail=f"Error interno del servidor al enviar email: {e}")