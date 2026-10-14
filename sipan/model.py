"""Pipeline TF-IDF + regresión logística (One-vs-Rest) y carga segura del modelo."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import FeatureUnion, Pipeline

from sipan import config
from sipan.preprocessing import normalize_for_model


class ModelUnavailable(RuntimeError):
    """No hay modelo entrenado válido (falta el archivo o no coincide su hash)."""


def build_pipeline() -> Pipeline:
    """TF-IDF de palabras (explicable) + n-gramas de caracteres (tolera errores de tipeo)."""
    return Pipeline([
        ("features", FeatureUnion([
            ("word", TfidfVectorizer(
                preprocessor=normalize_for_model, ngram_range=(1, 2), min_df=2, sublinear_tf=True,
            )),
            ("char", TfidfVectorizer(
                preprocessor=normalize_for_model, analyzer="char_wb", ngram_range=(3, 5),
                min_df=2, sublinear_tf=True,
            )),
        ])),
        ("clf", OneVsRestClassifier(LogisticRegression(
            class_weight="balanced", C=1.0, max_iter=2000, random_state=config.RANDOM_STATE,
        ))),
    ])


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_path_for(model_path: Path) -> Path:
    return model_path.with_suffix(".sha256")


_TOKEN_LABELS = {
    "tok_monto": "S/ (monto)",
    "tok_porcentaje": "(porcentaje)",
    "tok_num": "(número)",
    "tok_telefono": "(teléfono)",
    "tok_cuenta": "(cuenta)",
    "tok_url": "(enlace)",
    "tok_correo": "(correo)",
    "tok_dni": "(DNI)",
}


# Solo para mostrar explicaciones: el modelo sí usa estas palabras (p. ej. "no").
_DISPLAY_STOPWORDS = frozenset(
    "a al el la los las lo le les un una unos unas de del y o u e en con por para que q x "
    "se su sus tu tus te mi mis me es son si no ya muy mas hay este esta esto ese esa".split()
)


def _readable(term: str) -> str:
    return " ".join(_TOKEN_LABELS.get(word, word) for word in term.split())


def _is_informative(term: str) -> bool:
    return any(w not in _DISPLAY_STOPWORDS and w not in _TOKEN_LABELS for w in term.split())


@dataclass
class SignalModel:
    pipeline: Pipeline
    labels: tuple[str, ...]
    signal_thresholds: dict[str, float]
    review_thresholds: dict[str, float]
    version: str
    trained_at: str
    dataset_sha256: str

    def predict_proba(self, text: str) -> dict[str, float]:
        probs = self.pipeline.predict_proba([text])[0]
        return {label: float(p) for label, p in zip(self.labels, probs)}

    def top_terms(self, text: str, label: str, k: int = 5) -> list[str]:
        """Términos (palabras o bigramas) del texto que más empujan la predicción de `label`."""
        features = self.pipeline.named_steps["features"]
        word_vec: TfidfVectorizer = features.transformer_list[0][1]
        estimator = self.pipeline.named_steps["clf"].estimators_[self.labels.index(label)]
        if not hasattr(estimator, "coef_"):  # etiqueta constante en entrenamiento
            return []

        n_word = len(word_vec.vocabulary_)
        row = features.transform([text]).tocsr()[0, :n_word]
        coef = estimator.coef_[0, :n_word]
        contributions = row.multiply(coef).toarray()[0]
        names = word_vec.get_feature_names_out()
        terms: list[str] = []
        for i in np.argsort(contributions)[::-1]:
            if contributions[i] <= 0 or len(terms) == k:
                break
            if _is_informative(names[i]):
                terms.append(_readable(names[i]))
        return terms


def load_model(path: Path = config.MODEL_PATH) -> SignalModel:
    """Carga el modelo solo si su SHA-256 coincide con el registrado al entrenar.

    joblib usa pickle: nunca cargar archivos de origen desconocido.
    """
    hash_file = hash_path_for(path)
    if not path.exists() or not hash_file.exists():
        raise ModelUnavailable("No se encontró un modelo entrenado. Ejecuta scripts/train.py.")
    expected = hash_file.read_text(encoding="utf-8").strip()
    if sha256_of(path) != expected:
        raise ModelUnavailable("El archivo del modelo no coincide con su huella registrada.")

    artifact = joblib.load(path)
    return SignalModel(
        pipeline=artifact["pipeline"],
        labels=tuple(artifact["labels"]),
        signal_thresholds=dict(artifact["thresholds"]["signal"]),
        review_thresholds=dict(artifact["thresholds"]["review"]),
        version=artifact["version"],
        trained_at=artifact["trained_at"],
        dataset_sha256=artifact["dataset_sha256"],
    )
