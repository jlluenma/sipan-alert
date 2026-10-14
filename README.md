# SipánAlert IA

Prototipo web basado en Machine Learning que identifica **señales de riesgo** en textos de ofertas de préstamo y brinda orientación preventiva con fuentes oficiales (SBS, MININTER).

> SipánAlert IA **no** determina que una oferta sea fraude ni certifica que un prestamista sea legítimo. Sus resultados son orientativos.

Proyecto del curso Innovación y Transformación Digital, UTP Chiclayo, 2026. **Versión: Sprint 1 (US-01 a US-05).**

## Qué hace (Sprint 1)

| Historia | Implementación |
|---|---|
| US-01: Pegar una oferta | Formulario en **Inicio** y vista **Revisar mensaje**: valida texto vacío, longitud (10 a 3000 caracteres) y texto sin palabras. Ejemplos ficticios en un clic. |
| US-02: Identificar señales | Clasificador multietiqueta TF-IDF + regresión logística (One-vs-Rest) junto con reglas documentadas. Si el modelo no está disponible, avisa y usa solo reglas. |
| US-03: Entender por qué | Vista **Resultado**: el mensaje del usuario con las frases de riesgo **resaltadas y etiquetadas**, un veredicto en una línea y una tarjeta por señal con «Qué hacer» y «¿Por qué lo marcamos?» (origen, confianza y términos influyentes). |
| US-04: Orientación | Vista **Qué hacer**: dos acciones por señal detectada, contactos con un toque para llamar o escribir (SBS 0-800-10840, MININTER 1818, PNP 105) y fuentes oficiales. |
| US-05: Privacidad | Sin cuenta ni campos de DNI o contactos. El texto no se guarda ni se registra en logs. Teléfonos, DNI, correos, enlaces y cuentas se ocultan antes de analizar. Streamlit sin telemetría. |

**Señales (Anexo A, APF1):** `pago_anticipado`, `acceso_invasivo`, `amenaza_presion` y `condiciones_opacas`. Los criterios de cada una están en [`data/LABELING_GUIDE.md`](data/LABELING_GUIDE.md).

## Qué es real y qué es simulado

- **Dataset:** 100 % **sintético** (600 mensajes), generado por `scripts/generate_synthetic.py` a partir de frases escritas por el equipo según las advertencias de la SBS y el MININTER. No contiene mensajes reales.
- **Modelo:** entrenado y evaluado de verdad sobre ese corpus. Sus métricas **no representan** el desempeño con mensajes reales. Ver [`reports/metrics_v1.md`](reports/metrics_v1.md).
- **Resultado de la evaluación:** con validación por familias de redacción (GroupKFold), el ML obtiene un F1 macro de **0,68**, mientras que el baseline de reglas llega a **0,94**. Las reglas salen favorecidas porque se escribieron conociendo las mismas frases. Con este corpus el ML **no supera** al baseline; tal como prevé el APF1, la app combina ambos y muestra el origen de cada señal. Mejorar el modelo requiere un corpus revisado más diverso.

## Inicio rápido (Windows)

Requisitos: **Python 3.12** (también sirve 3.11+) y **Git**.

> ⚠️ Clona el proyecto en una ruta corta, por ejemplo `C:\proyectos\sipan-alert`. Si la ruta es muy larga, `pip install` falla con `WinError 206`, porque Streamlit trae archivos con rutas profundas y Windows tiene un límite de 260 caracteres.

```powershell
# 1. Clonar
cd C:\proyectos
git clone https://github.com/jlluenma/sipan-alert.git
cd sipan-alert

# 2. Crear y activar el entorno virtual
py -3.12 -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependencias (1 a 2 minutos)
pip install -r requirements.txt

# 4. Entrenar el modelo (solo la primera vez, unos 5 segundos)
python scripts/train.py

# 5. Abrir la app (se abre en http://localhost:8501)
streamlit run app/streamlit_app.py
```

Para detener la app, presiona `Ctrl + C` en la terminal. Las siguientes veces solo necesitas el paso 2 (activar) y el paso 5.

En Linux o macOS: `python3 -m venv .venv` y `source .venv/bin/activate`.

### Otros comandos

```bash
pytest                                 # 98 pruebas automáticas
python scripts/generate_synthetic.py   # regenera data/dataset_v1.csv (determinista, semilla 42)
```

El modelo no se sube a git. Reentrenar con el mismo dataset reproduce exactamente las métricas de `reports/`.

### Ejemplos ficticios para la demo (Anexo C)

