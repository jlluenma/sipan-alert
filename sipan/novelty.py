"""Agrupación explicable de aportes parecidos para revisión humana."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sipan.preprocessing import normalize_for_model


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
