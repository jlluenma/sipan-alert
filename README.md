# SipánAlert IA

Prototipo web basado en Machine Learning que identifica **señales de riesgo** en textos de ofertas de préstamo y brinda orientación preventiva con fuentes oficiales (SBS, MININTER).

> SipánAlert IA **no** determina que una oferta sea fraude ni certifica que un prestamista sea legítimo. Sus resultados son orientativos.

Proyecto del curso Innovación y Transformación Digital, UTP Chiclayo, 2026. **Versión: Sprint 1 (US-01 a US-05) + fase de integración T-3 + consolidación pre-APF3 (PR #8 y PR #9).**

## Qué hace (Sprint 1)

| Historia | Implementación |
|---|---|
| US-01: Pegar una oferta | Formulario de análisis en la interfaz React: valida texto vacío, longitud (10 a 3000 caracteres) y texto sin palabras. Ejemplos ficticios en un clic. |
| US-02: Identificar señales | Clasificador multietiqueta TF-IDF + regresión logística (One-vs-Rest) junto con reglas documentadas. Si el modelo no está disponible, avisa y usa solo reglas. |
| US-03: Entender por qué | Vista de resultado: el mensaje del usuario con las frases de riesgo **resaltadas y etiquetadas**, un veredicto en una línea y una tarjeta por señal con «Qué hacer» y «¿Por qué lo marcamos?» (origen, confianza y términos influyentes). |
| US-04: Orientación | Vista con dos acciones por señal detectada, contactos con un toque para llamar o escribir (SBS 0-800-10840, MININTER 1818, PNP 105) y fuentes oficiales. |
| US-05: Privacidad | El análisis público no persiste texto. Teléfonos, DNI, correos, enlaces y cuentas se ocultan antes de analizar. El envío de reportes para revisión requiere login y consentimiento explícito. |

**Señales (Anexo A, APF1):** `pago_anticipado`, `acceso_invasivo`, `amenaza_presion` y `condiciones_opacas`. Los criterios de cada una están en [`data/LABELING_GUIDE.md`](data/LABELING_GUIDE.md).

## Extensiones integradas (post-Sprint 1)

| Capacidad | Dónde se usa |
|---|---|
| Entrada por foto (OCR cliente) y por voz | Analizador principal; el OCR corre con tesseract.js en el navegador y nunca sube la imagen. |
| Comparación con reportes validados | Vista de resultado: señala similitud con reportes revisados sin exponer su texto crudo. |
| Investigación de entidad | Vista `Investigar entidad` (`/`): consulta un catálogo local de aplicaciones, empresas y dominios reportados. Con sesión iniciada incluye noticias vía Gemini (envía solo el nombre anonimizado). |
| PDF del resultado | Botón «Descargar PDF» en la vista de resultado; el PDF se genera 100 % en el navegador con jsPDF. |
| Notificaciones del usuario | Campana en la barra: avisa al autor cuando un reporte o publicación suya se valida o rechaza. |
| Fotos en comunidad | Las publicaciones aprobadas pueden llevar imágenes; se normalizan en el servidor (EXIF stripping, re-encoding, límite 5 MB). |

## Qué es real y qué es simulado

- **Dataset:** 100 % **sintético** (600 mensajes), generado por `scripts/generate_synthetic.py` a partir de frases escritas por el equipo según las advertencias de la SBS y el MININTER. No contiene mensajes reales.
- **Modelo:** entrenado y evaluado de verdad sobre ese corpus. Sus métricas **no representan** el desempeño con mensajes reales. Ver [`reports/metrics_v1.md`](reports/metrics_v1.md).
- **Resultado de la evaluación:** con validación por familias de redacción (GroupKFold), el ML obtiene un F1 macro de **0,68**, mientras que el baseline de reglas llega a **0,94**. Las reglas salen favorecidas porque se escribieron conociendo las mismas frases. Con este corpus el ML **no supera** al baseline; tal como prevé el APF1, la app combina ambos y muestra el origen de cada señal. Mejorar el modelo requiere un corpus revisado más diverso.

## Inicio rápido (Windows)

Requisitos: **Python 3.12** (también sirve 3.11+), **Node.js 20+**, **PostgreSQL 16+** y **Git**.

```powershell
# 1. Clonar
cd C:\proyectos
git clone https://github.com/jlluenma/sipan-alert.git
cd sipan-alert

# 2. Entorno Python
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar .env (ver sección "PostgreSQL y migraciones")
# Crear .env con DATABASE_URL y SIPAN_SESSION_SECRET

# 4. Migraciones y datos demo
alembic upgrade head
python scripts/create_admin.py admin@ejemplo.com   # o cargar seed demo

# 5. Entrenar el modelo (solo la primera vez, unos 5 segundos)
python scripts/train.py

# 6. Levantar API (terminal 1)
python -m uvicorn api.main:app --host 127.0.0.1 --port 8015

# 7. Levantar interfaz React (terminal 2)
cd frontend
npm install
npm run dev
```

Luego abre `http://localhost:5173`. La API corre en `http://localhost:8015`.

Para detener cada proceso, `Ctrl + C`. En Linux o macOS: `python3 -m venv .venv` y `source .venv/bin/activate`.

### Otros comandos

```bash
pytest                                 # suite automática (requiere Postgres levantado)
python scripts/generate_synthetic.py   # regenera data/dataset_v1.csv (determinista, semilla 42)
python scripts/seed_demo.py            # recarga fixtures/demo.dump en la DB local
```

El modelo no se sube a git. Reentrenar con el mismo dataset reproduce exactamente las métricas de `reports/`.

### Ejemplos ficticios para la demo (Anexo C)

| Mensaje | Señal esperada |
|---|---|
| «Deposita S/ 30 para liberar tu préstamo de S/ 500». | Pago anticipado |
| «Autoriza acceso a toda tu lista de contactos para aprobar el crédito». | Acceso invasivo |
| «Si no pagas hoy, tus familiares sabrán de tu deuda». | Amenaza o presión |
| «Recibes S/ 900 y pagas 20 cuotas de S/ 60». | El cálculo del total queda para el Sprint 2 |
| «Oferta de S/ 2.000; tasas, cargos y calendario disponibles en contrato». | Sin las señales definidas |

## Estructura

```
sipan/                     Núcleo (agnóstico a la UI; sin imports de Streamlit, React o FastAPI)
  config.py                Rutas, etiquetas, límites de entrada y DATABASE_URL
  preprocessing.py         Validación, anonimización y normalización para el modelo
  rules.py                 Reglas documentadas (baseline y explicación)
  model.py                 Pipeline TF-IDF + LogReg, carga con verificación SHA-256 y términos influyentes
  analyzer.py              analyze(texto) -> AnalysisResult (ML + reglas + avisos + similitud)
  guidance.py              Textos de orientación, fuentes oficiales y contactos
  auth.py                  AuthService (scrypt + roles usuario/revisor/administrador)
  database.py              SQLAlchemy engine lru-cached con DATABASE_URL
  persistence/             Modelos ORM y repositorios
  services.py              ReportService, LearningService, AccountService
  faq.py / gemini_faq.py   Chatbot preventivo con fallback a catálogo local (texto anonimizado antes de enviar)
  entity_investigation.py  Catálogo local de entidades reportadas (apps, empresas, dominios)
  web_verification.py      Verificación de contexto público con Gemini (anonimiza antes de enviar)
  novelty.py               Detección de agrupaciones emergentes
  dataset_versions.py      Composición de DatasetVersion a partir de reports validados
api/
  main.py                  FastAPI en puerto 8015, sesión cookie firmada
  community.py             Feed moderado con fotos (EXIF stripping, auditoría T-3.11 pendiente)
frontend/                  React + Vite (UI oficial desde 2026-11-18)
  src/App.jsx              App pública (análisis, resultado, comunidad, investigación, cuenta)
  src/PanelApp.jsx         Panel de revisor y administrador en /panel
  src/EntityInvestigation.jsx  Vista de investigación de entidad
  src/UserNotifications.jsx    Campana de notificaciones del autor
  src/ResultActions.jsx + resultPdf.js  Acciones del resultado y PDF cliente
migrations/                Alembic (head `20261118_06`: incluye community_post_photos)
data/
  LABELING_GUIDE.md        Manual de etiquetado (SECI: externalización)
  dataset_v1.csv           Corpus sintético versionado
  sbs_alerts*.json         Alertas oficiales consultables
fixtures/
  demo.dump                pg_dump para seed local (ver scripts/seed_demo.py)
scripts/
  generate_synthetic.py    Generador del corpus
  train.py                 Entrenamiento, evaluación sin fuga y reporte
  train_candidate.py       Entrenamiento de modelo candidato sobre reports validados
  create_admin.py          Crea una cuenta administradora
  grant_role.py            Agrega un rol a una cuenta existente
  seed_demo.py             Restaura fixtures/demo.dump, aplica alembic upgrade y resetea passwords
reports/                   Métricas versionadas (evidencia del sprint)
tests/                     pytest 93: entrada, anonimización, reglas, dataset, modelo, analizador, privacidad y continual learning
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

## Ficha técnica

| Aspecto | Término técnico | En SipánAlert IA |
|---|---|---|
| Tipo de sistema | **Sistema de apoyo a la decisión** | Orienta; la decisión es del usuario. |
| Problema | **Clasificación de texto multietiqueta** (PLN), **aprendizaje supervisado** | Un mensaje puede tener varias de las 4 señales a la vez. |
| Enfoque | **Sistema híbrido**: reglas + aprendizaje automático | Reglas interpretables y un modelo estadístico; se combinan sus resultados. |
| Características | **Vectorización TF-IDF** con **n-gramas de palabras** (1–2) y **de caracteres** (3–5), unidas con `FeatureUnion` | Los n-gramas de caracteres toleran errores de tipeo. |
| Clasificador | **Regresión logística One-vs-Rest**, `class_weight="balanced"` | Un clasificador binario por etiqueta, con ponderación por desbalance de clases. |
| Decisión | **Umbrales de decisión**; umbral de revisión calibrado con **F2** | Favorece el *recall*: prefiere avisar de más que dejar pasar una señal. |
| Datos | **Datos sintéticos** generados de forma **determinista** (semilla 42) | Reproducibles. |
| Evaluación | **Validación cruzada agrupada** (`GroupKFold`) con predicciones fuera de fold | Evita la **fuga de datos** entre familias de redacción. |
| Arquitectura | **Arquitectura en capas**, **separación de responsabilidades** | `sipan/` (dominio) no depende de `api/` ni de `frontend/`. |
| Ciclo del modelo | **Entrenamiento offline** e **inferencia en línea**; **serialización** con `joblib` | `scripts/train.py` entrena una vez; `analyze()` predice en cada consulta. |
| Persistencia | **PostgreSQL** gestionado con **SQLAlchemy** y migraciones **Alembic** | Reports con consentimiento, dataset versioning, roles y sesiones. |
| Seguridad | **Verificación de integridad** (SHA-256) contra **deserialización insegura** | El modelo solo se carga si su hash coincide. |
| Privacidad | **Privacidad desde el diseño**, **anonimización de PII**, **consentimiento explícito** para reports | El análisis público no persiste; solo los reports consentidos se almacenan tras anonimizar. |
| Calidad | **Pruebas automatizadas** unitarias y de **regresión** | `pytest`; incluye pruebas de privacidad y de lenguaje sin certezas. |
| Proceso | **Scrum/Scrumban**, **historias de usuario**; **GitHub Flow** | Sprints del APF2; ramas por cambio, PR con revisión y `main` protegida. |

## Limitaciones conocidas

- **Corpus sintético:** las métricas no representan el desempeño con mensajes reales, y el ML (F1 macro 0,68) no supera a las reglas (0,94).
- **Sesgo del corpus:** la apertura «sin aval y sin Infocorp» aparece en mensajes limpios y de riesgo, así que el modelo aprendió que es neutral (una **correlación espuria**).
- **Ofertas que quitan los controles normales de un préstamo** («te regalamos plata», «sin revisión en Infocorp, sin garantías», tasas irrealmente bajas) hoy no se detectan.
- **Auditoría técnica de `api/community.py` pendiente** (T-3.11): aun con el endpoint de fotos usando SQL parametrizado, queda la revisión formal del feed y de los filtros antes de publicar la comunidad.

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

- **Análisis público:** no requiere cuenta. El texto se procesa en memoria y **no se persiste** en disco ni en logs.
- **Reports para aprendizaje:** se almacenan en PostgreSQL únicamente si el usuario está autenticado y marca `consent=true` tras revisar la copia anonimizada. Cada report guarda un `content_hash` (para evitar duplicados) y un `deletion_token_hash` que permite al autor borrarlo después.
- **Anonimización:** teléfonos, DNI, correos, enlaces y cuentas se reemplazan antes de analizar o almacenar.
- **Modelo:** se carga solo si su huella SHA-256 coincide con la registrada al entrenar. Nunca cargues archivos `.joblib` de origen desconocido.

## Aprendizaje continuo y PostgreSQL

El análisis ordinario sigue procesando el texto en memoria. Desde el resultado, una persona autenticada puede decidir compartir una copia anonimizada para revisión. Los aportes consentidos se almacenan en PostgreSQL mediante SQLAlchemy.

1. Analiza un mensaje y selecciona **Compartir para revisión** después de revisar la copia anonimizada y aceptar el consentimiento.
2. Guarda el ID y el código de eliminación que muestra la aplicación. El código sirve para borrar el contenido del aporte desde la vista de cuenta.
3. Un revisor etiqueta cada aporte en el panel (`/panel`).
4. Un administrador crea una versión del dataset. Solo incorpora aportes validados sin duplicados.
5. `scripts/train_candidate.py` entrena un modelo candidato sobre esa versión, que se evalúa contra el baseline antes de reemplazar al modelo activo.

## PostgreSQL y migraciones

Configura las conexiones fuera del repositorio mediante `.env` o variables del sistema.

```env
DATABASE_URL=postgresql+psycopg://USUARIO:CONTRASENA@localhost:5432/sipanalert_db
DATABASE_MIGRATION_URL=postgresql+psycopg://USUARIO:CONTRASENA@localhost:5432/sipanalert_db
SIPAN_SESSION_SECRET=cambia-esto-en-produccion
# Opcional: habilita el chatbot FAQ con Gemini
GEMINI_API_KEY=
```

Aplica la migración antes de ejecutar la aplicación con persistencia:

```bash
alembic upgrade head
```

Las revisiones de esquema posteriores se generan con `alembic revision --autogenerate -m "descripcion"` y se revisan antes de aplicar `alembic upgrade head`. No guardes credenciales en Git.

### Login y roles

El registro y login viven en la interfaz React. Crea la primera cuenta administradora tras ejecutar las migraciones:

```bash
python scripts/create_admin.py admin@ejemplo.com
```

Los roles `revisor` y `administrador` acceden al panel (`/panel`). Las revisiones registran la cuenta que tomó la decisión.

Otorga un rol a una cuenta existente con:

```bash
python scripts/grant_role.py revisor@ejemplo.com revisor
```

Para datos de desarrollo rápido, `python scripts/seed_demo.py` restaura `fixtures/demo.dump` con tres cuentas (admin, revisor, usuario) y un report ya validado.

## Fuera del Sprint 1

- **Sprint 2:** calculadora de pagos (US-06), más fuentes oficiales (US-07) y ejemplos didácticos (US-12).
- **Sprint 3:** reporte técnico de métricas en la UI (US-08) y descarga del resumen (US-09).
- **Sprint 4:** OCR de capturas (US-10) e historial con consentimiento (US-11).
