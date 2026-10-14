# SipánAlert IA: guía del proyecto

Clasificador ML (TF-IDF + regresión logística One-vs-Rest) de señales de riesgo en ofertas de préstamo, combinado con reglas documentadas, con interfaz en Streamlit. Proyecto universitario UTP 2026. Documentos fuente: APF1 (requerimientos) y APF2 (backlog en 4 sprints).

## Stack
Python 3.12 · pandas · numpy · scikit-learn · joblib · Streamlit 1.65 · pytest. Versiones fijadas en `requirements.txt`. Sin base de datos (privacidad por defecto). Solo local.

## Comandos
- Entorno: `.venv\Scripts\activate`
- Dataset: `python scripts/generate_synthetic.py` (determinista, semilla 42)
- Entrenar: `python scripts/train.py` → `models/model_v1.joblib` (+ `.sha256`, no versionado) y `reports/metrics_v1.{json,md}` (versionado)
- App: `streamlit run app/streamlit_app.py`
- Tests: `pytest` (98). Los tests entrenan su propio modelo en un directorio temporal y no dependen de `models/`.

## Arquitectura
- `sipan/` es el núcleo y no importa Streamlit. La UI solo llama a `sipan.analyzer.analyze()`.
- `sipan/config.py` es la única fuente de rutas, `LABELS` y límites de entrada.
- `sipan/guidance.py` es la única fuente de los textos de cara al usuario: títulos de señales, recomendaciones, enlaces oficiales, contactos y avisos.
- Flujo de `analyze`: `validate_input` → `anonymize` → `rules.match_rules` + `model.predict_proba` → `AnalysisResult`.
- Umbrales: el modelo reporta una señal con prob ≥ 0,5 (`signal_thresholds`). Entre el umbral F2 (`review_thresholds`, calibrado fuera de fold) y 0,5 la marca como «posible señal». Las reglas siempre reportan.
- La app (`app/streamlit_app.py`) usa `st.navigation(position="hidden")` con navbar y footer propios (`theme.navbar`, `theme.render_footer`). Inicio es una landing con el formulario de análisis; «Resultado» es una página oculta a la que se llega con `st.switch_page`. Las anclas de secciones (`#como-funciona`, etc.) viven en Inicio: desde otras páginas se enlazan como `/#ancla` (`_home_anchor`). Las vistas están en `app/views/` y lo compartido en `app/ui_common.py` (agrega ROOT a `sys.path`).
- Diseño en `app/theme.py`: tokens CSS `--sa-*`, componentes HTML con `st.html` y `html.escape` en todo texto dinámico. La fuente (Google Sans) y los colores base están en `[theme]` de `.streamlit/config.toml`. La burbuja resalta `AnalysisResult.highlights` (spans de reglas sobre `analyzed_text`; CO2 no resalta). Imágenes en `app/assets/`, incrustadas en base64 con `_asset_b64` (cacheado). Las señales del ejemplo de Inicio salen del analizador, no se escriben a mano. El rediseño usa hex directos además de los tokens; al tocar estilos, preferir los tokens.
- Los tests de UI leen el HTML con `at.get("html")[i].proto.body`. Después de cambiar módulos importados, reinicia `streamlit run`: no se recargan solos.
- Evaluación: `GroupKFold` por `grupo_similitud`, que en el corpus sintético es la familia de redacción F1–F5 (fragmento i → familia i % 5).

## Convenciones
- Etiquetas (Anexo A): `pago_anticipado`, `acceso_invasivo`, `amenaza_presion`, `condiciones_opacas`.
- Las reglas se escriben sin tildes; `_flex()` las vuelve insensibles a tildes. La negación se busca en los 40 caracteres previos, dentro de la misma oración.
- El texto del usuario se muestra solo a través de `app/theme.py`, que lo escapa con `html.escape`.
- Para agregar frases al corpus, cada pool de `generate_synthetic.py` debe tener un número de frases múltiplo de 5.
- Colaboración: `main` está protegida (PR con 1 aprobación, sin force push ni borrado; el admin puede saltarla). Los colaboradores trabajan en ramas y abren PR.

## Reglas no negociables
- Nunca guardar ni loguear el texto del usuario (lo cubre `test_privacy_no_logs_and_no_files`).
- Redactar las salidas como «señales observadas»; nunca «estafa», «fraude» ni certezas. Que no haya señales no significa que la oferta sea segura (lo cubre `test_user_facing_text_never_claims_certainty`).
- No inventar métricas. Las del corpus sintético se declaran no representativas.
- `joblib.load` solo después de verificar el SHA-256 (`load_model`). Nunca cargar modelos de origen desconocido.
- Implementar solo el sprint en curso.

## Estado: Sprint 1 completo (US-01..US-05)
- Corpus v1: 600 mensajes sintéticos. ML F1 macro 0,68 frente a 0,94 de las reglas (evaluación por familias). Con este corpus el ML no supera al baseline; hace falta un corpus real revisado.
- Enlaces oficiales verificados con HTTP 200 el 2026-10-14. El sitio de la SBS usa Incapsula, así que su contenido no se puede leer automáticamente.
- Pendiente del equipo: revisión humana de una muestra del dataset (`revision` = pendiente), Planning Poker y evidencias del APF2.
- Pendiente (pospuesto, 2026-10-14): no se detectan ofertas que quitan los controles normales de un préstamo («promesa irreal / sin evaluación»).
  - «Te regalamos plata!»: ninguna regla salta (`_OFFER`/CO2 no reconoce «regalamos», «gratis») y el modelo solo da una posible señal `condiciones_opacas`. Además `theme.verdict()` ignora `possible_signals` y titula «No encontramos señales de alerta».
  - «Te prestamos hasta 1000 soles sin revisión en Infocorp, sin seguro, sin deudor, con una tasa de hasta 16% anual. Sin depósitos adelantados…»: cero señales (probabilidades 0,10–0,28, bajo los umbrales de revisión). CO2 no salta porque menciona una tasa, aunque sea irrealmente baja para un préstamo sin evaluación ni garantía.
  - Causa en el corpus: la apertura «Te prestamos S/ {monto} sin aval y sin Infocorp» de `APERTURAS` en `generate_synthetic.py` aparece en mensajes limpios y de riesgo (p. ej. SYN-0019 y SYN-0039 son `0,0,0,0`), así que el modelo aprendió que «sin Infocorp» es neutral.
  - Razonamiento: quien presta sin evaluar ni pedir garantías se asegura el cobro por otra vía (acceso a contactos, ubicación o fotos para presionar después). Indicios: «sin Infocorp / sin revisar centrales de riesgo / aprobado sin evaluación», «sin aval / garantía / seguro / requisitos», dinero regalado o gratis, tasa irrealmente baja (difícil por reglas). Las frases tranquilizadoras («sin depósitos adelantados») también pueden ser una táctica de confianza.
  - Propuesta: (1) titular ámbar cuando solo hay posibles señales; (2) reglas para esos indicios, con tests de negación; (3) sacar «sin Infocorp» de las aperturas neutras y agregar frases de este tipo al corpus, reentrenar y actualizar `reports/metrics_v1.*`; (4) recomendación del estilo «si no revisan tu historial ni piden garantías, pueden asegurarse el cobro pidiendo acceso a tus contactos o datos para presionarte después». Una 5.ª etiqueta cambia el Anexo A: decidirlo con el equipo para un sprint posterior.
- Siguiente, Sprint 2: US-06 calculadora, US-07 fuentes oficiales, US-12 ejemplos didácticos.