La vista **Revisar mensaje** incluye estos ejemplos en «¿No tienes uno a la mano? Prueba un ejemplo»:

| Mensaje | Señal esperada |
|---|---|
| «Deposita S/ 30 para liberar tu préstamo de S/ 500». | Pago anticipado |
| «Autoriza acceso a toda tu lista de contactos para aprobar el crédito». | Acceso invasivo |
| «Si no pagas hoy, tus familiares sabrán de tu deuda». | Amenaza o presión |
| «Recibes S/ 900 y pagas 20 cuotas de S/ 60». | El cálculo del total queda para el Sprint 2 |
| «Oferta de S/ 2.000; tasas, cargos y calendario disponibles en contrato». | Sin las señales definidas |

## Estructura

```
sipan/                     Núcleo (no depende de Streamlit)
  config.py                Rutas, etiquetas y límites de entrada
  preprocessing.py         Validación, anonimización y normalización para el modelo
  rules.py                 Reglas documentadas (baseline y explicación)
  model.py                 Pipeline TF-IDF + LogReg, carga con verificación SHA-256 y términos influyentes
  analyzer.py              analyze(texto) -> AnalysisResult (ML + reglas + avisos)
  guidance.py              Textos de orientación, fuentes oficiales y contactos
app/
  streamlit_app.py         Entrada y navegación (navbar y footer propios)
  theme.py                 Sistema visual: tokens, CSS y componentes HTML (navbar, landing, burbuja con resaltados, tarjetas, footer)
  assets/                  Logo e ilustraciones
  ui_common.py             Sesión, modelo cacheado y ejemplos
  views/                   inicio · analizar · resultado · orientacion
data/
  LABELING_GUIDE.md        Manual de etiquetado (SECI: externalización)
  dataset_v1.csv           Corpus sintético versionado
scripts/
  generate_synthetic.py    Generador del corpus
  train.py                 Entrenamiento, evaluación sin fuga y reporte
reports/                   Métricas versionadas (evidencia del sprint)
tests/                     pytest: entrada, anonimización, reglas, dataset, modelo, analizador, privacidad y UI
```

## Diseño

- **Idea central:** mostrar el sistema en vez de explicarlo. Inicio es una landing con el formulario de análisis arriba y un mensaje ficticio con las frases de riesgo resaltadas por el analizador real. El resultado usa esa misma burbuja con el mensaje del usuario.
- **Tipografía:** Google Sans (Google Fonts), configurada en `.streamlit/config.toml`. Íconos: Material Symbols Rounded.
- **Color:** el rojo `#E52428` identifica la marca y las acciones principales, y se combina con grises neutros. Las señales se resaltan con un tono suave (`#FDE2E2`) y el lenguaje nunca acusa: el rojo es identidad visual, no un veredicto de «peligro».
- **Accesibilidad:** diseño adaptable al celular, foco visible, animación de resaltado solo con `prefers-reduced-motion: no-preference` y todo el texto del usuario escapado.

## Cómo funciona el análisis

1. **Validación:** se descarta texto vacío, muy corto, muy largo o sin palabras.
2. **Anonimización:** teléfonos, DNI, correos, enlaces y cuentas pasan a `[TELEFONO]`, `[DNI]`, etc.
3. **Reglas documentadas:** expresiones regulares con manejo de negaciones («nunca te pediremos depósitos» no activa la señal). Cada regla cita la frase que la activó.
4. **Modelo ML:** probabilidad por señal.
   - ≥ 0,5: se reporta como **señal**.
   - Entre el umbral F2 calibrado (0,30 a 0,40) y 0,5: se reporta como **posible señal (confianza baja)**, para no perder casos dudosos.
5. **Resultado:** cada señal indica su origen (modelo, regla o ambos) y lleva siempre el aviso de límites. Que no haya señales no significa que la oferta sea segura.

**Evaluación sin fuga de datos:** `grupo_similitud` agrupa los mensajes por familia de redacción y cada fold de prueba usa frases que el modelo no vio al entrenar.

## Ficha técnica

