"""Rutas y constantes compartidas por scripts, núcleo y app."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

DATASET_VERSION = "v1"
DATASET_PATH = DATA_DIR / f"dataset_{DATASET_VERSION}.csv"
MODEL_PATH = MODELS_DIR / f"model_{DATASET_VERSION}.joblib"
METRICS_PATH = REPORTS_DIR / f"metrics_{DATASET_VERSION}.json"

# Etiquetas del Anexo A (APF1). El orden importa: es el orden de columnas del modelo.
LABELS = (
    "pago_anticipado",
    "acceso_invasivo",
    "amenaza_presion",
    "condiciones_opacas",
)

# Validación de entrada (US-01)
MIN_TEXT_LENGTH = 10
MAX_TEXT_LENGTH = 3000

RANDOM_STATE = 42
