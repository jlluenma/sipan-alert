"""Validación de entrada, anonimización y normalización de texto.

Ninguna función de este módulo registra (loguea) ni guarda el texto recibido.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from sipan import config


class InputError(ValueError):
    """Entrada no analizable. El mensaje es apto para mostrarse al usuario."""


def validate_input(text: str | None) -> str:
    """Limpia y valida el texto pegado por el usuario (US-01)."""
    if text is None:
        raise InputError("Pega el texto de la oferta para analizarlo.")
    text = unicodedata.normalize("NFC", text)
    # Quita caracteres de control invisibles, conserva saltos de línea y tabs.
    text = "".join(c for c in text if c in "\n\t" or unicodedata.category(c)[0] != "C")
    text = text.strip()
    if not text:
        raise InputError("Pega el texto de la oferta para analizarlo.")
    if len(text) < config.MIN_TEXT_LENGTH:
        raise InputError(
            f"El texto es muy corto para analizarlo (mínimo {config.MIN_TEXT_LENGTH} caracteres)."
        )
    if len(text) > config.MAX_TEXT_LENGTH:
        raise InputError(
            f"El texto supera el máximo de {config.MAX_TEXT_LENGTH} caracteres. "
            "Pega solo la parte que contiene la oferta."
        )
    if sum(c.isalpha() for c in text) < 5:
        raise InputError("El texto no contiene palabras que se puedan analizar.")
    return text


# Bordes numéricos: no partir cifras como "1.500" o "2,000", pero sí aceptar
# un número seguido de puntuación ("llama al 987654321, gracias").
_START = r"(?<!\d)(?<!\d[.,])"
_END = r"(?!\d)(?![.,]\d)"

# El orden importa: cuentas (13-20 dígitos) antes que teléfonos (9) y DNI (8).
_IDENTIFIERS = (
    ("CORREO", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("URL", re.compile(
        r"\b(?:https?://|www\.)\S+"
        r"|\b[\w-]+\.(?:com|pe|net|org|app|xyz|online|site|info|ly)(?:\.pe)?(?:/\S*)?",
        re.IGNORECASE,
    )),
    ("CUENTA", re.compile(rf"{_START}\d(?:[ -]?\d){{12,19}}{_END}")),
    ("TELEFONO", re.compile(rf"{_START}(?:\+?51[ -]?)?9\d{{2}}[ -]?\d{{3}}[ -]?\d{{3}}{_END}")),
    ("DNI", re.compile(rf"{_START}(?<!/)(?<!/ )\d{{8}}{_END}")),
)


@dataclass(frozen=True)
class Anonymized:
    text: str
    replaced: dict[str, int] = field(default_factory=dict)

    @property
    def found_identifiers(self) -> bool:
        return bool(self.replaced)


def anonymize(text: str) -> Anonymized:
    """Reemplaza teléfonos, DNI, correos, enlaces y cuentas por marcadores."""
    replaced: dict[str, int] = {}
    for tag, pattern in _IDENTIFIERS:
        text, count = pattern.subn(f"[{tag}]", text)
        if count:
            replaced[tag] = count
    return Anonymized(text, replaced)


def strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


_PLACEHOLDER = re.compile(r"\[(telefono|dni|correo|url|cuenta|nombre)\]")
_AMOUNT = re.compile(r"s/\.?\s*\d[\d.,]*")
_PERCENT = re.compile(r"\d+(?:[.,]\d+)?\s*%")
_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_NON_WORD = re.compile(r"[^a-z0-9_\s]")
_SPACES = re.compile(r"\s+")


def normalize_for_model(text: str) -> str:
    """Preprocesador del vectorizador TF-IDF.

    Anonimiza, pasa a minúsculas, quita tildes y emojis, y reemplaza montos,
    porcentajes y números por tokens para que el modelo aprenda el patrón
    ("deposita tok_monto") y no cifras concretas.
    """
    text = anonymize(text).text.lower()
    text = strip_accents(text)
    text = _PLACEHOLDER.sub(r" tok_\1 ", text)
    text = _AMOUNT.sub(" tok_monto ", text)
    text = _PERCENT.sub(" tok_porcentaje ", text)
    text = _NUMBER.sub(" tok_num ", text)
    text = _NON_WORD.sub(" ", text)
    return _SPACES.sub(" ", text).strip()
