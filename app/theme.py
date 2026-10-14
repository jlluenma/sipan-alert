"""Sistema visual de SipánAlert IA: tokens, CSS y componentes HTML.

Todo texto dinámico (en especial el mensaje del usuario) pasa por `html.escape`.
"""

from __future__ import annotations

from html import escape

import streamlit as st

from sipan import guidance
from sipan.analyzer import AnalysisResult, Highlight, Signal

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..24,500,0..1,0&display=block');

:root {
  --sa-ink: #13293D;
  --sa-muted: #536475;
  --sa-line: #DDE3E8;
  --sa-surface: #FFFFFF;
  --sa-bg: #F5F7F8;
  --sa-teal: #0B7A75;
  --sa-teal-soft: #E2F1F0;
  --sa-gold: #C8922A;
  --sa-mark: #FFE6B8;
  --sa-alert: #C2410C;
  --sa-alert-ink: #8A2E08;
  --sa-chat: #E4EBEE;
}

[data-testid="stMainBlockContainer"] { max-width: 760px; padding-top: 5.25rem; padding-bottom: 5rem; }
[data-testid="stTextArea"] textarea { background: var(--sa-surface); font-size: 1.05rem; line-height: 1.6; }
.sa-steps, .sa-trust, .sa-checklist, .sa-sources { padding-left: 0 !important; margin-left: 0 !important; }
.sa-steps li, .sa-trust li, .sa-checklist li, .sa-sources li { margin: 0 !important; }
[data-testid="stHeader"] { background: var(--sa-bg); }

.sa-icon {
  font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal;
  font-size: 1.25em; line-height: 1; vertical-align: -0.22em; display: inline-block;
  font-feature-settings: 'liga'; -webkit-font-smoothing: antialiased; user-select: none;
}

/* Marca */
.sa-brand { display: flex; align-items: center; gap: .5rem; font-weight: 700; font-size: 1.05rem; color: var(--sa-ink); margin-bottom: 1.5rem; }
.sa-brand .sa-icon { color: var(--sa-gold); font-size: 1.6rem; font-variation-settings: 'FILL' 1; }

/* Portada */
.sa-hero h1 { font-size: clamp(2.1rem, 6.5vw, 3.1rem); line-height: 1.06; letter-spacing: -0.025em; font-weight: 700; margin: 0 0 .8rem; color: var(--sa-ink); padding: 0; }
.sa-lead { font-size: 1.15rem; line-height: 1.5; color: var(--sa-muted); max-width: 32em; margin: 0; }

/* Burbuja de chat con resaltados: la pieza central del sistema */
.sa-chat { background: var(--sa-chat); border-radius: 1.5rem; padding: 1.25rem 1.25rem 1rem; margin: 1.75rem 0 1.25rem; }
.sa-chat__from { font-size: .8rem; color: var(--sa-muted); margin: 0 0 .5rem .25rem; display: flex; align-items: center; gap: .35rem; }
.sa-bubble {
  background: var(--sa-surface); border-radius: 1.1rem 1.1rem 1.1rem .3rem; padding: .95rem 1.1rem;
  max-width: 36em; font-size: 1.06rem; line-height: 1.85; color: var(--sa-ink);
  box-shadow: 0 1px 0 rgba(19, 41, 61, .10); white-space: pre-wrap; overflow-wrap: anywhere;
}
.sa-mark { background: var(--sa-mark); border-bottom: 2px solid var(--sa-alert); border-radius: .25em; padding: .08em .1em; -webkit-box-decoration-break: clone; box-decoration-break: clone; }
.sa-tag {
  display: inline-flex; align-items: center; gap: .2rem; margin: 0 .2rem; padding: .05rem .5rem .05rem .35rem;
  border-radius: 999px; background: var(--sa-alert-ink); color: #fff; font-size: .74rem; font-weight: 500;
  line-height: 1.5; white-space: nowrap; vertical-align: .12em;
}
.sa-tag .sa-icon { font-size: .95rem; vertical-align: 0; }
.sa-chat__note { font-size: .82rem; color: var(--sa-muted); margin: .7rem 0 0 .25rem; }

