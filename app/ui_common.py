"""Utilidades compartidas por las vistas: rutas, sesión y modelo cacheado.

Privacidad: el texto y el resultado viven solo en `st.session_state` (memoria
del servidor, por pestaña) y se descartan al cerrar la sesión. Nada se escribe a disco.
"""

from __future__ import annotations

import re

import streamlit as st

from sipan.analyzer import AnalysisResult
from sipan.model import ModelUnavailable, SignalModel, load_model

PAGES = {
    "inicio": "views/inicio.py",
    "analizar": "views/analizar.py",
    "resultado": "views/resultado.py",
    "orientacion": "views/orientacion.py",
}

TEXT_KEY = "offer_text"
RESULT_KEY = "analysis"

# Ejemplos ficticios del Anexo C (APF1) para demostraciones.
EXAMPLES = {
    "Pago anticipado": "Deposita S/ 30 para liberar tu préstamo de S/ 500.",
    "Acceso invasivo": "Autoriza acceso a toda tu lista de contactos para aprobar el crédito.",
    "Amenaza o presión": "Si no pagas hoy, tus familiares sabrán de tu deuda.",
    "Cuotas sin más detalle": "Recibes S/ 900 y pagas 20 cuotas de S/ 60.",
    "Oferta con condiciones": "Oferta de S/ 2.000; tasas, cargos y calendario disponibles en contrato.",
}


_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+\-.!|<>~$])")


def escape_markdown(text: str) -> str:
    """Muestra texto del usuario literalmente (sin enlaces, imágenes ni formato)."""
    return _MARKDOWN_SPECIAL.sub(r"\\\1", text)


@st.cache_resource(show_spinner=False)
def get_model() -> SignalModel | None:
    try:
        return load_model()
    except ModelUnavailable:
        return None


def get_result() -> AnalysisResult | None:
    return st.session_state.get(RESULT_KEY)


def clear_analysis() -> None:
    st.session_state.pop(RESULT_KEY, None)
    st.session_state[TEXT_KEY] = ""
