"""Agrupación explicable de aportes parecidos para revisión humana."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sipan import config
from sipan.preprocessing import normalize_for_model


def compare_reviewed_reports(message: str, reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Compara con aportes revisados y devuelve únicamente datos agregados."""
    candidates = [
        report for report in reports
        if report.get("status") == "validado" and report.get("content")
        and report.get("source") == config.VOLUNTARY_SOURCE
        and not report.get("duplicate_of")
    ]
    vectorizer = TfidfVectorizer(
        preprocessor=normalize_for_model,
        ngram_range=(1, 2),
    )
    if not candidates or not normalize_for_model(message):
        return {"count": 0, "labels": []}
    corpus = [normalize_for_model(report["content"]) for report in candidates]
    if not any(len(word) >= 2 for document in corpus for word in document.split()):
        return {"count": 0, "labels": []}
    matrix = vectorizer.fit_transform([report["content"] for report in candidates])
    scores = cosine_similarity(vectorizer.transform([message]), matrix)[0]
    matches = [report for report, score in zip(candidates, scores) if score >= 0.48]
    if len(matches) < 3:
        return {"count": 0, "labels": []}
    frequencies = Counter(
        label for report in matches
        for label, value in (report.get("labels") or {}).items()
        if label in config.LABELS and value == 1
    )
    return {"count": len(matches), "labels": [
        label for label, count in frequencies.most_common() if count >= 2
    ]}


def find_patterns(reports: list[dict[str, Any]], similarity_threshold: float = 0.35) -> list[dict[str, Any]]:
    """Devuelve grupos candidatos. La similitud indica cercanía textual, no confirmación."""
    usable = [report for report in reports if report.get("content") and not report.get("duplicate_of")]
    if len(usable) < 2:
        return []
    vectorizer = TfidfVectorizer(preprocessor=normalize_for_model, ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform([report["content"] for report in usable])
    similar = cosine_similarity(matrix)
    graph: dict[int, set[int]] = defaultdict(set)
    for first in range(len(usable)):
        for second in range(first + 1, len(usable)):
            if similar[first, second] >= similarity_threshold:
                graph[first].add(second)
                graph[second].add(first)

    groups: list[dict[str, Any]] = []
    visited: set[int] = set()
    names = vectorizer.get_feature_names_out()
    for seed in graph:
        if seed in visited:
            continue
        stack, component = [seed], set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            stack.extend(graph[node] - component)
        visited.update(component)
        members = sorted(component)
        pair_scores = [similar[a, b] for pos, a in enumerate(members) for b in members[pos + 1:]]
        centroid = np.asarray(matrix[members].mean(axis=0)).ravel()
        terms = [names[index] for index in centroid.argsort()[::-1] if centroid[index] > 0][:5]
        ids = [usable[index]["id"] for index in members]
        groups.append({
            "id": "PAT-" + hashlib.sha256("|".join(ids).encode()).hexdigest()[:8].upper(),
            "report_ids": ids,
            "count": len(ids),
            "similarity": round(float(np.mean(pair_scores)), 3),
            "common_terms": terms,
            "statuses": sorted({usable[index]["status"] for index in members}),
        })
    return sorted(groups, key=lambda group: (-group["count"], -group["similarity"]))