| Aspecto | Término técnico | En SipánAlert IA |
|---|---|---|
| Tipo de sistema | **Sistema de apoyo a la decisión** | Orienta; la decisión es del usuario. |
| Problema | **Clasificación de texto multietiqueta** (PLN), **aprendizaje supervisado** | Un mensaje puede tener varias de las 4 señales a la vez. |
| Enfoque | **Sistema híbrido**: reglas + aprendizaje automático | Reglas interpretables (expresiones regulares con manejo de negación) y un modelo estadístico; se combinan sus resultados. |
| Características | **Vectorización TF-IDF** con **n-gramas de palabras** (1–2) y **de caracteres** (3–5, `char_wb`), unidas con `FeatureUnion` | Los n-gramas de caracteres toleran errores de tipeo. |
| Clasificador | **Regresión logística One-vs-Rest** (*binary relevance*), `class_weight="balanced"` | Un clasificador binario por etiqueta, con ponderación por desbalance de clases. |
| Decisión | **Umbrales de decisión**; umbral de revisión calibrado con **F2** | Favorece el *recall*: prefiere avisar de más que dejar pasar una señal. |
| Datos | **Datos sintéticos** generados de forma **determinista** (semilla 42) | Reproducibles; la revisión humana de una muestra está pendiente. |
| Evaluación | **Validación cruzada agrupada** (`GroupKFold`) con **predicciones fuera de fold** | Evita la **fuga de datos** entre familias de redacción. Métrica principal: **F1 macro**, comparado contra las reglas como **línea base**. |
| Arquitectura | **Arquitectura en capas**, **separación de responsabilidades**, **bajo acoplamiento** | `sipan/` (dominio) no depende de `app/` (presentación); la UI solo llama a `analyze()`. |
| Configuración y textos | **Fuente única de verdad** | `sipan/config.py` (rutas, etiquetas, límites) y `sipan/guidance.py` (textos, contactos, enlaces). |
| Ciclo del modelo | **Entrenamiento offline** e **inferencia en línea**; **serialización** con `joblib` | `scripts/train.py` entrena una vez; `analyze()` predice en cada consulta. |
| Estado | **Aplicación sin estado** (*stateless*), **monolito local** | Sin base de datos; un solo proceso Streamlit. |
| Seguridad | **Verificación de integridad** (SHA-256) contra **deserialización insegura**; **escape de HTML** contra **XSS** | El modelo solo se carga si su hash coincide; todo texto dinámico pasa por `html.escape`. |
| Privacidad | **Privacidad desde el diseño**, **minimización de datos**, **anonimización de PII** | Se ocultan teléfonos, DNI, correos, enlaces y cuentas antes de analizar. |
| Calidad | **Pruebas automatizadas** unitarias, de interfaz (`AppTest`) y de **regresión** | `pytest`; incluye pruebas de privacidad y de lenguaje sin certezas. |
| Proceso | **Scrum/Scrumban**, **historias de usuario**; **GitHub Flow** | Sprints del APF2; ramas por cambio, *pull request* con revisión y `main` protegida. |

## Limitaciones conocidas

- **Corpus sintético:** las métricas no representan el desempeño con mensajes reales, y el ML (F1 macro 0,68) no supera a las reglas (0,94).
- **Sesgo del corpus:** la apertura «sin aval y sin Infocorp» aparece en mensajes limpios y de riesgo, así que el modelo aprendió que es neutral (una **correlación espuria**).
- **Ofertas que quitan los controles normales de un préstamo** («te regalamos plata», «sin revisión en Infocorp, sin garantías», tasas irrealmente bajas) hoy no se detectan.
- **Titular del resultado:** si solo hay «posibles señales», el titular dice «No encontramos señales de alerta».

Estas limitaciones están documentadas con su diagnóstico y una propuesta de corrección para un sprint posterior.

## Cómo colaborar

`main` está protegida: los cambios entran por *pull request* con una aprobación.

```bash
git checkout main
git pull
git checkout -b nombre-de-la-rama
# ...cambios y commits...
pytest
git push -u origin nombre-de-la-rama
```

Después abre un PR hacia `main` en GitHub. Cuando se mergea, la rama se borra sola del remoto; para limpiar la copia local: `git fetch --prune` y `git branch -d nombre-de-la-rama`.

## Privacidad

- No se requiere cuenta, DNI ni acceso a contactos.
- El texto se procesa en memoria (`st.session_state`) y **no se guarda** en disco ni en logs. Lo verifica `tests/test_analyzer.py::test_privacy_no_logs_and_no_files`.
- La telemetría de Streamlit está desactivada (`.streamlit/config.toml`).
- El modelo se carga solo si su huella SHA-256 coincide con la registrada al entrenar. Nunca cargues archivos `.joblib` de origen desconocido.

## Fuera del Sprint 1

- **Sprint 2:** calculadora de pagos (US-06), más fuentes oficiales (US-07) y ejemplos didácticos (US-12).
- **Sprint 3:** reporte técnico de métricas en la UI (US-08) y descarga del resumen (US-09).
- **Sprint 4:** OCR de capturas (US-10) e historial con consentimiento (US-11).
