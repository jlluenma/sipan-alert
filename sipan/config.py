"""Rutas y constantes compartidas por scripts, núcleo y app."""

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"
PRIVATE_DATA_DIR = DATA_DIR / "private"
CONTINUAL_DB_PATH = PRIVATE_DATA_DIR / "continual_learning.sqlite3"
DATASET_VERSIONS_DIR = PRIVATE_DATA_DIR / "dataset_versions"

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

# Un aporte voluntario solo llega a un dataset cuando un revisor lo valida.
VOLUNTARY_SOURCE = "voluntario_anonimizado"
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_MIGRATION_URL = os.getenv("DATABASE_MIGRATION_URL", DATABASE_URL)
