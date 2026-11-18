from __future__ import annotations

import json

import pandas as pd
import pytest

from sipan import config
from sipan.dataset_versions import create_version
from sipan.novelty import find_patterns
from sipan.reports_store import delete_report, list_reports, review_report, submit_report


def test_voluntary_report_requires_review_before_dataset_export(tmp_path):
    database = tmp_path / "reports.sqlite3"
    report_id, deletion_code, duplicate = submit_report(
        "Una voz dice que es mi familiar y pide transferir dinero urgente.", {}, "v1", path=database,
    )
    assert duplicate is None
    report = list_reports(path=database)[0]
    assert report["status"] == "pendiente"

    review_report(report_id, "validado", {label: 0 for label in config.LABELS}, "Caso nuevo", path=database)
    version = create_version(list_reports(path=database), tmp_path / "versions")
    training = pd.read_csv(version["paths"]["entrenamiento"])
    evaluation = pd.read_csv(version["paths"]["evaluacion"])
    assert len(training) + len(evaluation) == 1
    assert json.loads((tmp_path / "versions" / version["version"] / "manifest.json").read_text())["eligible_reports"] == 1
    assert delete_report(report_id, deletion_code, path=database)
    assert list_reports(path=database) == []


def test_duplicate_is_detected_and_not_exported(tmp_path):
    database = tmp_path / "reports.sqlite3"
    first, _, _ = submit_report("Deposita para liberar el préstamo", {}, "v1", path=database)
    second, _, duplicate = submit_report("Deposita para liberar el préstamo", {}, "v1", path=database)
    assert duplicate == first
    labels = {label: 0 for label in config.LABELS}
    review_report(first, "validado", labels, "Revisado", path=database)
    review_report(second, "validado", labels, "Revisado", path=database)
    version = create_version(list_reports(path=database), tmp_path / "versions")
    rows = pd.concat([pd.read_csv(version["paths"]["entrenamiento"]), pd.read_csv(version["paths"]["evaluacion"])])
    assert list(rows["id"]) == [first]


def test_similar_reports_form_a_candidate_group():
    reports = [
        {"id": "REP-A", "content": "Una voz de mi familiar pide una transferencia urgente", "status": "pendiente"},
        {"id": "REP-B", "content": "Mi familiar llama con una voz y solicita transferir dinero urgente", "status": "pendiente"},
    ]
    patterns = find_patterns(reports, similarity_threshold=0.1)
    assert len(patterns) == 1
    assert patterns[0]["report_ids"] == ["REP-A", "REP-B"]


def test_training_rejects_pending_voluntary_rows(tmp_path):
    from scripts.train import load_dataset

    dataset = tmp_path / "pending.csv"
    pd.DataFrame([{
        "mensaje": "Mensaje para revisión", "grupo_similitud": "G1", "revision": "pendiente",
        "fuente": config.VOLUNTARY_SOURCE, **{label: 0 for label in config.LABELS},
    }]).to_csv(dataset, index=False)
    with pytest.raises(ValueError, match="pendientes"):
        load_dataset(dataset)
