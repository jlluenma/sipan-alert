# Guía de etiquetado — SipánAlert IA (v1)

Manual de anotación del corpus (fase de **Externalización** del modelo SECI). Define cuándo marcar cada señal para que dos revisores etiqueten igual el mismo mensaje.

> Una etiqueta describe **lo que dice el texto**, no una determinación jurídica. Marcar una señal no significa que la oferta sea una estafa; no marcar ninguna no significa que sea segura.

## Esquema del dataset (Anexo A, APF1)

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | texto | Identificador único (`SYN-0001` para sintéticos). |
| `mensaje` | texto | Oferta anonimizada o sintética. |
| `pago_anticipado` | 0/1 | Ver §1. |
| `acceso_invasivo` | 0/1 | Ver §2. |
| `amenaza_presion` | 0/1 | Ver §3. |
| `condiciones_opacas` | 0/1 | Ver §4. |
| `fuente` | categoría | `sintetico`, `publico` o `voluntario_anonimizado`. |
| `grupo_similitud` | ID | Agrupa variantes casi idénticas. La división train/test se hace **por grupo**, nunca por fila. |
| `revision` | estado | `revisada`, `pendiente` o `descartada`. El entrenamiento excluye `descartada`. |

Un mensaje puede tener **varias señales a la vez** (multietiqueta).

## 1. `pago_anticipado`

**Marcar 1** si el texto pide dinero **antes** de entregar el préstamo, con cualquier nombre: comisión, seguro, garantía, trámite, notaría, activación, verificación, "primera cuota adelantada". Incluye pedidos por Yape, Plin o transferencia.

- ✅ "Para liberar tu préstamo deposita S/ 30 de trámite."
- ✅ "Yapea S/ 50 de seguro y hoy recibes el dinero."
- ❌ "Nunca te pediremos depósitos por adelantado." (negación: es un aviso, no un pedido)
- ❌ "Tu cuota de S/ 120 vence mañana." (cobro de un préstamo ya recibido)

## 2. `acceso_invasivo`

**Marcar 1** si el texto pide acceso o envío de información personal **desproporcionada** para evaluar un préstamo: contactos, galería, fotos, SMS, WhatsApp, ubicación, redes sociales, claves o contraseñas, números de familiares. También cuenta instalar APKs que piden esos permisos.

- ✅ "Autoriza el acceso a tus contactos para aprobar el crédito."
- ✅ "Comparte tu clave de banca por internet para validar ingresos."
- ❌ "Nuestra app no requiere permisos de contactos ni fotos."
- ❌ Pedir solo el DNI para identificarse **no** se marca por sí solo.

## 3. `amenaza_presion`

**Marcar 1** si hay:

- **Amenaza o coerción**: exponer al deudor ante familiares o contactos, publicar fotos, ir al domicilio o al puesto de trabajo, insultos públicos ("moroso", "estafador").
- **Presión indebida**: urgencia artificial ("solo por hoy", "responde en 10 minutos"), pedir que no se consulte con nadie o que no se lea el contrato.

- ✅ "Si no pagas hoy, tus familiares sabrán de tu deuda."
- ✅ "La oferta vence en 30 minutos, no lo consultes con nadie."
- ❌ "Te recordamos que tu cuota vence el 15 de noviembre." (recordatorio neutro)
- ❌ "Tómate el tiempo que necesites para revisar el contrato."

## 4. `condiciones_opacas`

Aplica **solo a ofertas** de préstamo (no a mensajes de cobranza). **Marcar 1** si:

- la oferta **no menciona** información económica esencial: ni cuotas (monto y número), ni tasa/TCEA, ni costo total, ni cronograma/contrato/hoja resumen; **o**
- la oferta **oculta o pospone** las condiciones: "los intereses te los explicamos después", "sin contrato", "tasa mínima, no te preocupes", "detalles por interno".

**Marcar 0** si la oferta indica cuotas y número de pagos (lo que permite calcular el total), una tasa/TCEA, el costo total, o remite a contrato, cronograma u hoja resumen entregados antes de firmar.

- ✅ "Te prestamos S/ 500 sin aval. Escríbenos al [TELEFONO]."
- ✅ "Pagas poquito diario, te contamos al aprobar."
- ❌ "Recibes S/ 900 y pagas 20 cuotas diarias de S/ 60." (permite calcular el total)
- ❌ "Oferta de S/ 2.000; tasas, cargos y calendario disponibles en contrato."

## Anonimización (obligatoria antes de incorporar un texto)

Reemplazar cualquier identificador por su marcador:

| Dato | Marcador |
|---|---|
| Teléfono | `[TELEFONO]` |
| DNI | `[DNI]` |
| Correo | `[CORREO]` |
| Enlace / web | `[URL]` |
| Cuenta bancaria / CCI | `[CUENTA]` |
| Nombre de persona | `[NOMBRE]` |

`sipan/preprocessing.py` aplica los cinco primeros de forma automática; los nombres se revisan **a mano**.

## Casos dudosos y desacuerdos

1. Si un revisor duda, marca `revision = pendiente` y anota el motivo en el registro del equipo.
2. Un segundo integrante etiqueta sin ver la primera etiqueta.
3. Si no coinciden, se discute con esta guía. Si sigue sin acuerdo, el mensaje se marca `descartada`.
4. Si un caso nuevo obliga a cambiar la guía, se sube la versión (v1 → v2) y se registra el cambio.

## Corpus v1 (Sprint 1)

`data/dataset_v1.csv` es **100 % sintético**: lo genera `scripts/generate_synthetic.py` combinando frases escritas por el equipo a partir de las advertencias de la SBS y el MININTER. Todas las filas tienen `fuente = sintetico` y `revision = pendiente` hasta la revisión humana de una muestra.

- `grupo_similitud` es la **familia de redacción** (F1–F5): cada familia usa frases distintas. La evaluación entrena con 4 familias y prueba con la quinta, así se mide si el modelo generaliza a redacciones que nunca vio.
- Las métricas sobre este corpus **no representan** el desempeño con mensajes reales de Chiclayo.
