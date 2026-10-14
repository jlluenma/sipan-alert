import json

import pytest

from sipan import config
from sipan.model import ModelUnavailable, hash_path_for, load_model

from .conftest import ANNEX_C


def test_probabilities_cover_all_labels(model):
    probs = model.predict_proba(ANNEX_C["pago"])
    assert set(probs) == set(config.LABELS)
    assert all(0.0 <= p <= 1.0 for p in probs.values())


@pytest.mark.parametrize("key, label", [
    ("pago", "pago_anticipado"),
    ("acceso", "acceso_invasivo"),
    ("amenaza", "amenaza_presion"),
])
def test_annex_c_signal_is_detected(model, key, label):
    assert model.predict_proba(ANNEX_C[key])[label] >= model.signal_thresholds[label]


def test_top_terms_explain_with_words_from_text(model):
    terms = model.top_terms(ANNEX_C["acceso"], "acceso_invasivo")
    assert terms
    assert any("contactos" in t or "acceso" in t for t in terms)
    assert all(t not in {"el", "la", "tu", "para", "de"} for t in terms)


def test_thresholds_are_ordered(model):
    for label in config.LABELS:
        assert 0 < model.review_thresholds[label] <= model.signal_thresholds[label] < 1


def test_metrics_report_compares_with_rules(trained_artifacts):
    metrics = json.loads(trained_artifacts["metrics"].read_text(encoding="utf-8"))
    assert "NO representan" in metrics["note"]
    assert metrics["evaluation"].startswith("GroupKFold")
    for label in config.LABELS:
        entry = metrics["per_label"][label]
        assert {"ml_at_signal", "ml_at_review", "rules"} <= set(entry)
    assert trained_artifacts["metrics"].with_suffix(".md").exists()


def test_missing_model_raises(tmp_path):
    with pytest.raises(ModelUnavailable):
        load_model(tmp_path / "no_existe.joblib")


def test_tampered_model_is_rejected(trained_artifacts, tmp_path):
    copy = tmp_path / "model.joblib"
    copy.write_bytes(trained_artifacts["model"].read_bytes() + b"x")
    hash_path_for(copy).write_text(hash_path_for(trained_artifacts["model"]).read_text())
    with pytest.raises(ModelUnavailable, match="huella"):
        load_model(copy)
