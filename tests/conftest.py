"""Fixtures compartidas: entrena un modelo en un directorio temporal.

Los tests no dependen de models/ (no versionado): generan su propio dataset
sintético y modelo, así son reproducibles en cualquier máquina.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from sipan import config
from sipan.model import load_model

ROOT = Path(__file__).resolve().parent.parent

# Ejemplos ficticios del Anexo C (APF1).
ANNEX_C = {
    "pago": "Deposita S/ 30 para liberar tu préstamo de S/ 500.",
    "acceso": "Autoriza acceso a toda tu lista de contactos para aprobar el crédito.",
    "amenaza": "Si no pagas hoy, tus familiares sabrán de tu deuda.",
    "cuotas": "Recibes S/ 900 y pagas 20 cuotas de S/ 60.",
    "sin_senales": "Oferta de S/ 2.000; tasas, cargos y calendario disponibles en contrato.",
}


@pytest.fixture(scope="session")
def trained_artifacts(tmp_path_factory):
    out = tmp_path_factory.mktemp("artifacts")
    dataset = out / "dataset.csv"
    model_path = out / "model.joblib"
    metrics_path = out / "metrics.json"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_synthetic.py"),
                    "--out", str(dataset)], check=True, capture_output=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "train.py"), "--dataset", str(dataset),
                    "--model-out", str(model_path), "--metrics-out", str(metrics_path)],
                   check=True, capture_output=True)
    return {"dataset": dataset, "model": model_path, "metrics": metrics_path}


@pytest.fixture(scope="session")
def model(trained_artifacts):
    return load_model(trained_artifacts["model"])


@pytest.fixture
def labels():
    return config.LABELS
