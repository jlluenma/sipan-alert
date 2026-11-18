"""Investigación pública basada en comunicados y publicaciones moderadas."""

from functools import lru_cache
import json

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from sipan.config import DATA_DIR
from sipan.official_alerts import normalize
from sipan.persistence.database import DatabaseNotConfigured, session_scope

IDENTIFIERS = ("package", "domain")


@lru_cache(maxsize=1)
def catalog_entries():
    entries = {}
    publisher_evidence = json.loads((DATA_DIR / "publisher_evidence.json").read_text(encoding="utf-8"))
    for filename in ("sbs_alerts.json", "sbs_alerts_2026_07.json"):
        catalog = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
        for item in catalog["entities"]:
            identifiers = {key: item[key] for key in IDENTIFIERS if item.get(key)}
            key = (normalize(item["name"]), tuple(identifiers.items()))
            entry = entries.setdefault(key, {
                "name": item["name"],
                "kind": item.get("kind", "aplicación" if item.get("package") else "sitio web"),
                "aliases": [],
                "identifiers": identifiers,
                "alerts": [],
                "publisherEvidence": publisher_evidence.get(identifiers.get("package") or identifiers.get("domain"), []),
            })
            entry["aliases"] = list(dict.fromkeys([*entry["aliases"], *item.get("aliases", [])]))
            entry["alerts"].append({
                "title": catalog["title"], "url": catalog["source"], "date": catalog["published_at"],
                "reviewedAt": catalog.get("reviewed_at"),
                "recommendation": catalog.get("app_recommendation") if item.get("package") else None,
                "context": (
                    catalog.get("company_context") if item.get("kind") == "empresa"
                    else catalog.get("evidence_context") if item.get("package")
                    else "La SBS incluye este nombre y su dirección web en el listado del comunicado."
                ),
                "record": {"name": item["name"], "aliases": item.get("aliases", []), "identifiers": identifiers},
            })
    return list(entries.values())


def _recent_publications():
    try:
        with session_scope() as session:
            posts = session.execute(text("""
                SELECT content, created_at FROM community_posts
                WHERE status='publicado' ORDER BY created_at DESC LIMIT 100
            """)).mappings().all()
    except (DatabaseNotConfigured, SQLAlchemyError):
        return None
    return posts


def _community_mentions(posts, names):
    if posts is None:
        return None
    return [
        {"date": post["created_at"].isoformat(), "excerpt": post["content"][:220]}
        for post in posts
        if any(f" {name} " in f" {normalize(post['content'])} " for name in names)
    ][:5]


def investigate_entity(query):
    search = normalize(query)
    if len(search) < 3:
        return []
    entries = catalog_entries()
    posts = _recent_publications()
    results = []
    for entry in entries:
        names = [normalize(value) for value in [entry["name"], *entry["aliases"]]]
        identifier_match = any(search == normalize(value) for value in entry["identifiers"].values())
        name_match = any(f" {search} " in f" {name} " for name in names)
        if not identifier_match and not name_match:
            continue
        results.append({
            **entry,
            "match": "identificador" if identifier_match else "nombre",
            "relations": [
                {"name": other["name"], "kind": key, "value": value,
                 "sources": other["alerts"], "originSources": entry["alerts"]}
                for other in entries if other is not entry
                for key, value in entry["identifiers"].items()
                if other["identifiers"].get(key) == value
            ],
            "community": _community_mentions(posts, names),
        })
    return results