/* Pasos (secuencia real: numerados) */
.sa-steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 2.75rem 0 1.5rem; padding: 0; list-style: none; }
.sa-steps li { display: flex; gap: .7rem; align-items: flex-start; font-size: .98rem; line-height: 1.4; color: var(--sa-ink); }
.sa-steps b { flex: none; width: 1.8rem; height: 1.8rem; border-radius: 50%; display: grid; place-items: center; background: var(--sa-teal-soft); color: var(--sa-teal); font-size: .9rem; }
@media (max-width: 640px) { .sa-steps { grid-template-columns: 1fr; gap: .8rem; } }

.sa-trust { display: flex; flex-wrap: wrap; gap: .5rem 1.4rem; color: var(--sa-muted); font-size: .9rem; margin: 0; padding: 0; list-style: none; }
.sa-trust .sa-icon { color: var(--sa-teal); margin-right: .25rem; }
.sa-fine { color: var(--sa-muted); font-size: .82rem; line-height: 1.5; margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid var(--sa-line); }

/* Encabezados de página */
.sa-page h1 { font-size: clamp(1.8rem, 5vw, 2.4rem); letter-spacing: -0.02em; line-height: 1.1; margin: 0 0 .4rem; padding: 0; color: var(--sa-ink); }
.sa-page p { color: var(--sa-muted); font-size: 1.05rem; margin: 0; }
.sa-privacy { display: flex; gap: .5rem; align-items: flex-start; color: var(--sa-muted); font-size: .88rem; line-height: 1.45; margin: .25rem 0 .5rem; }
.sa-privacy .sa-icon { color: var(--sa-teal); }

