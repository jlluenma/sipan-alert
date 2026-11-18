"""Selector reutilizable de evidencias para el formulario de reportes."""
from dataclasses import dataclass
from pathlib import Path

import streamlit as st


@dataclass(frozen=True)
class ReportAttachment:
    name: str
    media_type: str
    content: bytes


FORMATS = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".mp3": "audio/mpeg", ".wav": "audio/wav",
    ".ogg": "audio/ogg", ".m4a": "audio/mp4",
}


def report_attachments(*, key: str) -> tuple[ReportAttachment, ...] | None:
    """Devuelve adjuntos en memoria, o None si el formulario debe bloquear el envío."""
    uploads = st.file_uploader(
        "Fotos y audios del reporte", type=[ext[1:] for ext in FORMATS],
        max_upload_size=10, accept_multiple_files=True, key=key,
        help="Hasta 3 archivos de 10 MB cada uno. Adjunta solo evidencia pertinente.",
    )
    if len(uploads) > 3:
        st.error("Selecciona hasta 3 archivos.")
        return None

    attachments = []
    for upload in uploads:
        extension = Path(upload.name).suffix.lower()
        if extension not in FORMATS or not 0 < upload.size <= 10 * 1024 * 1024:
            st.error("Adjunta archivos del formato indicado, con un tamaño de hasta 10 MB.")
            return None
        attachments.append(ReportAttachment(Path(upload.name).name, FORMATS[extension], upload.getvalue()))

    for attachment in attachments:
        st.text(attachment.name)
        if attachment.media_type.startswith("image/"):
            st.image(attachment.content, width=240)
        else:
            st.audio(attachment.content, format=attachment.media_type)
    return tuple(attachments)
