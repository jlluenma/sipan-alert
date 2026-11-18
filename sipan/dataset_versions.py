"""Exportación reproducible de aportes revisados para futuros entrenamientos."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sipan import config
from sipan.novelty import find_patterns


def _partition(group: str) -> str:
    return "evaluacion" if int(hashlib.sha256(group.encode()).hexdigest(), 16) % 5 == 0 else "entrenamiento"


def create_version(reports: list[dict[str, Any]], output_dir: Path = config.DATASET_VERSIONS_DIR) -> dict[str, Any]:
    """Exporta solo aportes validados. Los duplicados y pendientes jamás se exportan."""
    eligible = [r for r in reports if r["status"] == "validado" and not r.get("duplicate_of") and r.get("content")]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    version = f"voluntario_{stamp}"
    target = output_dir / version
    target.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, Any]] = []
    group_by_report = {
        report_id: pattern["id"]
        for pattern in find_patterns(eligible)
        for report_id in pattern["report_ids"]
    }
    for report in eligible:
        group = group_by_report.get(report["id"], "G-" + hashlib.sha256(report["content"].encode()).hexdigest()[:12])
        labels = report["labels"]
        rows.append({
            "id": report["id"], "mensaje": report["content"], **{label: labels[label] for label in config.LABELS},
            "fuente": report["source"], "grupo_similitud": group, "revision": "revisada",
            "particion": _partition(group), "recibido_en": report["received_at"],
        })
    fields = ["id", "mensaje", *config.LABELS, "fuente", "grupo_similitud", "revision", "particion", "recibido_en"]
    paths: dict[str, str] = {}
    for partition in ("entrenamiento", "evaluacion"):
        path = target / f"{partition}.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(row for row in rows if row["particion"] == partition)
        paths[partition] = str(path)
    manifest = {
        "version": version,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "eligible_reports": len(rows),
        "training_reports": sum(row["particion"] == "entrenamiento" for row in rows),
        "evaluation_reports": sum(row["particion"] == "evaluacion" for row in rows),
        "source": config.VOLUNTARY_SOURCE,
        "paths": paths,
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest["manifest"] = str(manifest_path)
    return manifest
