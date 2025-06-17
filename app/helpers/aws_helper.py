import io
import json
import os
from typing import List, Dict, Any, Optional
import boto3
import oracledb
from fastapi import Form
from pydantic import EmailStr, HttpUrl

from app.core.config import settings
from services.lval_service import LvalService, LvalConfig
from utils.compress_pdf_bytes import compress_pdf_bytes

class AwsHelper:

    @staticmethod
    async def upload_blobs_to_s3(
        files: List[Dict[str, bytes]],
        bucket: str,
        prefix: str,
    ) -> List[Dict[str, Any]]:
        """
        Process list of dicts with keys:
          - 'filename': str
          - 'blob': bytes

        Compress PDFs, upload each to S3 in-memory,
        and return metadata list:
          [{ 'filename': str, 'url': str, 'size': int }, ...]
        """
        lval = await LvalConfig.load(settings.DB_AWS_TIPOLVAL)

        s3 = boto3.client(
            "s3",
            aws_access_key_id=lval.get(settings.DB_AWS_KEY),
            aws_secret_access_key=lval.get(settings.DB_AWS_SECRET),
            region_name=lval.get(settings.DB_AWS_REGION)
        )

        results: List[Dict[str, Any]] = []
        for item in files:
            filename = item.get("filename")
            blob = item.get("blob")
            if not filename or blob is None:
                continue

            ext = os.path.splitext(filename)[1].lower()
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

    @staticmethod
    async def send_email(from_addr: EmailStr,
                         to_addrs: List[EmailStr],
                         cc: List[EmailStr],
                         bcc: List[EmailStr],
                         subject: str,
                         body: Optional[str]      = None,
                         html_body: Optional[str] = Form,
                         attachments: List[str]  = None,
                         ) -> Dict[str, Any]:
        """
        Encola un mensaje para envío vía SES, incluyendo las URLs de S3 generadas.
        """

        lval = await LvalConfig.load(settings.DB_AWS_TIPOLVAL)

        QUEUE_NAME: str = lval.get(settings.DB_AWS_QUEUE)

        # Cliente SQS
        sqs = boto3.client(
            "sqs",
            aws_access_key_id=lval.get(settings.DB_AWS_KEY),
            aws_secret_access_key=lval.get(settings.DB_AWS_SECRET),
            region_name=lval.get(settings.DB_AWS_REGION)
        )

        # Obtener la URL de la cola
        QUEUE_URL:str = sqs.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]

        msg = {
            "from": from_addr,
            "to": to_addrs,
            "cc": cc or [],
            "bcc": bcc or [],
            "subject": subject,
            "body": body or "",
            "html_body": html_body or "",
            "attachments": attachments or []
        }
        resp = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(msg, ensure_ascii=False)
        )
        return resp

