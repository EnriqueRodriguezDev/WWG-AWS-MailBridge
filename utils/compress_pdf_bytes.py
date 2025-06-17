import io
import os
import subprocess
import tempfile
from typing import List, Dict, Tuple
import pikepdf

# thresholds in bytes
THRESHOLD_SKIP = 100 * 1024  # 100 KB: skip compression
THRESHOLD_PDF = 1_000 * 1024  # 1 MB: pikepdf only


def compress_pdf_bytes(data: bytes, gs_quality: str = "ebook") -> Tuple[bytes, int]:
    """
    Compress PDF binary in-memory.
    - If <= THRESHOLD_SKIP: return original and its size.
    - If <= THRESHOLD_PDF: compress streams via pikepdf.
    - Else: run Ghostscript then pikepdf.

    Returns tuple of (final_bytes, final_size).
    """
    orig_size = len(data)

    # Skip small files
    if orig_size <= THRESHOLD_SKIP:
        return data, orig_size

    # Medium files: pikepdf only
    if orig_size <= THRESHOLD_PDF:
        buf = io.BytesIO()
        with pikepdf.Pdf.open(io.BytesIO(data)) as pdf:
            pdf.save(
                buf,
                compress_streams=True,
                recompress_flate=True,
                linearize=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate
            )
        compressed = buf.getvalue()
    else:
        # Large files: Ghostscript -> pikepdf
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(data)
            tmp.flush()
            in_path = tmp.name

        out_path = in_path + ".gs.pdf"
        gs_cmd = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS=/{gs_quality}",
            "-dNOPAUSE", "-dBATCH", "-dQUIET",
            "-dAutoRotatePages=/None",
            "-dDetectDuplicateImages=true",
            "-dDownsampleColorImages=true",
            "-dColorImageResolution=150",
            f"-sOutputFile={out_path}",
            in_path
        ]
        subprocess.check_call(gs_cmd)

        # further optimize with pikepdf
        buf = io.BytesIO()
        with pikepdf.Pdf.open(out_path) as pdf:
            pdf.save(
                buf,
                compress_streams=True,
                recompress_flate=True,
                linearize=True,
                object_stream_mode=pikepdf.ObjectStreamMode.generate
            )
        compressed = buf.getvalue()

        # cleanup temp files
        os.remove(in_path)
        os.remove(out_path)

    # Decide best
    final = compressed if len(compressed) < orig_size else data
    return final, len(final)