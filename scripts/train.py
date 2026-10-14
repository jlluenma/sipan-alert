"""Entrena y evalúa el clasificador de señales; compara contra el baseline de reglas.

Evaluación: GroupKFold por `grupo_similitud` (cada fold deja fuera una familia de
redacción completa), así ninguna variante casi idéntica cruza de train a test.
Por etiqueta se calibran dos umbrales sobre las predicciones fuera de fold:
- "review": maximiza F2 (prioriza recall; un falso negativo da falsa seguridad).
  Entre este umbral y el de señal, la UI muestra una "posible señal".
- "signal": fijo en 0.5 (límite de decisión de la regresión logística). Con
  corpus sintético las probabilidades no están bien calibradas para redacciones
  nuevas; recalibrar este umbral cuando exista un corpus real revisado.
El modelo final se reentrena con todo el dataset.

Uso: python scripts/train.py [--dataset data/dataset_v1.csv]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import confusion_matrix, fbeta_score, precision_recall_fscore_support
from sklearn.model_selection import GroupKFold

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sipan import config, rules  # noqa: E402
from sipan.model import build_pipeline, hash_path_for, sha256_of  # noqa: E402

THRESHOLD_GRID = np.round(np.arange(0.20, 0.71, 0.05), 2)
SIGNAL_THRESHOLD = 0.5
SYNTHETIC_NOTE = (
    "Métricas calculadas sobre un corpus 100% sintético redactado por el equipo. "
    "Las reglas baseline se escribieron conociendo esas mismas frases, por lo que la "
    "comparación las favorece. Estos valores NO representan el desempeño con mensajes "
    "reales y no deben presentarse como precisión del sistema."
)


def load_dataset(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8")
    missing = {"mensaje", "grupo_similitud", "revision", *config.LABELS} - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en el dataset: {sorted(missing)}")
    return df[df["revision"] != "descartada"].reset_index(drop=True)


def _binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=0
    )
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "precision": round(float(precision), 3),
        "recall": round(float(recall), 3),
        "f1": round(float(f1), 3),
        "support": int(y_true.sum()),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def choose_review_threshold(y_true: np.ndarray, proba: np.ndarray) -> float:
    scores = [fbeta_score(y_true, proba >= t, beta=2, zero_division=0) for t in THRESHOLD_GRID]
    best = max(scores)
    # En empate, el umbral más alto (menos falsos positivos con igual F2).
    return float(max(t for t, s in zip(THRESHOLD_GRID, scores) if s == best))


def evaluate(df: pd.DataFrame) -> tuple[dict, dict[str, float]]:
    texts = df["mensaje"].to_numpy()
    y = df[list(config.LABELS)].to_numpy()
    groups = df["grupo_similitud"].to_numpy()
    n_splits = min(5, len(np.unique(groups)))
    if n_splits < 2:
        raise ValueError("Se necesitan al menos 2 grupos de similitud para evaluar sin fuga.")

    oof = np.zeros(y.shape, dtype=float)
    fold_f1: list[float] = []
    for train_idx, test_idx in GroupKFold(n_splits=n_splits).split(texts, y, groups):
        pipe = build_pipeline().fit(texts[train_idx], y[train_idx])
        oof[test_idx] = pipe.predict_proba(texts[test_idx])
        fold_pred = (oof[test_idx] >= 0.5).astype(int)
        fold_f1.append(float(np.mean([
            fbeta_score(y[test_idx, j], fold_pred[:, j], beta=1, zero_division=0)
            for j in range(len(config.LABELS))
        ])))

    rule_pred = np.array([[rules.predict_labels(t)[l] for l in config.LABELS] for t in texts])
    thresholds: dict[str, dict[str, float]] = {"review": {}, "signal": {}}
    per_label: dict[str, dict] = {}
    for j, label in enumerate(config.LABELS):
        review = choose_review_threshold(y[:, j], oof[:, j])
        signal = max(SIGNAL_THRESHOLD, review)
        thresholds["review"][label] = review
        thresholds["signal"][label] = signal
        per_label[label] = {
            "threshold_review": review,
            "threshold_signal": signal,
            "ml_at_0.5": _binary_metrics(y[:, j], (oof[:, j] >= 0.5).astype(int)),
            "ml_at_review": _binary_metrics(y[:, j], (oof[:, j] >= review).astype(int)),
            "ml_at_signal": _binary_metrics(y[:, j], (oof[:, j] >= signal).astype(int)),
            "rules": _binary_metrics(y[:, j], rule_pred[:, j]),
        }

    ml_signal_pred = np.column_stack(
        [oof[:, j] >= thresholds["signal"][l] for j, l in enumerate(config.LABELS)]
    )
    macro = lambda key: round(float(np.mean([per_label[l][key]["f1"] for l in config.LABELS])), 3)  # noqa: E731
    metrics = {
        "evaluation": f"GroupKFold({n_splits}) por grupo_similitud; predicciones fuera de fold",
        "per_label": per_label,
        "macro_f1": {key: macro(key) for key in ("ml_at_0.5", "ml_at_review", "ml_at_signal", "rules")},
        "ml_macro_f1_per_fold_at_0.5": {
            "values": [round(v, 3) for v in fold_f1],
            "mean": round(float(np.mean(fold_f1)), 3),
            "std": round(float(np.std(fold_f1)), 3),
        },
        "any_signal": {
            "ml_at_signal": _binary_metrics(y.any(axis=1).astype(int), ml_signal_pred.any(axis=1).astype(int)),
            "rules": _binary_metrics(y.any(axis=1).astype(int), rule_pred.any(axis=1).astype(int)),
        },
        "threshold_note": "Umbrales elegidos sobre las mismas predicciones fuera de fold: "
                          "las métricas 'ml_at_review' y 'ml_at_signal' pueden ser algo optimistas.",
    }
    return metrics, thresholds


def write_markdown_report(metrics: dict, path: Path) -> None:
    lines = [
        f"# Reporte de evaluación — modelo {metrics['model_version']}",
        "",
        f"> **Aviso:** {SYNTHETIC_NOTE}",
        "",
        f"- Dataset: `{metrics['dataset']['path']}` ({metrics['dataset']['n_samples']} mensajes, "
        f"fuentes: {metrics['dataset']['sources']})",
        f"- SHA-256 del dataset: `{metrics['dataset']['sha256']}`",
        f"- Entrenado: {metrics['trained_at']} · scikit-learn {metrics['sklearn_version']}",
        f"- Evaluación: {metrics['evaluation']}",
        "",
        "## Métricas por etiqueta",
        "",
        "ML «señal» = umbral 0.5 (señal reportada); ML «revisar» = umbral F2 (posibles señales).",
        "",
        "| Etiqueta | Umbral señal / revisar | ML señal P · R · F1 | ML revisar P · R · F1 | Reglas P · R · F1 |",
        "|---|---|---|---|---|",
    ]
    fmt = lambda m: f"{m['precision']:.2f} · {m['recall']:.2f} · {m['f1']:.2f}"  # noqa: E731
    for label, m in metrics["per_label"].items():
        lines.append(f"| {label} | {m['threshold_signal']:.2f} / {m['threshold_review']:.2f} | "
                     f"{fmt(m['ml_at_signal'])} | {fmt(m['ml_at_review'])} | {fmt(m['rules'])} |")
    folds = metrics["ml_macro_f1_per_fold_at_0.5"]
    macro = metrics["macro_f1"]
    lines += [
        "",
        f"- F1 macro — ML señal: **{macro['ml_at_signal']}** · ML revisar: {macro['ml_at_review']} · "
        f"ML 0.5: {macro['ml_at_0.5']} · Reglas: **{macro['rules']}**",
        f"- F1 macro ML por familia (0.5): {folds['values']} → media {folds['mean']} ± {folds['std']}",
        f"- {metrics['threshold_note']}",
        "",
        "## Matrices de confusión (ML, umbral de señal)",
        "",
        "| Etiqueta | VN | FP | FN | VP |",
        "|---|---|---|---|---|",
    ]
    for label, m in metrics["per_label"].items():
        c = m["ml_at_signal"]["confusion"]
        lines.append(f"| {label} | {c['tn']} | {c['fp']} | {c['fn']} | {c['tp']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", type=Path, default=config.DATASET_PATH)
    parser.add_argument("--model-out", type=Path, default=config.MODEL_PATH)
    parser.add_argument("--metrics-out", type=Path, default=config.METRICS_PATH)
    args = parser.parse_args()

    df = load_dataset(args.dataset)
    metrics, thresholds = evaluate(df)

    pipeline = build_pipeline().fit(df["mensaje"].to_numpy(), df[list(config.LABELS)].to_numpy())
    trained_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    dataset_sha = sha256_of(args.dataset)

    args.model_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({
        "pipeline": pipeline,
        "labels": list(config.LABELS),
        "thresholds": thresholds,
        "version": config.DATASET_VERSION,
        "trained_at": trained_at,
        "dataset_sha256": dataset_sha,
        "sklearn_version": sklearn.__version__,
    }, args.model_out)
    hash_path_for(args.model_out).write_text(sha256_of(args.model_out) + "\n", encoding="utf-8")

    try:
        dataset_label = args.dataset.resolve().relative_to(config.ROOT).as_posix()
    except ValueError:
        dataset_label = args.dataset.name
    metrics = {
        "model_version": config.DATASET_VERSION,
        "trained_at": trained_at,
        "sklearn_version": sklearn.__version__,
        "note": SYNTHETIC_NOTE,
        "dataset": {
            "path": dataset_label,
            "sha256": dataset_sha,
            "n_samples": len(df),
            "sources": df["fuente"].value_counts().to_dict() if "fuente" in df else {},
            "positives": {l: int(df[l].sum()) for l in config.LABELS},
        },
        **metrics,
    }
    args.metrics_out.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(metrics, args.metrics_out.with_suffix(".md"))

    print(f"Modelo -> {args.model_out}")
    print(f"Métricas -> {args.metrics_out} (+ .md)")
    print(f"F1 macro  ML(señal)={metrics['macro_f1']['ml_at_signal']}  Reglas={metrics['macro_f1']['rules']}")
    print(f"Umbrales: {thresholds}")


if __name__ == "__main__":
    main()
