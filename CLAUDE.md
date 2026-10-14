# SipánAlert IA — guía del proyecto

Clasificador ML (TF-IDF + regresión logística One-vs-Rest) de señales de riesgo en ofertas de préstamo, con UI Streamlit. Proyecto universitario UTP 2026; documentos fuente: APF1 (requerimientos) y APF2 (backlog en 4 sprints).

## Stack
Python 3.12 · pandas · numpy · scikit-learn · joblib · Streamlit · pytest. Sin base de datos en Sprint 1 (privacidad por defecto). Solo local.

## Comandos
- Entorno: `.venv\Scripts\activate`
- Tests: `pytest`

## Convenciones
- `sipan/config.py` es la única fuente de rutas, etiquetas (`LABELS`) y límites de entrada.
- Etiquetas (Anexo A): `pago_anticipado`, `acceso_invasivo`, `amenaza_presion`, `condiciones_opacas`.
- El núcleo `sipan/` no importa Streamlit; la UI en `app/` solo llama a `sipan.analyzer`.

## Reglas no negociables
- Nunca guardar ni loguear el texto del usuario.
- Redactar salidas como "señales observadas"; nunca "estafa", "fraude" ni certezas. Ausencia de señales ≠ oferta segura.
- No inventar métricas; las de datos sintéticos se declaran como no representativas.

## Estado (Sprint 1: US-01..US-05)
- [x] Paso 1: setup (estructura, venv, dependencias, config)
- [ ] Paso 2: guía de etiquetado + dataset sintético
- [ ] Paso 3: preprocesamiento + reglas baseline
- [ ] Paso 4: entrenamiento y evaluación
- [ ] Paso 5: analizador + orientación
- [ ] Paso 6: UI Streamlit (4 vistas)
- [ ] Paso 7: tests completos
- [ ] Paso 8: README final
