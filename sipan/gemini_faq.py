"""Generación de respuestas del asistente mediante Gemini."""
import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from dataclasses import dataclass

from sipan.guidance import CONTACTS, LABEL_INFO, LIMITS_NOTICE, SOURCES
from sipan.preprocessing import anonymize


@dataclass(frozen=True)
class GuidedReply:
    message: str
    choices: tuple[str, ...]


MODEL = "gemini-2.5-flash-lite"
INSTRUCTIONS = "\n".join([
    "Eres el asistente de SIPAN Alert. Responde en español, con pasos concretos y breves.",
    "Limítate a prevención y orientación sobre ofertas de préstamos en Perú. "
    "Usa solo los datos del catálogo. Si falta información, dilo. "
    "No certifiques empresas, no inventes enlaces ni solicites datos personales.",
    "Guía el caso paso a paso. Si un dato cambia la orientación, haz una sola pregunta concreta "
    "y ofrece de dos a tres respuestas seleccionables en primera persona. "
    "Si ya hay información suficiente, da el siguiente paso y deja la lista de opciones vacía. "
    "Mantén las opciones breves y coherentes con tu pregunta.",
    LIMITS_NOTICE,
    *(f"{info.title}. {info.explanation} {' '.join(info.recommendations)}" for info in LABEL_INFO.values()),
    *(f"{contact.name}: {contact.value}. {contact.use}" for contact in CONTACTS),
    *(f"{source.name}: {source.url}. {source.description}" for source in SOURCES.values()),
])


def generate_answer(question: str, api_key: str) -> GuidedReply | None:
    """Devuelve la respuesta de Gemini o None si el servicio no está disponible."""
    payload = {
        "systemInstruction": {"parts": [{"text": INSTRUCTIONS}]},
        "contents": [{"role": "user", "parts": [{"text": anonymize(question).text}]}],
        "generationConfig": {"maxOutputTokens": 650,
            "thinkingConfig": {"thinkingBudget": 0},
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "message": {"type": "STRING"},
                    "choices": {"type": "ARRAY", "items": {"type": "STRING"}, "maxItems": 3},
                },
                "required": ["message", "choices"],
            },},
    }
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
    )
    try:
        with urlopen(request, timeout=12) as response:
            result = json.load(response)
        parts = result["candidates"][0]["content"]["parts"]
        reply = json.loads("".join(part.get("text", "") for part in parts if not part.get("thought")))
        message, choices = reply["message"], reply["choices"]
        if not isinstance(message, str) or not message.strip() or not isinstance(choices, list):
            return None
        options = dict.fromkeys(choice.strip() for choice in choices
                                if isinstance(choice, str) and 0 < len(choice.strip()) <= 90)
        return GuidedReply(message.strip(), tuple(options)[:3])
    except (URLError, TimeoutError, ValueError, KeyError, IndexError, TypeError):
        return None
