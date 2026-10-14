# Reporte de evaluación — modelo v1

> **Aviso:** Métricas calculadas sobre un corpus 100% sintético redactado por el equipo. Las reglas baseline se escribieron conociendo esas mismas frases, por lo que la comparación las favorece. Estos valores NO representan el desempeño con mensajes reales y no deben presentarse como precisión del sistema.

- Dataset: `data/dataset_v1.csv` (600 mensajes, fuentes: {'sintetico': 600})
- SHA-256 del dataset: `77be02a74dddef957491c18cbba201b776e46a5492babc92828684363f276130`
- Entrenado: 2026-10-14T07:54:54+00:00 · scikit-learn 1.9.1
- Evaluación: GroupKFold(5) por grupo_similitud; predicciones fuera de fold

## Métricas por etiqueta

ML «señal» = umbral 0.5 (señal reportada); ML «revisar» = umbral F2 (posibles señales).

| Etiqueta | Umbral señal / revisar | ML señal P · R · F1 | ML revisar P · R · F1 | Reglas P · R · F1 |
|---|---|---|---|---|
| pago_anticipado | 0.50 / 0.35 | 0.52 · 0.57 · 0.55 | 0.39 · 0.90 · 0.55 | 0.85 · 1.00 · 0.92 |
| acceso_invasivo | 0.50 / 0.40 | 0.71 · 0.82 · 0.76 | 0.64 · 0.88 · 0.74 | 0.95 · 1.00 · 0.97 |
| amenaza_presion | 0.50 / 0.35 | 0.58 · 0.69 · 0.63 | 0.41 · 0.86 · 0.56 | 1.00 · 0.86 · 0.93 |
| condiciones_opacas | 0.50 / 0.30 | 0.89 · 0.71 · 0.79 | 0.61 · 0.99 · 0.76 | 0.96 · 0.95 · 0.96 |

- F1 macro — ML señal: **0.682** · ML revisar: 0.651 · ML 0.5: 0.682 · Reglas: **0.944**
- F1 macro ML por familia (0.5): [0.601, 0.557, 0.741, 0.692, 0.758] → media 0.67 ± 0.079
- Umbrales elegidos sobre las mismas predicciones fuera de fold: las métricas 'ml_at_review' y 'ml_at_signal' pueden ser algo optimistas.

## Matrices de confusión (ML, umbral de señal)

| Etiqueta | VN | FP | FN | VP |
|---|---|---|---|---|
| pago_anticipado | 413 | 65 | 52 | 70 |
| acceso_invasivo | 449 | 38 | 20 | 93 |
| amenaza_presion | 339 | 87 | 54 | 120 |
| condiciones_opacas | 381 | 17 | 58 | 144 |
