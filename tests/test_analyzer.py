import logging
import re

import pytest

from sipan import guidance
from sipan.analyzer import analyze
from sipan.preprocessing import InputError

from .conftest import ANNEX_C

FORBIDDEN_CLAIMS = re.compile(r"\b(es (una )?estafa|es fraude|fraude confirmado|estafa confirmada|es seguro|es segura)\b", re.I)


def _labels(result):
    return {s.label for s in result.signals}


@pytest.mark.parametrize("key, label", [
    ("pago", "pago_anticipado"),
    ("acceso", "acceso_invasivo"),
    ("amenaza", "amenaza_presion"),
])
def test_annex_c_signals(model, key, label):
    assert label in _labels(analyze(ANNEX_C[key], model=model))


def test_offer_with_conditions_has_no_signals(model):
    result = analyze(ANNEX_C["sin_senales"], model=model)
    assert not result.has_signals
    assert guidance.NO_SIGNALS_NOTICE in result.notices


def test_offer_without_amount_details_does_not_crash(model):
    result = analyze(ANNEX_C["cuotas"], model=model)
    assert result.model_available
    assert guidance.LIMITS_NOTICE in result.notices


def test_limits_notice_always_present(model):
    for text in ANNEX_C.values():
        assert analyze(text, model=model).notices[0] == guidance.LIMITS_NOTICE


def test_signal_explains_origin_and_evidence(model):
    signal = next(s for s in analyze(ANNEX_C["pago"], model=model).signals if s.label == "pago_anticipado")
    assert signal.source == "modelo y reglas"
    assert signal.evidence == (ANNEX_C["pago"],)
    assert signal.recommendations == guidance.LABEL_INFO["pago_anticipado"].recommendations


def test_works_without_model_using_rules_only():
    result = analyze(ANNEX_C["pago"], model=None, use_default_model=False)
    assert not result.model_available
    assert "pago_anticipado" in _labels(result)
    assert all(s.source == "reglas" for s in result.signals)
    assert any("no está disponible" in n for n in result.notices)


def test_invalid_input_raises():
    with pytest.raises(InputError):
        analyze("   ", use_default_model=False)


def test_identifiers_are_hidden_from_evidence(model):
    result = analyze("Deposita S/ 30 al 987654321 para liberar tu préstamo.", model=model)
    assert result.identifiers_hidden == {"TELEFONO": 1}
    phrases = " ".join(p for s in result.signals for p in s.evidence)
    assert "987654321" not in phrases and "[TELEFONO]" in phrases


@pytest.mark.parametrize("text", [
    "préstamo préstamo préstamo préstamo préstamo préstamo",
    "t3 prest@mos s/500 ¡¡al toq!! 🔥🔥 deposita ya q no ay tiempo",
    "Visita http://préstamos-fácil.xyz/?ref=<script>alert(1)</script> ahora",
    "x" * 2980 + " préstamo",
])
def test_robust_to_unusual_input(model, text):
    analyze(text, model=model)


def test_user_facing_text_never_claims_certainty(model):
    texts = []
    for sample in ANNEX_C.values():
        result = analyze(sample, model=model)
        texts += list(result.notices)
        for s in result.signals + result.possible_signals:
            texts += [s.title, s.explanation, *s.recommendations]
    texts += [i.title for i in guidance.LABEL_INFO.values()]
    texts += list(guidance.GENERAL_RECOMMENDATIONS)
    assert not [t for t in texts if FORBIDDEN_CLAIMS.search(t)]


def test_privacy_no_logs_and_no_files(model, caplog, tmp_path, monkeypatch):
    """US-05: el texto del usuario no aparece en logs ni se escribe en disco."""
    secret = "MensajeSecreto-XYZ-123 deposita S/ 30 para liberar tu préstamo"
    monkeypatch.chdir(tmp_path)
    caplog.set_level(logging.DEBUG)
    analyze(secret, model=model)
    assert "MensajeSecreto" not in caplog.text
    assert list(tmp_path.iterdir()) == []
