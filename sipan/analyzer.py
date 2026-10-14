"""Punto de entrada del análisis: combina modelo ML, reglas y orientación.

Privacidad: el texto vive solo en memoria durante la llamada. Este módulo no
escribe archivos ni emite logs con el contenido analizado.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sipan import config, guidance, rules
from sipan.model import ModelUnavailable, SignalModel, load_model
from sipan.preprocessing import anonymize, validate_input

# Umbrales calibrados en scripts/train.py: desde `signal_thresholds` el modelo
# reporta una señal; entre `review_thresholds` y ese valor, una "posible señal".
HIGH_CONFIDENCE_PROB = 0.8


@dataclass(frozen=True)
class Signal:
    label: str
    title: str
    explanation: str
    source: str  # "modelo", "reglas" o "modelo y reglas"
    confidence: str  # "alta", "media", "baja" o "regla"
    probability: float | None
    evidence: tuple[str, ...]  # frases del texto que activaron reglas
    rule_descriptions: tuple[str, ...]
    model_terms: tuple[str, ...]  # términos que más influyeron en el modelo
    recommendations: tuple[str, ...]


@dataclass(frozen=True)
class Highlight:
    start: int
    end: int
    label: str


@dataclass(frozen=True)
class AnalysisResult:
    signals: tuple[Signal, ...]
    possible_signals: tuple[Signal, ...]
    model_available: bool
    model_version: str | None
    identifiers_hidden: dict[str, int] = field(default_factory=dict)
    notices: tuple[str, ...] = ()
    # Texto ya anonimizado (solo en memoria) y fragmentos que activaron reglas.
    analyzed_text: str = ""
    highlights: tuple[Highlight, ...] = ()

    @property
    def has_signals(self) -> bool:
        return bool(self.signals)


def _build_signal(label: str, probability: float | None, matches: list[rules.RuleMatch],
                  terms: list[str], from_model: bool, possible: bool = False) -> Signal:
    info = guidance.LABEL_INFO[label]
    if from_model and matches:
        source = "modelo y reglas"
    elif from_model:
        source = "modelo"
    else:
        source = "reglas"
    if possible:
        confidence = "baja"
    elif from_model and probability is not None:
        confidence = "alta" if probability >= HIGH_CONFIDENCE_PROB else "media"
    else:
        confidence = "regla"
    return Signal(
        label=label,
        title=info.title,
        explanation=info.explanation,
        source=source,
        confidence=confidence,
        probability=probability,
        evidence=tuple(dict.fromkeys(m.phrase for m in matches)),
        rule_descriptions=tuple(dict.fromkeys(m.description for m in matches)),
        model_terms=tuple(terms),
        recommendations=info.recommendations,
    )


def _highlights(matches: list[rules.RuleMatch]) -> tuple[Highlight, ...]:
    """Fragmentos a resaltar, en orden y sin solaparse (gana el primero)."""
    spans = sorted((m.span[0], m.span[1], m.label) for m in matches if m.span)
    result: list[Highlight] = []
    for start, end, label in spans:
        if result and start < result[-1].end:
            continue
        result.append(Highlight(start, end, label))
    return tuple(result)


_model_cache: dict[str, SignalModel | ModelUnavailable] = {}


def get_default_model() -> SignalModel | None:
    """Carga el modelo una vez por proceso; devuelve None si no está disponible."""
    if "default" not in _model_cache:
        try:
            _model_cache["default"] = load_model()
        except ModelUnavailable as exc:
            _model_cache["default"] = exc
    cached = _model_cache["default"]
    return cached if isinstance(cached, SignalModel) else None


def analyze(text: str | None, model: SignalModel | None = None,
            use_default_model: bool = True) -> AnalysisResult:
    """Analiza el texto de una oferta. Lanza InputError si la entrada no es válida."""
    clean = validate_input(text)
    anon = anonymize(clean)
    if model is None and use_default_model:
        model = get_default_model()

    all_matches = rules.match_rules(anon.text)
    matches_by_label: dict[str, list[rules.RuleMatch]] = {label: [] for label in config.LABELS}
    for match in all_matches:
        matches_by_label[match.label].append(match)

    probabilities = model.predict_proba(anon.text) if model else {}

    signals: list[Signal] = []
    possible: list[Signal] = []
    for label in config.LABELS:
        matches = matches_by_label[label]
        prob = probabilities.get(label)
        model_hit = model_possible = False
        if model is not None and prob is not None:
            model_hit = prob >= model.signal_thresholds[label]
            model_possible = not model_hit and prob >= model.review_thresholds[label]
        terms = model.top_terms(anon.text, label) if model_hit or model_possible else []

        if model_hit or matches:
            signals.append(_build_signal(label, prob, matches, terms, from_model=model_hit))
        elif model_possible:
            possible.append(_build_signal(label, prob, [], terms, from_model=True, possible=True))

    notices = [guidance.LIMITS_NOTICE]
    if not signals:
        notices.append(guidance.NO_SIGNALS_NOTICE)
    if model is None:
        notices.append(guidance.MODEL_UNAVAILABLE_NOTICE)
    else:
        notices.append(guidance.SYNTHETIC_MODEL_NOTICE)

    return AnalysisResult(
        signals=tuple(signals),
        possible_signals=tuple(possible),
        model_available=model is not None,
        model_version=model.version if model else None,
        identifiers_hidden=dict(anon.replaced),
        notices=tuple(notices),
        analyzed_text=anon.text,
        highlights=_highlights(all_matches),
    )
