"""Respuestas de preguntas frecuentes con la orientación del proyecto."""
import re

from sipan.guidance import LABEL_INFO, LIMITS_NOTICE, SOURCES
from sipan.preprocessing import strip_accents


TOPICS = (
    ("¿Qué hago si me piden pagar por adelantado?", r"deposit|adelant|yape|comisi|transfer|pagu|liberar", "pago_anticipado", "sbs_aplicativos"),
    ("¿Qué hago si piden acceso a mis contactos?", r"contactos|permiso|acceso|contrasena|datos personales", "acceso_invasivo", "sbs_aplicativos"),
    ("¿Qué hago si me amenazan?", r"amenaz|extors|presion|gota a gota|denunc", "amenaza_presion", "mininter_gota"),
    ("¿Qué reviso antes de aceptar un préstamo?", r"acept|cuota|tasa|contrato|costo|condicion", "condiciones_opacas", "sbs_finanzas"),
)


def answer(question: str) -> str:
    normalized = strip_accents(question.casefold())
    if re.search(r"segur|legitim|confiable|senales|resultado", normalized) and not any(
        re.search(pattern, normalized) for _, pattern, _, _ in TOPICS
    ):
        return LIMITS_NOTICE
    responses = []
    for _, pattern, label, source_key in TOPICS:
        if re.search(pattern, normalized):
            info = LABEL_INFO[label]
            source = SOURCES[source_key]
            actions = "\n".join(f"- {action}" for action in info.recommendations)
            responses.append(f"**{info.title}**\n\n{actions}\n\n[{source.name}]({source.url})")
    return "\n\n".join(responses) or (
        "Puedo responder preguntas sobre pagos anticipados, acceso a contactos, "
        "amenazas y condiciones del préstamo. Elige una pregunta frecuente o reformula tu consulta."
    )

FOLLOW_UPS = {
    "pago_anticipado": (("Si todavía no pagué", (0, 1)), ("Si ya hice el pago", (2,))),
    "acceso_invasivo": (("Qué permisos evitar", (0,)), ("Qué datos proteger", (2,))),
    "amenaza_presion": (("Qué hacer si me amenazan", (1, 2)), ("Qué hacer si me presionan", (0,))),
    "condiciones_opacas": (("Qué condiciones pedir", (0,)), ("Qué revisar antes de firmar", (1, 2))),
}


def matching_topic(question: str):
    normalized = strip_accents(question.casefold())
    return next((topic for topic in TOPICS if re.search(topic[1], normalized)), None)
