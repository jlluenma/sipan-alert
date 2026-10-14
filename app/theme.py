"""Sistema visual de SipánAlert IA: tokens, CSS y componentes HTML.

Todo texto dinámico (en especial el mensaje del usuario) pasa por `html.escape`.
"""

from __future__ import annotations

import base64
from html import escape
from pathlib import Path

import streamlit as st

from sipan import guidance
from sipan.analyzer import AnalysisResult, Highlight, Signal

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..24,500,0..1,0&display=block');

:root {
  --sa-shell: 1280px;
  --sa-gutter: clamp(1.5rem, 5vw, 4.5rem);
  --sa-ink: #222B39;
  --sa-muted: #687386;
  --sa-line: #E5E7EB;
  --sa-surface: #FFFFFF;
  --sa-bg: #F4F5F7;
  --sa-teal: #E52428;
  --sa-teal-soft: #FFF0F0;
  --sa-gold: #C8922A;
  --sa-mark: #FDE2E2;
  --sa-alert: #E52428;
  --sa-alert-ink: #A81319;
  --sa-chat: #F1F2F4;
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

/* SipánAlert responsive landing page (Figma reference) */
[data-testid="stMainBlockContainer"] { max-width: none; padding: 0 0 3rem; }
[data-testid="stMainBlockContainer"]:has(.sa-footer) { padding-bottom: 0; }
[data-testid="stAppViewContainer"] { background: #fff; }
[data-testid="stHeader"] { display: none; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stMainMenu"] { display: none; }
.st-key-sa-navbar { box-sizing: border-box; height: 76px; min-height: 76px; justify-content: center; background: #fff; border-bottom: 1px solid #ECEDEF; padding: 0 64px; }
.st-key-sa-navbar [data-testid="stHorizontalBlock"] { width: 100%; max-width: none; margin: 0; align-items: center; gap: 40px; }
.st-key-sa-navbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { width: auto !important; max-width: none !important; flex: 0 0 auto !important; }
.st-key-sa-navbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child { width: 195px !important; max-width: 195px !important; flex: 0 0 195px !important; }
.st-key-sa-navbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) { margin-left: auto; }
.st-key-sa-navbar [data-testid="stPageLink"] a, .st-key-sa-navbar .stMarkdown a { color: #222B39 !important; background: transparent !important; border-radius: 4px; padding: .35rem .2rem; font-size: .88rem; text-decoration: none !important; }
.st-key-sa-navbar [data-testid="stPageLink"] a:hover, .st-key-sa-navbar .stMarkdown a:hover { color: #E52428 !important; text-decoration: underline !important; }
.st-key-sa-navbar { position: relative; }
.st-key-sa-navbar .st-key-sa-logo-click { position: absolute !important; top: 0; left: 64px; z-index: 20; width: 195px; height: 76px; pointer-events: auto; }
.st-key-sa-logo-click [data-testid="stVerticalBlock"] { position: relative; width: 100%; height: 100%; min-height: 100%; gap: 0 !important; }
.st-key-sa-logo-click [data-testid="stElementContainer"]:has([data-testid="stButton"]) { position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; }
.st-key-sa-logo-click [data-testid="stButton"], .st-key-sa-logo-click [data-testid="stButton"] button { display: block; width: 100%; height: 100%; pointer-events: auto; }
.st-key-sa-logo-click [data-testid="stButton"] button { color: transparent !important; background: transparent !important; border: 0 !important; padding: 0 !important; font-size: 0 !important; box-shadow: none !important; }
.st-key-sa-logo-click [data-testid="stButton"] button:focus-visible { outline: 2px solid #E52428; outline-offset: -3px; }
.sa-brand-link--native { pointer-events: none; }
.st-key-sa-footer-shell { position: relative; }
.st-key-sa-footer-shell .st-key-sa-footer-logo-click { position: absolute !important; top: 3.5rem; left: clamp(24px, 4vw, 64px); z-index: 20; width: 200px; height: 64px; }
.st-key-sa-footer-logo-click [data-testid="stVerticalBlock"] { position: relative; width: 100%; height: 100%; min-height: 100%; gap: 0 !important; }
.st-key-sa-footer-logo-click [data-testid="stElementContainer"]:has([data-testid="stButton"]) { position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; }
.st-key-sa-footer-logo-click [data-testid="stButton"], .st-key-sa-footer-logo-click [data-testid="stButton"] button { display: block; width: 100%; height: 100%; }
.st-key-sa-footer-logo-click [data-testid="stButton"] button { color: transparent !important; background: transparent !important; border: 0 !important; padding: 0 !important; font-size: 0 !important; box-shadow: none !important; }
.st-key-sa-footer-logo-click [data-testid="stButton"] button:focus-visible { outline: 2px solid #fff !important; outline-offset: -3px; }
.sa-footer-logo-link--native { pointer-events: none; }
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stLayoutWrapper"]:has(.st-key-sa-hero-wrap) { margin-top: -1rem; }
.st-key-sa-hero-wrap { box-sizing: border-box; background: linear-gradient(90deg, #7B1111 0%, #DC2626 55%, #8B1A1A 100%); padding: 1.25rem max(0px, calc((100vw - var(--sa-shell))/2)) 1.5rem; border-radius: 0; }
.st-key-sa-hero-wrap [data-testid="stVerticalBlock"] { gap: .45rem !important; }
.sa-hero { max-width: 1180px; margin: 0 auto; text-align: center; color: #fff; }
.sa-hero__eyebrow { margin: 0 0 .5rem; color: #fff; font-size: .77rem; font-weight: 700; letter-spacing: .12em; text-transform: uppercase; }
.sa-hero h1 { color: #fff; max-width: 620px; margin: 0 auto .45rem; font-size: clamp(2.1rem,3.5vw,2.6rem); line-height: 1.1; letter-spacing: -.035em; font-weight: 750; }
.sa-hero .sa-lead { margin: 0 auto; color: #fff; font-size: 1rem; line-height: 1.45; }
.sa-hero-form { max-width: 1020px; margin: .8rem auto 0; }
.st-key-sa-hero-form { box-sizing: border-box; width: min(100%, 1020px); margin: 0 auto; background: #fff; border: 1px solid rgba(255,255,255,.35); border-radius: 16px; padding: .85rem 1.15rem .55rem; box-shadow: 0 14px 40px rgba(71,13,16,.12); }
.st-key-sa-hero-form [data-testid="stVerticalBlock"] { gap: .5rem !important; }
.st-key-sa-hero-form [data-testid="stTextArea"] label { color: #273142; font-size: .85rem; font-weight: 650; }
.st-key-sa-hero-form [data-testid="stTextArea"] textarea { height: 94px !important; min-height: 94px; border: 1px solid #AEB5C0; border-radius: 6px; font-size: .93rem; }
.st-key-sa-hero-form [data-testid="stTextArea"] textarea:focus { border-color: var(--sa-teal); box-shadow: 0 0 0 2px rgba(229,36,40,.18); }
.st-key-sa-hero-form [data-testid="stButton"] { display: flex; justify-content: flex-end; }
.st-key-sa-hero-form [data-testid="stButton"] button[kind="primary"] { width: auto !important; min-width: 120px; min-height: 40px; border-radius: 8px; padding-inline: 1.1rem; background: #E52428; border-color: #E52428; font-weight: 650; }
.st-key-sa-hero-form [data-testid="stButton"] button[kind="primary"]:hover { background: #BD171C; border-color: #BD171C; }
.sa-form-bottom { display: flex; justify-content: space-between; align-items: center; gap: .75rem; margin-top: -.45rem; }
.sa-example-link { color: #B5161A; font-size: .84rem; font-weight: 600; text-decoration: underline; text-underline-offset: 3px; }
.sa-privacy { color: #536071; font-size: .8rem; margin: .15rem 0 .2rem; }
.st-key-sa-hero-wrap [data-testid="stAlert"] { box-sizing: border-box; display: flex; align-items: center; width: min(100%, 1020px); min-height: 2rem; margin: .2rem auto 0; padding: .2rem .7rem !important; border-radius: 8px; background: #FFF8E7 !important; color: #49370A !important; border: 1px solid #EAD9A6; border-left: 3px solid #B7791F; font-size: .84rem; line-height: 1.4; }
.st-key-sa-hero-wrap [data-testid="stAlert"] p { margin-block: 0 !important; }
.st-key-sa-hero-wrap [data-testid="stAlert"] svg { width: 1.1rem; height: 1.1rem; }
.st-key-sa-hero-wrap [data-testid="stAlert"] * { color: #222B39 !important; }
.sa-brand { display: flex; align-items: center; gap: .5rem; margin: 0; color: var(--sa-ink); font-size: 1.35rem; line-height: 1; font-weight: 750; }
.sa-brand-link { display: inline-flex; color: inherit; text-decoration: none; }
.sa-brand img { width: 43px; height: 43px; object-fit: contain; }
.sa-brand__alert { color: #E52428; }
.sa-brand sup { align-self: center; font-size: .5rem; margin: .8rem 0 0 -.35rem; letter-spacing: -.02em; }
.sa-nav { max-width: 1180px; padding: .55rem 0; margin: 0 auto; align-items: center; }
.sa-nav [data-testid="stPageLink"] a, .sa-nav .stMarkdown a { color: #202938 !important; font-size: .88rem; text-decoration: none; }
.sa-nav [data-testid="stPageLink"] a:hover, .sa-nav .stMarkdown a:hover { color: #E52428 !important; text-decoration: underline; }
.sa-nav .stButton button { background: transparent; border: 0; color: #202938; min-height: 2.6rem; padding: .25rem .4rem; }
.sa-nav .stButton button:hover { color: #E52428; background: transparent; }
.sa-home-section { box-sizing: border-box; width: min(100%, var(--sa-shell)); margin: 0 auto; padding: 3.25rem var(--sa-gutter); }
.sa-home-section--soft { max-width: var(--sa-shell); background: #FFFFFF; padding: .5rem clamp(1.15rem, 4.5vw, 4.5rem) 3.25rem; }
#ejemplo-analisis.sa-home-section { padding-bottom: 6rem; }
.sa-section-inner { max-width: 1180px; margin: 0 auto; }
.sa-kicker { color: #B5161A; font-size: .72rem; line-height: 1.3; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; text-align: center; margin: 0 0 .5rem; }
.sa-home-title { color: #222B39; text-align: center; font-size: clamp(1.8rem,3.6vw,2.55rem); line-height: 1.15; letter-spacing: -.025em; margin: 0 0 .45rem; }
.sa-home-subtitle { color: #687386; text-align: center; margin: 0 auto 1.65rem; font-size: .98rem; }
.sa-how-grid { display: grid; grid-template-columns: minmax(0,1.2fr) minmax(260px,.8fr); gap: 3rem; align-items: center; margin-top: 1.8rem; }
.sa-step-list { display: grid; gap: 1.3rem; margin: 0; padding: 0; list-style: none; }
.sa-step { display: grid; grid-template-columns: 2.2rem 1fr; column-gap: .8rem; align-items: start; color: #222B39; }
.sa-step__number { font-size: 1.1rem; font-weight: 750; }
.sa-step h3 { font-size: 1.05rem; line-height: 1.25; margin: 0 0 .25rem; }
.sa-step p { color: #687386; font-size: .9rem; line-height: 1.5; margin: 0; max-width: 32rem; }
.sa-how-image { display: block; width: min(100%,390px); height: auto; justify-self: center; }
.sa-example-panel { display: grid; grid-template-columns: minmax(0,1.8fr) minmax(0,1fr); gap: 2rem; align-items: center; width: min(100%, 850px); margin: 1.4rem auto 0; }
.sa-example-device { background: #F1F2F4; border-radius: 16px; padding: 1.5rem; }
.sa-example-device .sa-chat { margin: 0; background: transparent; padding: 0; }
.sa-example-device .sa-chat__from { display: none; }
.sa-example-device .sa-bubble { max-width: none; border-radius: 10px; font-size: 1.08rem; line-height: 1.55; padding: 1rem; box-shadow: none; }
.sa-example-label { color: #202938; font-size: .82rem; font-weight: 650; margin: 0 0 .8rem; }
.sa-example-message { background: #fff; border-radius: 10px; padding: 1rem; font-size: 1.08rem; line-height: 1.55; color: #30394A; margin: 0; }
.sa-example-message mark { color: inherit; background: transparent; border-bottom: 2px solid #E52428; padding: 0; }
.sa-example-signals { display: grid; gap: 1.3rem; }
.sa-example-signals h3 { color: #222B39; font-size: 1.05rem; margin: 0 0 .18rem; }
.sa-example-signals p { color: #687386; font-size: .88rem; margin: 0; }
.sa-protect-heading { text-align: center; margin-bottom: 2rem; }
.sa-protect-heading .sa-home-title { font-size: clamp(1.6rem, 2.4vw, 1.9rem); line-height: 1.2; margin-bottom: .45rem; }
.sa-protect-heading .sa-home-subtitle { font-size: .82rem; margin: 0 auto; }
.sa-protect-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 1.15rem; }
.sa-protect-card { box-sizing: border-box; min-height: 220px; display: flex; flex-direction: column; align-items: flex-start; padding: 1.65rem 1.7rem; border: 1px solid #E9EBEF; border-radius: 18px; background: #fff; box-shadow: none; }
.sa-protect-icon { display: grid; place-items: center; width: 48px; height: 48px; border-radius: 11px; margin: 0 0 1rem; color: #fff; background: #E52428; box-shadow: 5px -4px 0 #FDE2E2; }
.sa-protect-icon .sa-icon { font-size: 1.45rem; vertical-align: 0; font-variation-settings: 'FILL' 0; }
.sa-protect-card h3 { margin: 0 0 .4rem; font-size: 1.08rem; line-height: 1.3; color: #222B39; }
.sa-protect-card p { margin: 0; color: #536071; font-size: .78rem; line-height: 1.5; }
.sa-protect-card b { display: block; margin-top: auto; padding-top: 1.1rem; color: #E52428; font-size: .68rem; line-height: 1.3; }
.sa-cta-row { display: grid; grid-template-columns: 1fr auto; gap: 1.5rem; align-items: center; }
.sa-cta-row h2 { margin: 0 0 .35rem; font-size: clamp(1.45rem,3vw,2rem); color: #222B39; }
.sa-cta-row p { margin: 0; color: #4E596A; font-size: .93rem; }
.st-key-sa-cta { box-sizing: border-box; width: 100%; max-width: none; margin: 0; padding: 1.5rem var(--sa-gutter); background: #F4F5F7; }
.st-key-sa-cta-footer, .st-key-sa-cta-footer [data-testid="stVerticalBlock"] { gap: 0 !important; }
.st-key-sa-cta [data-testid="stHorizontalBlock"] { align-items: center; max-width: 1180px; margin: 0 auto; gap: 1rem; }
.st-key-sa-cta [data-testid="stElementContainer"]:has([data-testid="stPageLink"]) { width: 100%; align-self: stretch; }
.st-key-sa-cta [data-testid="stPageLink"] { display: flex; justify-content: flex-end; }
.st-key-sa-cta [data-testid="stPageLink"] a { box-sizing: border-box; display: inline-flex; flex: 0 0 auto; align-items: center; justify-content: center; width: auto; min-height: 2.5rem; margin-left: auto; color: #fff !important; background: #E52428; border: 1px solid #E52428; border-radius: 8px; padding: .55rem 1rem; font-size: .82rem; line-height: 1.2; font-weight: 650; text-decoration: none; }
.st-key-sa-cta [data-testid="stPageLink"] a p { margin: 0; color: #fff !important; font-size: inherit; line-height: inherit; }
.st-key-sa-cta [data-testid="stPageLink"] a:hover { background: #BD171C; border-color: #BD171C; }
.sa-footer { box-sizing: border-box; width: 100%; margin: 0; padding: 3.5rem 0 2rem; color: #fff; background: #DC2626; }
.sa-footer__content { box-sizing: border-box; width: min(calc(100% - 2 * clamp(24px, 4vw, 64px)), 1280px); margin-inline: auto; }
.sa-footer-grid { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 3rem; }
.sa-footer-logo { width: min(200px,100%); height: auto; object-fit: contain; object-position: left center; }
.sa-footer .sa-footer-logo-link { display: inline-flex; width: fit-content; margin: 0; }
.sa-footer p { color: #fff; font-size: .92rem; line-height: 1.6; }
.sa-footer h3 { color: #fff; font-size: .95rem; margin: .1rem 0 .95rem; }
.sa-footer a { display: block; color: #fff !important; text-decoration: none; font-size: .92rem; margin: 0 0 .85rem; }
.sa-footer a:hover { text-decoration: underline; }
.sa-footer-copy { border-top: 1px solid rgba(255,255,255,.3); margin: 1.15rem 0 0; padding-top: .8rem; font-size: .74rem; color: rgba(255,255,255,.92); }
.sa-page { max-width: 920px; margin: 2.2rem auto 1rem; padding: 0 1rem; }
.sa-page h1 { color: #222B39; }
.sa-signal { box-shadow: 0 8px 22px rgba(48,27,30,.045); }
.sa-verdict--alert { background: #FFF0F0; color: #A81319; }
.sa-verdict--alert .sa-icon { color: #E52428; }
.sa-verdict--alert p { color: #6F282B; }
.sa-verdict--clear { background: #F1F2F4; color: #273142; }
.sa-verdict--clear .sa-icon { color: #687386; }
.sa-signal__icon { background: #FFF0F0; color: #E52428; }
.sa-signal__do strong, .sa-signal summary, .sa-sources a, .sa-contact__value { color: #D21F24; }
.sa-checklist .sa-icon { color: #E52428; }
.sa-contact:hover { border-color: #E52428; }
.sa-contact:focus-visible, .sa-signal summary:focus-visible { outline-color: #E52428; }
.stButton button:focus-visible, a:focus-visible, [data-testid="stPageLink"] a:focus-visible, textarea:focus-visible, select:focus-visible { outline: 3px solid #111827 !important; outline-offset: 3px !important; }

/* Páginas secundarias: análisis, resultado y orientación */
.st-key-sa-page-content {
  box-sizing: border-box; width: min(100%, 1080px); max-width: 1080px;
  margin-inline: auto; padding: 2.6rem 2rem 3rem;
}
.st-key-sa-page-content .sa-page {
  max-width: none; margin: 0 0 1.2rem; padding: 0;
}
.st-key-sa-page-content .sa-page h1 {
  font-size: clamp(2rem, 4vw, 2.55rem); line-height: 1.12; letter-spacing: -.035em;
}
.st-key-sa-page-content .sa-page p { font-size: 1rem; line-height: 1.55; }
.st-key-sa-page-content [data-testid="stTextArea"] textarea {
  box-sizing: border-box; border: 1px solid #D6DAE1; border-radius: 12px;
  padding: 1rem 1.1rem; background: #fff; font-size: .98rem; line-height: 1.6;
}
.st-key-sa-page-content [data-testid="stTextArea"] textarea:focus {
  border-color: #E52428; box-shadow: 0 0 0 3px rgba(229,36,40,.12);
}
.st-key-sa-page-content [data-testid="stAlert"] {
  border-radius: 10px; border-left: 3px solid #C8922A; background: #FFF8E7;
}
.st-key-sa-page-content [data-testid="stButton"] button[kind="primary"] {
  border-radius: 8px; border-color: #E52428; background: #E52428; font-weight: 650;
}
.st-key-sa-page-content [data-testid="stButton"] button[kind="primary"]:hover {
  border-color: #BD171C; background: #BD171C;
}
.st-key-sa-page-content .sa-verdict {
  border: 1px solid rgba(229,36,40,.12); border-radius: 14px; padding: 1.25rem 1.4rem;
}
.st-key-sa-page-content .sa-chat {
  border: 1px solid #E9EBEF; border-radius: 16px; padding: 1.25rem;
}
.st-key-sa-page-content .sa-section-title {
  margin: 2rem 0 .8rem; font-size: 1.2rem; letter-spacing: -.015em;
}
.st-key-sa-page-content .sa-checklist {
  padding: .35rem 1.2rem !important; border: 1px solid #E9EBEF; border-radius: 14px; background: #F7F8FA;
}
.st-key-sa-page-content .sa-checklist li { padding: .85rem 0; }
.st-key-sa-page-content .sa-contacts { gap: 1rem; }
.st-key-sa-page-content .sa-contact {
  padding: 1.1rem 1.2rem; border-radius: 14px; box-shadow: 0 5px 18px rgba(34,43,57,.04);
}
.st-key-sa-page-content .sa-sources {
  padding: .35rem 1.2rem !important; border: 1px solid #E9EBEF; border-radius: 14px; background: #F7F8FA;
}
.st-key-sa-page-content .sa-sources li + li { border-top: 1px solid #E5E7EB; }
.st-key-sa-page-content .sa-fine { margin-top: 1.5rem; }
@media (max-width: 700px) {
  .st-key-sa-hero-wrap { padding: 1.1rem 1rem 1.25rem; }
  .sa-hero h1 { font-size: clamp(2rem,8vw,2.5rem); }
  .st-key-sa-hero-form { padding: .8rem .85rem .55rem; }
  .st-key-sa-navbar { padding-inline: 1rem; }
  .st-key-sa-navbar .st-key-sa-logo-click { left: 1rem; width: min(195px, 36vw); }
  .st-key-sa-footer-shell .st-key-sa-footer-logo-click { top: 2.25rem; left: 18px; }
  .st-key-sa-navbar [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: clamp(4px, 1vw, 10px); }
  .st-key-sa-navbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width: 0 !important; }
  .st-key-sa-navbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:first-child { width: min(195px, 36vw) !important; max-width: min(195px, 36vw) !important; flex-basis: min(195px, 36vw) !important; }
  .st-key-sa-navbar [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]:nth-child(2) { margin-left: auto; }
  .st-key-sa-navbar [data-testid="stPageLink"] a, .st-key-sa-navbar .stMarkdown a { font-size: .77rem; }
  .sa-nav [data-testid="stPageLink"] a, .sa-nav .stMarkdown a { font-size: .77rem; }
  .sa-brand { font-size: 1.05rem; gap: .3rem; }
  .sa-brand img { width: 34px; height: 34px; }
  .sa-home-section { padding: 2.6rem 1.15rem; }
  #ejemplo-analisis.sa-home-section { padding-bottom: 5rem; }
  .sa-example-panel { width: 100%; grid-template-columns: 1fr; gap: 1.4rem; }
  .sa-protect-grid { grid-template-columns: 1fr; gap: .8rem; }
  .sa-protect-card { min-height: 0; }
  .sa-protect-card b { margin-top: 1.1rem; }
  .sa-cta-row { grid-template-columns: 1fr; }
  .st-key-sa-cta { padding: 1.35rem 1.15rem; }
  .st-key-sa-cta [data-testid="stHorizontalBlock"] { flex-direction: column; gap: .75rem; }
  .st-key-sa-cta [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
  .st-key-sa-cta [data-testid="stPageLink"] { justify-content: center; }
  .st-key-sa-cta [data-testid="stPageLink"] a { margin-inline: auto; }
  .sa-footer__content { width: min(calc(100% - 36px), 1160px); }
  .sa-footer { padding: 2.25rem 0 1.25rem; }
  .sa-footer-logo { width: min(200px,100%); }
  .sa-footer-grid { grid-template-columns: 1fr 1fr; gap: 1.4rem; }
  .sa-footer-grid > :first-child { grid-column: 1 / -1; }
  .sa-steps { grid-template-columns: 1fr; }
  .st-key-sa-page-content { width: 100%; padding: 1.8rem 1.15rem 3rem; }
  .st-key-sa-page-content .sa-page { margin-bottom: .9rem; }
  .st-key-sa-page-content .sa-section-title { margin-top: 1.55rem; }
  .st-key-sa-page-content .sa-checklist { padding-inline: .9rem !important; }
}
@media (max-width: 390px) {
  .sa-brand sup { display: none; }
  .st-key-sa-navbar [data-testid="stPageLink"] a, .st-key-sa-navbar .stMarkdown a { font-size: .7rem; }
  .sa-nav [data-testid="stPageLink"] a, .sa-nav .stMarkdown a { font-size: .7rem; }
  .sa-footer-grid { grid-template-columns: 1fr; }
  .sa-footer-grid > :first-child { grid-column: auto; }
  .sa-home-section { padding-inline: 1rem; }
}
</style>
"""


def inject_css() -> None:
    st.html(CSS)


def icon(name: str) -> str:
    return f'<span class="sa-icon" aria-hidden="true">{escape(name)}</span>'


def brand(*, is_home: bool) -> str:
    icon_path = Path(__file__).resolve().parent / "assets" / "logo-icon.png"
    logo = base64.b64encode(icon_path.read_bytes()).decode("ascii")
    href = "#top" if is_home else "/"
    native_class = "" if is_home else " sa-brand-link--native"
    native_attrs = "" if is_home else ' tabindex="-1" aria-hidden="true"'
    return (f'<a class="sa-brand-link{native_class}" href="{href}" aria-label="SipánAlert IA, ir al inicio"{native_attrs}>'
            f'<div class="sa-brand"><img src="data:image/png;base64,{logo}" '
            'alt="Escudo SipánAlert IA"><span>Sipán<span class="sa-brand__alert">Alert</span></span>'
            '<sup>IA</sup></div></a>')


def navbar(home_path: str, guidance_path: str, *, is_home: bool) -> None:
    with st.container(key="sa-navbar"):
        logo_col, home_col, how_col, guide_col = st.columns([2.5, .75, 1.2, .95], vertical_alignment="center")
        with logo_col:
            st.html(brand(is_home=is_home))
        with home_col:
            st.page_link(home_path, label="Inicio")
        with how_col:
            st.markdown('[Cómo funciona](#como-funciona)', unsafe_allow_html=True)
        with guide_col:
            st.page_link(guidance_path, label="Qué hacer")
        if not is_home:
            with st.container(key="sa-logo-click"):
                st.button("SipánAlert IA, ir al inicio", key="sa-logo-home-button", on_click=st.switch_page, args=[home_path])


def landing_sections(example_message: str = "") -> str:
    illustration_path = Path(__file__).resolve().parent / "assets" / "how-it-works.png"
    illustration = base64.b64encode(illustration_path.read_bytes()).decode("ascii")
    return (
        '<section class="sa-home-section" id="como-funciona">'
        '<p class="sa-kicker">Cómo funciona</p>'
        '<h2 class="sa-home-title">Revisa una oferta en tres pasos</h2>'
        '<p class="sa-home-subtitle">Analiza el texto de una oferta de préstamo y revisa posibles señales de riesgo.</p>'
        '<div class="sa-how-grid"><ol class="sa-step-list">'
        '<li class="sa-step"><span class="sa-step__number">01</span><div><h3>Pega la oferta</h3><p>Copia el texto del préstamo que recibiste en WhatsApp, SMS, correo o redes sociales.</p></div></li>'
        '<li class="sa-step"><span class="sa-step__number">02</span><div><h3>Analiza las señales</h3><p>El sistema evalúa posibles patrones de riesgo mediante inteligencia artificial y reglas documentadas.</p></div></li>'
        '<li class="sa-step"><span class="sa-step__number">03</span><div><h3>Comprende el resultado</h3><p>Revisa las señales identificadas y recibe orientación preventiva.</p></div></li>'
        f'</ol><img class="sa-how-image" src="data:image/png;base64,{illustration}" alt="Una mano sostiene un teléfono junto a una señal amarilla de advertencia"></div></section>'
        '<section class="sa-home-section" id="ejemplo-analisis"><p class="sa-kicker">Ejemplo de análisis</p>'
        '<h2 class="sa-home-title">¿Qué señales puede ocultar una oferta?</h2>'
        '<p class="sa-home-subtitle">Observa este ejemplo ficticio y aprende a reconocer posibles riesgos.</p>'
        '<div class="sa-example-panel"><div class="sa-example-device"><p class="sa-example-label">Oferta de préstamo · Ejemplo ficticio</p>'
        f'{example_message}</div>'
        '<div class="sa-example-signals"><div><h3>Pago anticipado</h3><p>Solicitan dinero antes de entregar el préstamo.</p></div>'
        '<div><h3>Presión temporal</h3><p>Intentan que tomes una decisión inmediata.</p></div></div></div></section>'
        '<section class="sa-home-section sa-home-section--soft" id="privacidad"><div class="sa-section-inner">'
        '<div class="sa-protect-heading"><h2 class="sa-home-title">Tu información merece protección</h2><p class="sa-home-subtitle">Revisa ofertas de préstamo sin proporcionar datos personales.</p></div>'
        '<div class="sa-protect-grid"><article class="sa-protect-card"><span class="sa-protect-icon">'
        f'{icon("person_off")}</span><h3>Sin Registro</h3><p>Usa el analizador sin crear cuentas.</p><b>100% Anónimo</b></article>'
        '<article class="sa-protect-card"><span class="sa-protect-icon">'
        f'{icon("lock")}</span><h3>Sin Datos Sensibles</h3><p>No pedimos DNI ni claves bancarias.</p><b>Datos Protegidos</b></article>'
        '<article class="sa-protect-card"><span class="sa-protect-icon">'
        f'{icon("visibility_off")}</span><h3>Análisis Privado</h3><p>No guardamos tu historial.</p><b>Sin Historial</b></article></div></div></section>'
    )


def landing_footer(*, is_home: bool = False) -> str:
    logo_path = Path(__file__).resolve().parent / "assets" / "logo-white.png"
    logo = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    home_href = "#top" if is_home else "/"
    native_class = "" if is_home else " sa-footer-logo-link--native"
    native_attrs = "" if is_home else ' tabindex="-1" aria-hidden="true"'
    return (
        '<footer class="sa-footer"><div class="sa-footer__content"><div class="sa-footer-grid"><div>'
        f'<a class="sa-footer-logo-link{native_class}" href="{home_href}" aria-label="SipánAlert IA, ir al inicio"{native_attrs}><img class="sa-footer-logo" src="data:image/png;base64,{logo}" alt="SipánAlert IA"></a>'
        '<p>Plataforma de análisis preventivo de posibles señales de riesgo en ofertas de préstamos.</p></div>'
        '<div><h3>Plataforma</h3><a href="#top">Inicio</a><a href="#como-funciona">Cómo funciona</a><a href="#ejemplo-analisis">Ejemplo de análisis</a></div>'
        '<div><h3>Recursos</h3><a href="#que-hacer">Orientación preventiva</a><a href="https://www.sbs.gob.pe/">SBS</a><a href="https://www.gob.pe/mininter">Ministerio del Interior</a></div>'
        '</div><div class="sa-footer-copy">© 2026 SipánAlert IA. Todos los derechos reservados.</div></div></footer>'
    )


def render_footer(home_path: str, *, is_home: bool = False) -> None:
    with st.container(key="sa-footer-shell"):
        st.html(landing_footer(is_home=is_home))
        if not is_home:
            with st.container(key="sa-footer-logo-click"):
                st.button("SipánAlert IA, ir al inicio", key="sa-footer-home-button", on_click=st.switch_page, args=[home_path])


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
