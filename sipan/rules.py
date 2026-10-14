"""Reglas documentadas: baseline de comparación del modelo y fuente de explicaciones.

Cada regla es una expresión regular con una descripción en lenguaje sencillo.
Las reglas trabajan sobre el texto original (anonimizado) para poder citar la
frase exacta que las activó.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from sipan import config

_VOWELS = {"a": "[aá]", "e": "[eé]", "i": "[ií]", "o": "[oó]", "u": "[uúü]"}


def _flex(pattern: str) -> re.Pattern[str]:
    """Compila un patrón escrito sin tildes para que también acepte vocales con tilde."""
    out, in_class, escaped = [], False, False
    for ch in pattern:
        if escaped:
            out.append(ch)
            escaped = False
        elif ch == "\\":
            out.append(ch)
            escaped = True
        elif ch == "[":
            in_class = True
            out.append(ch)
        elif ch == "]":
            in_class = False
            out.append(ch)
        elif not in_class and ch in _VOWELS:
            out.append(_VOWELS[ch])
        else:
            out.append(ch)
    return re.compile("".join(out), re.IGNORECASE)


@dataclass(frozen=True)
class Rule:
    id: str
    label: str
    description: str
    pattern: re.Pattern[str]
    check_negation: bool = True


@dataclass(frozen=True)
class RuleMatch:
    rule_id: str
    label: str
    description: str
    phrase: str


_PAY_VERB = r"(deposit\w*|yape\w*|plin\w*|transfier\w*|transfer\w*|abon\w*|envi\w*|pag\w*|adelant\w*|cancel\w*)"
_PAY_REASON = (
    r"(antes|previo|liberar|activar|activacion|reservar|desembolso|desembolsar|tramite|"
    r"comision|garantia|seguro|verificacion|evaluacion|apertura|notaria|gastos)"
)
_DATA = r"(contactos|agenda|galeria|fotos|sms|mensajes|whatsapp|redes sociales|ubicacion|almacenamiento|camara)"
_OFFER = re.compile(
    r"\b(pr[eé]stamos?|cr[eé]ditos?|te prestamos|te damos|dinero disponible|efectivo)\b", re.IGNORECASE
)
_COLLECTION = _flex(r"\b(vence\w*|vencid\w*|atraso|mora|deuda|saldo pendiente|recordatorio|recordamos|cobranza)\b")
_ECONOMIC_INFO = _flex(
    r"\b(tasa|tcea|tea|interes(es)? (mensual|anual)|\d+ cuotas|cuotas? (de|mensuales|fijas|diarias)|"
    r"plazo|cronograma|hoja resumen|contrato|costo total|monto total|calendario)\b"
)
_NEGATION = _flex(r"\b(no|nunca|jamas|ningun\w*|ni)\b")

RULES: tuple[Rule, ...] = (
    # --- pago_anticipado ---
    Rule("PA1", "pago_anticipado", "Pide un pago, depósito o transferencia ligado al desembolso.",
         _flex(rf"\b{_PAY_VERB}\b[^.!?\n]{{0,60}}?\b{_PAY_REASON}\b")),
    Rule("PA2", "pago_anticipado", "Menciona un pago previo o por adelantado.",
         _flex(r"\b(antes del? (desembolso|desembolsar|recibir)|pago previo|abono previo|por adelantado|adelanto de)\b")),
    Rule("PA3", "pago_anticipado", "Condiciona la entrega del dinero a 'liberar' o 'activar' el préstamo.",
         _flex(r"\bpara (liberar|activar) (tu|el|su) (prestamo|credito|dinero)\b")),
    # --- acceso_invasivo ---
    Rule("AI1", "acceso_invasivo", "Pide acceso o permisos sobre datos personales del celular.",
         _flex(rf"\b(acceso|permisos?|autoriz\w*|lectura|compart\w*|envia\w*|danos)\b[^.!?\n]{{0,50}}?\b{_DATA}\b")),
    Rule("AI2", "acceso_invasivo", "Pide la lista o agenda de contactos.",
         _flex(r"\b(lista|agenda) (de contactos|telefonica)\b")),
    Rule("AI3", "acceso_invasivo", "Pide claves, contraseñas o códigos personales.",
         _flex(r"\b(comparte|compartir|envia\w*|manda\w*|danos|dame|indica\w*)\b[^.!?\n]{0,40}?\b(clave|contrase[nñ]a|pin|token|codigo de verificacion)\b")),
    Rule("AI4", "acceso_invasivo", "Pide números o referencias de familiares.",
         _flex(r"\b(numeros de \d+ familiares|referencias familiares)\b")),
    Rule("AI5", "acceso_invasivo", "Pide instalar una aplicación fuera de tiendas oficiales (APK).",
         _flex(r"\b(instala\w*|descarga\w*)\b[^.!?\n]{0,20}\bapk\b")),
    # --- amenaza_presion ---
    Rule("AP1", "amenaza_presion", "Amenaza con avisar o exponer a familiares, contactos o al trabajo.",
         _flex(r"\b(familiares|familia|contactos|trabajo)\b[^.!?\n]{0,40}?\b(sabran|tendra problemas|se enteraran)\b"
               r"|\b(avisaremos|llamaremos|informaremos)\b[^.!?\n]{0,40}?\b(contactos|familia\w*|trabajo)\b"),
         check_negation=False),
    Rule("AP2", "amenaza_presion", "Amenaza con publicar fotos o exponer en redes.",
         _flex(r"\b(publicar|exponer|enviarse|difundir)\b[^.!?\n]{0,40}?\b(fotos?|contactos|redes)\b"
               r"|\bfotos?\b[^.!?\n]{0,30}?\b(enviarse|publicar\w*|difundir\w*)\b"),
         check_negation=False),
    Rule("AP3", "amenaza_presion", "Amenaza con ir al domicilio, al negocio o con consecuencias.",
         _flex(r"\b(iremos a buscarte|mandaremos gente|sabemos donde vives|atente a las consecuencias|vamos a ir)\b"),
         check_negation=False),
    Rule("AP4", "amenaza_presion", "Usa insultos o etiquetas públicas contra el deudor.",
         _flex(r"\b(moroso|estafador|ladron)\b")),
    Rule("AP5", "amenaza_presion", "Crea urgencia artificial para decidir sin revisar.",
         _flex(r"\b(solo por hoy|ultima oportunidad|cupos? limitados?|de inmediato|sin pensarlo|pierdes? la oferta|perderas)\b"
               r"|\b(vence|expira) en \d+ (minutos|horas?)\b|\ben \d+ minutos\b|\b(acepta|decide|confirma)\w* (ya|ahora|rapido)\b")),
    Rule("AP6", "amenaza_presion", "Pide que no consultes con nadie o que no revises el contrato.",
         _flex(r"\bno (le )?(cuentes|consultes|digas)\b|\bno hay tiempo para revisar\b"),
         check_negation=False),
    # --- condiciones_opacas (explícitas) ---
    Rule("CO1", "condiciones_opacas", "Oculta o pospone las condiciones económicas.",
         _flex(r"\b(sin (contrato|papeleo|cronograma)|cero contrato|tasa es minima|interes bajito|detalles por interno|"
               r"te (explicamos|contamos) (despues|luego|al aprobar)|explicamos despues|lo conversamos luego|"
               r"se arregla en el momento|depende del cobrador|se definen despues)\b"),
         check_negation=False),
)

_RULE_IMPLICIT_OPAQUE = Rule(
    "CO2", "condiciones_opacas",
    "Ofrece dinero sin mencionar cuotas, tasa, plazo, costo total ni contrato.",
    _OFFER, check_negation=False,
)

# Un punto entre dígitos ("S/ 1.000") no termina la oración.
_SENTENCE_END = re.compile(r"[!?\n]|(?<!\d)\.|\.(?!\d)")


def _sentence_around(text: str, start: int, end: int, limit: int = 160) -> str:
    left = max((m.end() for m in _SENTENCE_END.finditer(text, 0, start)), default=0)
    right_match = _SENTENCE_END.search(text, end)
    right = right_match.end() if right_match else len(text)
    sentence = text[left:right].strip()
    return sentence if len(sentence) <= limit else sentence[: limit - 1].rstrip() + "…"


def _is_negated(text: str, start: int, max_chars: int = 40) -> bool:
    """¿Hay una negación antes de la coincidencia, dentro de la misma oración?"""
    window = text[max(0, start - max_chars):start]
    window = _SENTENCE_END.split(window)[-1]
    return bool(_NEGATION.search(window))


def match_rules(text: str) -> list[RuleMatch]:
    """Devuelve las reglas que se activan en el texto (una coincidencia por regla)."""
    matches: list[RuleMatch] = []
    for rule in RULES:
        for m in rule.pattern.finditer(text):
            if rule.check_negation and _is_negated(text, m.start()):
                continue
            matches.append(RuleMatch(rule.id, rule.label, rule.description,
                                     _sentence_around(text, m.start(), m.end())))
            break

    offer = _OFFER.search(text)
    if (offer and not _COLLECTION.search(text) and not _ECONOMIC_INFO.search(text)
            and not any(m.label == "condiciones_opacas" for m in matches)):
        rule = _RULE_IMPLICIT_OPAQUE
        matches.append(RuleMatch(rule.id, rule.label, rule.description,
                                 _sentence_around(text, offer.start(), offer.end())))
    return matches


def predict_labels(text: str) -> dict[str, int]:
    """Predicción binaria del baseline de reglas, por etiqueta."""
    found = {m.label for m in match_rules(text)}
    return {label: int(label in found) for label in config.LABELS}
