"""Auditoria empirica T-3.6: verifica que los endpoints no filtran texto crudo.

- `/api/analyze` no persiste y no loggea el texto del usuario.
- `sipan.gemini_faq.generate_answer` anonimiza antes del POST a Gemini.
- `sipan.web_verification.search_official_sources` anonimiza antes del POST a Gemini.
"""
from __future__ import annotations

import json
import logging
from types import SimpleNamespace

import pytest

from api import main as api_main
from sipan import gemini_faq, web_verification


SECRET_PHONE = "987654321"
SECRET_MARKER = "MensajeSecreto"
SAMPLE_OFFER = (
    f"{SECRET_MARKER}: Deposita S/ 30 para liberar tu prestamo de S/ 500. "
    f"Escribe al {SECRET_PHONE} y envia tu DNI 12345678."
)


class _FakeResponse:
    """Minimo stand-in de la respuesta de urlopen para Gemini."""

    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


class _CapturingUrlopen:
    """Intercepta urlopen y guarda el payload del Request sin ejecutar red."""

    def __init__(self, response_payload: dict):
        self._response_payload = response_payload
        self.last_request = None

    def __call__(self, request, timeout=None):  # noqa: ARG002 - mimic urlopen signature
        self.last_request = request
        return _FakeResponse(self._response_payload)


def test_analyze_endpoint_does_not_persist_or_log_raw_text(monkeypatch, caplog):
    """`POST /api/analyze` no persiste y no deja rastro del texto crudo."""

    # Evita la lectura de DB para la similitud (la ruta captura DatabaseNotConfigured,
    # pero preferimos no depender del estado del servicio Postgres en tests).
    monkeypatch.setattr(
        api_main.LearningService,
        "list_reports",
        lambda self, status=None: [],
    )

    # Hook sobre ReportService.submit: si se llamara, el test debe fallar.
    submit_calls = []

    def _fail_if_called(*args, **kwargs):
        submit_calls.append((args, kwargs))
        raise AssertionError("/api/analyze no debe invocar ReportService.submit.")

    monkeypatch.setattr(api_main.ReportService, "submit", _fail_if_called)

    caplog.set_level(logging.DEBUG)

    payload = api_main.AnalysisInput(text=SAMPLE_OFFER)
    stub_user = {"id": "00000000-0000-0000-0000-000000000000", "roles": ["usuario"]}

    response = api_main.analyze_offer(payload, stub_user)

    # Invariantes de analyzedText: anonimizado antes de cualquier uso corriente
    # (similitud, persistencia si se reportara, panel revisor). El numero crudo
    # y el DNI no deben aparecer alli.
    assert SECRET_PHONE not in response["analyzedText"]
    assert "12345678" not in response["analyzedText"]
    assert "[TELEFONO]" in response["analyzedText"]
    assert "[DNI]" in response["analyzedText"]
    # El texto no identificable (marcador) se conserva: no es PII.
    assert SECRET_MARKER in response["analyzedText"]

    # Las frases de evidencia de las senales se construyen sobre el texto
    # anonimizado, no sobre el crudo.
    for signal in [*response["signals"], *response["possibleSignals"]]:
        for phrase in signal["evidence"]:
            assert SECRET_PHONE not in phrase
            assert "12345678" not in phrase

    # Nota empirica del audit (seccion 5.1 de AUDITORIA_PRIVACIDAD_T36):
    # `verification.checks[].value` devuelve al usuario sus propios
    # identificadores crudos (telefono/RUC/URL) para que los contraste contra
    # el canal oficial. Eso es eco al mismo autor del request, no persistencia
    # ni filtracion a terceros, y es por diseno.
    verif_values = {check["value"] for check in response["verification"]["checks"]}
    assert SECRET_PHONE in verif_values  # eco intencional al usuario
    # Lo que si debe cumplirse: la seccion verification no filtra el marcador
    # textual (no identificador) ni el DNI como numero libre fuera de su tipo.
    assert all(SECRET_MARKER not in str(v) for v in verif_values)

    # Logs: ningun registro debe contener el texto crudo con PII.
    assert SECRET_PHONE not in caplog.text
    assert "12345678" not in caplog.text
    assert SECRET_MARKER not in caplog.text

    # Nadie debe haber intentado submit() (no hay persistencia en /analyze).
    assert submit_calls == []


def test_gemini_faq_sends_only_anonymized_text(monkeypatch):
    """`generate_answer` anonimiza la pregunta antes del POST a Gemini."""
    capturing = _CapturingUrlopen(
        {"candidates": [{"content": {"parts": [{"text": json.dumps({"message": "ok", "choices": []})}]}}]}
    )
    monkeypatch.setattr(gemini_faq, "urlopen", capturing)

    question = f"Mi DNI {SECRET_PHONE[:8]} es 12345678 y mi telefono {SECRET_PHONE}."
    gemini_faq.generate_answer(question, api_key="fake-key")

    assert capturing.last_request is not None
    body = capturing.last_request.data.decode("utf-8")
    sent = json.loads(body)
    parts = sent["contents"][0]["parts"][0]["text"]

    # El numero crudo no debe viajar.
    assert SECRET_PHONE not in parts
    assert "12345678" not in parts
    # Los marcadores de anonimizacion si deben aparecer.
    assert "[TELEFONO]" in parts or "[DNI]" in parts


def test_web_verification_sends_only_anonymized_query(monkeypatch):
    """`search_official_sources` anonimiza la query antes del POST a Gemini."""
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    capturing = _CapturingUrlopen({
        "candidates": [{
            "content": {"parts": [{"text": "resumen"}]},
            "groundingMetadata": {
                "groundingChunks": [{"web": {"uri": "https://sbs.gob.pe/x", "title": "SBS"}}],
                "groundingSupports": [{"groundingChunkIndices": [0]}],
            },
        }]
    })
    monkeypatch.setattr(web_verification, "urlopen", capturing)

    query = f"Prestamo con contacto {SECRET_PHONE} - deposita S/ 30 ahora"
    web_verification.search_official_sources(query)

    assert capturing.last_request is not None
    sent = json.loads(capturing.last_request.data.decode("utf-8"))
    prompt = sent["contents"][0]["parts"][0]["text"]

    assert SECRET_PHONE not in prompt
    assert "[TELEFONO]" in prompt
