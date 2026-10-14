# SipánAlert IA

Prototipo web basado en Machine Learning que identifica **señales de riesgo** en textos de ofertas de préstamo y brinda orientación preventiva con fuentes oficiales (SBS, MININTER).

> SipánAlert IA **no** determina que una oferta sea fraude ni certifica que un prestamista sea legítimo. Sus resultados son orientativos.

Proyecto del curso Innovación y Transformación Digital, UTP Chiclayo, 2026. **Versión: Sprint 1 (US-01 a US-05).**

## Qué hace (Sprint 1)

| Historia | Implementación |
|---|---|
| US-01: Pegar una oferta | Vista **Analizar mensaje**: valida texto vacío, longitud (10 a 3000 caracteres) y texto sin palabras. |
| US-02: Identificar señales | Clasificador multietiqueta TF-IDF + regresión logística (One-vs-Rest) junto con reglas documentadas. Si el modelo no está disponible, avisa y usa solo reglas. |
| US-03: Entender por qué | Vista **Resultado**: muestra la señal, el origen (modelo o regla), el nivel de confianza, la frase del texto que la activó, los términos influyentes y los límites del análisis. |
| US-04: Orientación | Vista **Orientación**: recomendaciones por señal, fuentes oficiales y teléfonos (SBS 0-800-10840, MININTER 1818, PNP 105). |
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
git clone <URL-del-repositorio> sipan-alert
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
pytest                                 # 91 pruebas automáticas
python scripts/generate_synthetic.py   # regenera data/dataset_v1.csv (determinista, semilla 42)
```

El modelo no se sube a git. Reentrenar con el mismo dataset reproduce exactamente las métricas de `reports/`.

### Ejemplos ficticios para la demo (Anexo C)

La vista **Analizar mensaje** incluye estos ejemplos en «Usa un ejemplo ficticio»:

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
  streamlit_app.py         Entrada y navegación
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

## Cómo funciona el análisis

1. **Validación:** se descarta texto vacío, muy corto, muy largo o sin palabras.
2. **Anonimización:** teléfonos, DNI, correos, enlaces y cuentas pasan a `[TELEFONO]`, `[DNI]`, etc.
3. **Reglas documentadas:** expresiones regulares con manejo de negaciones («nunca te pediremos depósitos» no activa la señal). Cada regla cita la frase que la activó.
4. **Modelo ML:** probabilidad por señal.
   - ≥ 0,5: se reporta como **señal**.
   - Entre el umbral F2 calibrado (0,30 a 0,40) y 0,5: se reporta como **posible señal (confianza baja)**, para no perder casos dudosos.
5. **Resultado:** cada señal indica su origen (modelo, regla o ambos) y lleva siempre el aviso de límites. Que no haya señales no significa que la oferta sea segura.

**Evaluación sin fuga de datos:** `grupo_similitud` agrupa los mensajes por familia de redacción y cada fold de prueba usa frases que el modelo no vio al entrenar.

## Privacidad

- No se requiere cuenta, DNI ni acceso a contactos.
- El texto se procesa en memoria (`st.session_state`) y **no se guarda** en disco ni en logs. Lo verifica `tests/test_analyzer.py::test_privacy_no_logs_and_no_files`.
- La telemetría de Streamlit está desactivada (`.streamlit/config.toml`).
- El modelo se carga solo si su huella SHA-256 coincide con la registrada al entrenar. Nunca cargues archivos `.joblib` de origen desconocido.

## Fuera del Sprint 1

- **Sprint 2:** calculadora de pagos (US-06), más fuentes oficiales (US-07) y ejemplos didácticos (US-12).
- **Sprint 3:** reporte técnico de métricas en la UI (US-08) y descarga del resumen (US-09).
- **Sprint 4:** OCR de capturas (US-10) e historial con consentimiento (US-11).
