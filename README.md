# SipánAlert IA

Prototipo web basado en Machine Learning que identifica **señales de riesgo** en textos de ofertas de préstamo (pago anticipado, acceso invasivo a datos, amenaza/presión, condiciones opacas) y brinda orientación preventiva con fuentes oficiales (SBS, MININTER).

> SipánAlert IA **no** determina que una oferta sea fraude ni certifica que un prestamista sea legítimo. Sus resultados son orientativos.

Proyecto del curso Innovación y Transformación Digital — UTP Chiclayo, 2026.

## Requisitos

- Python 3.12 (también funciona con 3.11+)
- Git

## Instalación

```bash
py -3.12 -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Estructura

```
sipan/      Núcleo: preprocesamiento, reglas, modelo, analizador, orientación
app/        Interfaz Streamlit (Inicio, Analizar, Resultado, Orientación)
data/       Guía de etiquetado y dataset versionado (sintético en S1)
scripts/    Generación de datos sintéticos y entrenamiento
models/     Modelo entrenado (generado, no versionado)
reports/    Métricas de evaluación (generado, no versionado)
tests/      Pruebas automáticas (pytest)
```

## Uso

```bash
pytest                          # pruebas
```

_(Los comandos de generación de datos, entrenamiento y ejecución de la app se documentan a medida que se implementan en el Sprint 1.)_

## Privacidad

- No se requiere cuenta, DNI ni acceso a contactos.
- El texto analizado se procesa en memoria y **no se guarda**.
- La telemetría de Streamlit está desactivada (`.streamlit/config.toml`).