/* Veredicto */
.sa-verdict { display: flex; gap: .9rem; align-items: flex-start; padding: 1.1rem 1.25rem; border-radius: 1rem; margin-bottom: .5rem; }
.sa-verdict .sa-icon { font-size: 1.9rem; font-variation-settings: 'FILL' 1; }
.sa-verdict h2 { font-size: 1.5rem; line-height: 1.2; margin: 0 0 .2rem; padding: 0; letter-spacing: -0.01em; }
.sa-verdict p { margin: 0; font-size: .98rem; }
.sa-verdict--alert { background: #FFF1DC; color: var(--sa-alert-ink); }
.sa-verdict--alert .sa-icon { color: var(--sa-alert); }
.sa-verdict--alert p { color: #6B3A16; }
.sa-verdict--clear { background: var(--sa-teal-soft); color: #0A4F4C; }
.sa-verdict--clear .sa-icon { color: var(--sa-teal); }
.sa-hidden-ids { font-size: .82rem; color: var(--sa-muted); margin: .4rem 0 0; display: flex; gap: .35rem; align-items: center; }

/* Señales */
.sa-section-title { font-size: 1.1rem; font-weight: 700; margin: 1.75rem 0 .75rem; color: var(--sa-ink); }
.sa-signal { background: var(--sa-surface); border: 1px solid var(--sa-line); border-radius: 1rem; padding: 1rem 1.15rem; margin-bottom: .75rem; }
.sa-signal__head { display: flex; align-items: center; gap: .65rem; }
.sa-signal__icon { flex: none; width: 2.25rem; height: 2.25rem; border-radius: .7rem; display: grid; place-items: center; background: #FFF1DC; color: var(--sa-alert); }
.sa-signal__icon .sa-icon { font-size: 1.3rem; vertical-align: 0; }
.sa-signal h3 { font-size: 1.08rem; font-weight: 700; margin: 0; padding: 0; color: var(--sa-ink); flex: 1; line-height: 1.25; }
@media (max-width: 480px) { .sa-badge { display: none; } }
.sa-badge { font-size: .74rem; color: var(--sa-muted); border: 1px solid var(--sa-line); border-radius: 999px; padding: .1rem .55rem; white-space: nowrap; }
.sa-signal__do { margin: .7rem 0 0; font-size: .98rem; line-height: 1.5; color: var(--sa-ink); }
.sa-signal__do strong { color: var(--sa-teal); font-weight: 700; }
.sa-signal details { margin-top: .6rem; font-size: .9rem; color: var(--sa-muted); }
.sa-signal summary { cursor: pointer; color: var(--sa-teal); font-weight: 500; width: fit-content; border-radius: .3rem; }
.sa-signal summary:focus-visible { outline: 2px solid var(--sa-teal); outline-offset: 2px; }
.sa-signal details[open] summary { margin-bottom: .4rem; }
.sa-signal details p, .sa-signal details ul { margin: .3rem 0; line-height: 1.5; }
.sa-signal details ul { padding-left: 1.1rem; }
.sa-signal--possible { background: transparent; border-style: dashed; }
.sa-signal--possible .sa-signal__icon { background: var(--sa-chat); color: var(--sa-muted); }

/* Orientación */
.sa-tips { margin-bottom: 1.1rem; }
.sa-tips h3 { display: flex; align-items: center; gap: .45rem; font-size: 1rem; font-weight: 700; margin: 0 0 .1rem; padding: 0; color: var(--sa-alert-ink); }
.sa-tips h3 .sa-icon { color: var(--sa-alert); }
.sa-checklist { list-style: none; padding: 0; margin: 0 0 .5rem; }
.sa-checklist li { display: flex; gap: .6rem; align-items: flex-start; padding: .6rem 0; border-bottom: 1px solid var(--sa-line); font-size: 1rem; line-height: 1.45; color: var(--sa-ink); }
.sa-checklist li:last-child { border-bottom: 0; }
.sa-checklist .sa-icon { color: var(--sa-teal); flex: none; margin-top: .1rem; }
.sa-contacts { display: grid; grid-template-columns: repeat(2, 1fr); gap: .75rem; margin-bottom: .5rem; }
@media (max-width: 640px) { .sa-contacts { grid-template-columns: 1fr; } }
.sa-contact { display: block; background: var(--sa-surface); border: 1px solid var(--sa-line); border-radius: 1rem; padding: .9rem 1.05rem; text-decoration: none !important; color: var(--sa-ink) !important; }
.sa-contact:hover { border-color: var(--sa-teal); }
.sa-contact:focus-visible { outline: 2px solid var(--sa-teal); outline-offset: 2px; }
.sa-contact__value { display: block; font-size: 1.45rem; font-weight: 700; color: var(--sa-teal); letter-spacing: -0.01em; overflow-wrap: anywhere; }
.sa-contact__name { display: block; font-weight: 500; font-size: .95rem; margin-top: .15rem; }
.sa-contact__use { display: block; font-size: .85rem; color: var(--sa-muted); margin-top: .2rem; line-height: 1.4; }
.sa-sources { list-style: none; padding: 0; margin: 0; }
.sa-sources li { padding: .45rem 0; }
.sa-sources a { color: var(--sa-teal); font-weight: 500; text-decoration: none; }
.sa-sources a:hover { text-decoration: underline; }
.sa-sources span { display: block; color: var(--sa-muted); font-size: .86rem; }

@media (prefers-reduced-motion: no-preference) {
  .sa-mark { animation: sa-mark-in .7s ease-out both; animation-delay: calc(var(--i, 0) * 220ms + 250ms); }
  @keyframes sa-mark-in { from { background-color: transparent; border-bottom-color: transparent; } }
}
</style>
"""


def inject_css() -> None:
    st.html(CSS)


def icon(name: str) -> str:
    return f'<span class="sa-icon" aria-hidden="true">{escape(name)}</span>'


def brand() -> str:
    return f'<div class="sa-brand">{icon("verified_user")}SipánAlert IA</div>'


def page_header(title: str, subtitle: str = "") -> None:
    sub = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.html(f'<header class="sa-page"><h1>{escape(title)}</h1>{sub}</header>')


def _tag(label: str) -> str:
    info = guidance.LABEL_INFO[label]
    return f'<span class="sa-tag">{icon(info.icon)}{escape(info.short)}</span>'


def highlighted_text(text: str, highlights: tuple[Highlight, ...] | list[Highlight]) -> str:
    """Devuelve el texto escapado con los fragmentos de riesgo marcados y etiquetados."""
    parts: list[str] = []
    tagged: set[str] = set()
    cursor = 0
    for i, h in enumerate(highlights):
        parts.append(escape(text[cursor:h.start]))
        parts.append(f'<mark class="sa-mark" style="--i:{i}">{escape(text[h.start:h.end])}</mark>')
        if h.label not in tagged:  # una etiqueta por señal, aunque haya varias marcas
            parts.append(_tag(h.label))
            tagged.add(h.label)
        cursor = h.end
    parts.append(escape(text[cursor:]))
    return "".join(parts)


def chat_bubble(text: str, highlights, sender: str, note: str = "") -> str:
    note_html = f'<p class="sa-chat__note">{escape(note)}</p>' if note else ""
    return (
        f'<figure class="sa-chat" aria-label="Mensaje analizado">'
        f'<figcaption class="sa-chat__from">{icon("chat")}{escape(sender)}</figcaption>'
        f'<div class="sa-bubble">{highlighted_text(text, highlights)}</div>{note_html}</figure>'
    )


def verdict(result: AnalysisResult) -> str:
    count = len(result.signals)
    if count:
        noun = "señal de alerta" if count == 1 else "señales de alerta"
        return (f'<section class="sa-verdict sa-verdict--alert" role="status">{icon("warning")}<div>'
                f'<h2>Encontramos {count} {noun}</h2>'
                f'<p>Revisa lo marcado antes de pagar o dar tus datos.</p></div></section>')
    return (f'<section class="sa-verdict sa-verdict--clear" role="status">{icon("info")}<div>'
            f'<h2>No encontramos señales de alerta</h2>'
            f'<p>Eso no garantiza que la oferta sea segura: solo revisamos el texto.</p></div></section>')


_SOURCE_TEXT = {
    "modelo y reglas": "el modelo de IA y una regla documentada",
    "modelo": "el modelo de IA",
    "reglas": "una regla documentada",
}
_BADGE = {"alta": "Confianza alta", "media": "Confianza media", "baja": "Confianza baja", "regla": "Regla"}


def signal_card(signal: Signal, possible: bool = False) -> str:
    info = guidance.LABEL_INFO[signal.label]
    details = [f"<li>Lo detectó {_SOURCE_TEXT[signal.source]} ({_BADGE[signal.confidence].lower()}).</li>"]
    if signal.model_terms:
        terms = ", ".join(f"«{escape(t)}»" for t in signal.model_terms)
        details.append(f"<li>Palabras que más influyeron: {terms}.</li>")
    if signal.probability is not None:
        details.append(f"<li>Probabilidad del modelo: {signal.probability:.0%} "
                       f"(no es la probabilidad de fraude).</li>")
    for description in signal.rule_descriptions:
        details.append(f"<li>Regla: {escape(description)}</li>")

    modifier = " sa-signal--possible" if possible else ""
    title = f"Posible: {info.short.lower()}" if possible else info.short
    return (
        f'<article class="sa-signal{modifier}">'
        f'<div class="sa-signal__head"><span class="sa-signal__icon">{icon(info.icon)}</span>'
        f'<h3>{escape(title)}</h3><span class="sa-badge">{_BADGE[signal.confidence]}</span></div>'
        f'<p class="sa-signal__do"><strong>Qué hacer:</strong> {escape(signal.recommendations[0])}</p>'
        f'<details><summary>¿Por qué lo marcamos?</summary>'
        f'<p>{escape(signal.explanation)}</p><ul>{"".join(details)}</ul></details>'
        f'</article>'
    )


def tips_by_signal(signals, per_signal: int = 2) -> str:
    groups = []
    for s in signals:
        info = guidance.LABEL_INFO[s.label]
        groups.append(
            f'<section class="sa-tips"><h3>{icon(info.icon)}{escape(info.short)}</h3>'
            f'{checklist(s.recommendations[:per_signal])}</section>'
        )
    return "".join(groups)


def checklist(items) -> str:
    rows = "".join(f"<li>{icon('check_circle')}<span>{escape(item)}</span></li>" for item in items)
    return f'<ul class="sa-checklist">{rows}</ul>'


def contact_cards() -> str:
    cards = []
    for c in guidance.CONTACTS:
        href = f"mailto:{c.value}" if "@" in c.value else f"tel:{c.value.replace('-', '')}"
        cards.append(
            f'<a class="sa-contact" href="{escape(href)}">'
            f'<span class="sa-contact__value">{escape(c.value)}</span>'
            f'<span class="sa-contact__name">{escape(c.name)}</span>'
            f'<span class="sa-contact__use">{escape(c.use)}</span></a>'
        )
    return f'<div class="sa-contacts">{"".join(cards)}</div>'


def source_links() -> str:
    rows = "".join(
        f'<li><a href="{escape(s.url)}" target="_blank" rel="noopener">{escape(s.name)}</a>'
        f'<span>{escape(s.description)}</span></li>'
        for s in guidance.SOURCES.values()
    )
    return f'<ul class="sa-sources">{rows}</ul>'


def section_title(text: str) -> None:
    st.html(f'<h2 class="sa-section-title">{escape(text)}</h2>')
