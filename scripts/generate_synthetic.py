"""Genera el corpus sintético v1 (data/dataset_v1.csv).

Cada mensaje se arma con fragmentos escritos a mano (ver LABELING_GUIDE.md) y
las etiquetas se derivan de los fragmentos usados. El fragmento i de cada pool
pertenece a la familia i % N_FAMILIES; un mensaje solo usa fragmentos de su
familia. La evaluación agrupa por familia, así el test contiene redacciones que
el modelo nunca vio en entrenamiento.

Uso: python scripts/generate_synthetic.py [--n 600] [--seed 42]
"""

from __future__ import annotations

import argparse
import random
import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sipan import config  # noqa: E402

N_FAMILIES = 5

APERTURAS = [
    "¡Hola! Te ofrecemos un préstamo de S/ {monto}.",
    "Préstamos rápidos de S/ {monto} para tu negocio.",
    "¿Necesitas efectivo? Te prestamos S/ {monto}.",
    "Crédito personal hasta S/ {monto}, desembolso en 24 horas.",
    "Estimado cliente, tiene un préstamo preaprobado de S/ {monto}.",
    "Préstamos para comerciantes del mercado, desde S/ {monto}.",
    "Hola vecino, tenemos dinero disponible: S/ {monto} para ti.",
    "Campaña de créditos: accede a S/ {monto} para capital de trabajo.",
    "Te prestamos S/ {monto} sin aval y sin Infocorp.",
    "Felicidades, calificas a un préstamo de S/ {monto}.",
    "Préstamo express de S/ {monto} para emprendedores.",
    "Oferta para independientes: crédito de S/ {monto}.",
    "¿Te falta para la campaña? Te damos S/ {monto} hoy mismo.",
    "Atención: préstamo disponible de S/ {monto} con trámite sencillo.",
    "Hola, somos una financiera y te ofrecemos S/ {monto}.",
]

PAGO_ANTICIPADO = [
    "Para liberar tu préstamo debes depositar S/ {adelanto} por gastos de trámite.",
    "Yapea S/ {adelanto} de seguro y hoy mismo recibes el dinero.",
    "Antes del desembolso se paga una comisión de apertura de S/ {adelanto} a la cuenta [CUENTA].",
    "Solo necesitas adelantar la primera cuota de S/ {adelanto} para activar el crédito.",
    "Envía S/ {adelanto} por Plin para la verificación y te depositamos.",
    "Para aprobar tu solicitud realiza un abono previo de S/ {adelanto}.",
    "El costo de evaluación es S/ {adelanto}, se paga antes de recibir el préstamo.",
    "Deposita la garantía de S/ {adelanto} y tu dinero llega en minutos.",
    "Tu crédito está aprobado, falta pagar S/ {adelanto} de notaría para el desembolso.",
    "Transfiere S/ {adelanto} para cubrir el seguro de desgravamen y liberamos el monto.",
    "Primero haces un pago de S/ {adelanto} por apertura de expediente.",
    "Para enviarte el dinero necesitamos que deposites S/ {adelanto} de comisión.",
    "Paga S/ {adelanto} de activación por Yape al [TELEFONO] y recibes tu préstamo.",
    "Se requiere un adelanto de S/ {adelanto} para reservar tu crédito.",
    "Antes de desembolsar debes cancelar S/ {adelanto} por gastos administrativos.",
]

ACCESO_INVASIVO = [
    "Descarga la app y autoriza el acceso a tus contactos para aprobar el crédito.",
    "Necesitamos permiso a tu galería de fotos y a tu lista de contactos.",
    "Para evaluarte envíanos foto de tu DNI y captura de tus contactos.",
    "La aplicación pedirá acceso a tus contactos, fotos y mensajes; acéptalos todos.",
    "Danos acceso a tu WhatsApp para verificar tus referencias.",
    "Debes compartir tu lista de contactos y 10 referencias familiares.",
    "Instala el APK y acepta los permisos de cámara, contactos y ubicación.",
    "Para aprobar necesitamos acceso a tu agenda telefónica.",
    "Envía una selfie con tu DNI y permite el acceso a tu galería.",
    "Autoriza la lectura de tus SMS y contactos para continuar.",
    "Comparte tu clave de banca por internet para validar tus ingresos.",
    "Requerimos los números de 5 familiares y acceso a tus redes sociales.",
    "Activa los permisos de contactos y almacenamiento en la app para el desembolso.",
    "Mándanos la contraseña de tu correo para registrar la solicitud.",
    "Sin acceso a tus contactos no podemos aprobar el préstamo.",
]

PRESION = [
    "Responde en 10 minutos o pierdes la oferta.",
    "Última oportunidad: solo por hoy, decide ya.",
    "Si no aceptas ahora, el cupo se le da a otra persona.",
    "Cupos limitados, confirma de inmediato sin pensarlo.",
    "No hay tiempo para revisar contratos, acepta ya.",
    "No le cuentes a tu familia, es una oferta reservada solo para ti.",
    "La oferta vence en 30 minutos, no lo consultes con nadie.",
    "Si no confirmas hoy, quedas bloqueado para futuros créditos.",
    "Decide rápido, mañana ya no habrá dinero disponible.",
    "Acepta antes de que termine el día o perderás tu aprobación.",
]

AMENAZA = [
    "Si no pagas hoy, tus familiares sabrán de tu deuda.",
    "Vamos a publicar tus fotos en tus contactos si no cancelas.",
    "Si no depositas, iremos a buscarte a tu puesto del mercado.",
    "Sabemos dónde vives, paga o atente a las consecuencias.",
    "Te vamos a exponer como estafador en redes sociales.",
    "Tienes una hora para pagar o llamaremos a tu trabajo.",
    "Paga o tu familia tendrá problemas.",
    "Avisaremos a todos tus contactos que eres moroso.",
    "Si no pagas la mora hoy, mandaremos gente a tu casa.",
    "Tu foto ya está lista para enviarse a tus contactos, paga ahora.",
]

CONDICIONES_CLARAS = [
    "Pagas {n} cuotas mensuales de S/ {cuota}, TCEA {tcea}%.",
    "Tasa efectiva anual {tea}%, plazo de {n} meses, cuota de S/ {cuota}.",
    "El costo total del crédito es S/ {total} en {n} cuotas fijas.",
    "Te entregamos el cronograma de pagos y la hoja resumen antes de firmar.",
    "TEA {tea}%, TCEA {tcea}%, sin comisiones adicionales; todo figura en el contrato.",
    "Cuotas de S/ {cuota} durante {n} meses, con cronograma detallado.",
    "Revisa la hoja resumen: tasa, seguros y comisiones están detallados.",
    "Plazo de {n} meses con una TCEA referencial de {tcea}%.",
    "Monto total a pagar: S/ {total}, incluyendo intereses y seguro.",
    "Las condiciones (tasa, cargos y calendario) están en el contrato que recibirás.",
    "Recibes el dinero y devuelves {n} cuotas diarias de S/ {cuota}.",
    "Puedes simular tu crédito en nuestra web antes de aceptar; TCEA {tcea}%.",
    "Son {n} cuotas fijas de S/ {cuota} con fechas de pago definidas.",
    "Te enviamos el contrato y la hoja resumen para que los revises con calma.",
    "Cronograma de {n} pagos quincenales de S/ {cuota}, TCEA {tcea}%.",
]

CONDICIONES_OPACAS = [
    "Los intereses te los explicamos después del depósito.",
    "Sin papeleo y sin contrato, todo por WhatsApp.",
    "La tasa es mínima, no te preocupes por los detalles.",
    "Pagas poquito diario, te contamos al aprobar.",
    "Las cuotas se definen después de que recibas el dinero.",
    "No necesitas firmar nada, el interés lo conversamos luego.",
    "Sin cronograma: pagas lo que te indique el cobrador cada día.",
    "Cero requisitos y cero contrato.",
    "El costo final depende del cobrador, se arregla en el momento.",
    "Interés bajito, los detalles por interno.",
]

# Frases con palabras "de riesgo" pero en sentido preventivo: enseñan al modelo
# que la palabra sola no es la señal.
NEGACIONES_SEGURAS = [
    "Nunca te pediremos depósitos por adelantado.",
    "No cobramos comisiones antes del desembolso.",
    "Jamás solicitaremos acceso a tus contactos ni a tu galería.",
    "No compartas tu clave con nadie, ni siquiera con nosotros.",
    "Nuestra app no requiere permisos de contactos ni fotos.",
    "Tómate el tiempo que necesites para revisar el contrato.",
    "Puedes consultar con tu familia antes de decidir.",
    "Verifica que somos una empresa supervisada por la SBS.",
    "Ningún asesor te pedirá pagos previos por Yape o Plin.",
    "Si alguien te pide dinero para liberar un préstamo, no lo hagas y repórtalo.",
]

CIERRES = [
    "Escríbenos al [TELEFONO].",
    "Más info por interno.",
    "Atención de lunes a sábado.",
    "Visítanos en [URL].",
    "Responde SI para continuar.",
    "Consultas al WhatsApp [TELEFONO].",
    "Te esperamos en nuestra agencia de Chiclayo.",
    "Saludos cordiales.",
    "Solicítalo desde nuestra web oficial.",
    "Contáctanos para más información.",
]

COBRANZA_BASE = [
    "Hola, te recordamos que tu cuota de S/ {cuota} vence el {fecha}.",
    "Estimado cliente, tiene un saldo pendiente de S/ {cuota}.",
    "Tu préstamo registra {dias} días de atraso.",
    "Recordatorio: el pago de tu crédito vence mañana.",
    "Hola, tu cuota número {k} de {n} está por vencer.",
    "Aviso de cobranza: cuota de S/ {cuota} pendiente.",
    "Te escribimos por tu deuda de S/ {cuota}.",
    "Su crédito presenta una cuota vencida de S/ {cuota}.",
    "Le informamos que su fecha de pago es el {fecha}.",
    "Hola, tu préstamo tiene un pago pendiente de S/ {cuota}.",
]

COBRANZA_CIERRE = [
    "Puedes pagar en cualquier agencia o por la app oficial.",
    "Si ya pagaste, ignora este mensaje.",
    "Para reprogramar tu deuda acércate a nuestras oficinas.",
    "Consulta tu cronograma en la banca por internet.",
    "Evita intereses moratorios pagando a tiempo.",
    "Ante dudas llama a nuestra central de atención.",
    "Puedes solicitar una refinanciación sin costo.",
    "Revisa tu estado de cuenta en la app.",
    "Gracias por tu puntualidad.",
    "Tienes derecho a solicitar tu cronograma actualizado.",
]

POOLS = {
    "APERTURAS": APERTURAS,
    "PAGO_ANTICIPADO": PAGO_ANTICIPADO,
    "ACCESO_INVASIVO": ACCESO_INVASIVO,
    "PRESION": PRESION,
    "AMENAZA": AMENAZA,
    "CONDICIONES_CLARAS": CONDICIONES_CLARAS,
    "CONDICIONES_OPACAS": CONDICIONES_OPACAS,
    "NEGACIONES_SEGURAS": NEGACIONES_SEGURAS,
    "CIERRES": CIERRES,
    "COBRANZA_BASE": COBRANZA_BASE,
    "COBRANZA_CIERRE": COBRANZA_CIERRE,
}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "setiembre", "octubre", "noviembre", "diciembre"]
EMOJIS = ["💰", "🔥", "✅", "📲", "💸", "⚠️", "👉"]


def _family_pool(pool: list[str], family: int) -> list[str]:
    return [frag for i, frag in enumerate(pool) if i % N_FAMILIES == family]


def _amounts(rng: random.Random) -> dict[str, str]:
    monto = rng.choice([300, 500, 800, 1000, 1500, 2000, 3000, 5000])
    n = rng.choice([6, 10, 12, 18, 20, 24, 30])
    cuota = round(monto * rng.uniform(1.1, 1.8) / n)
    tea = rng.randint(18, 95)
    return {
        "monto": f"{monto:,}".replace(",", "."),
        "adelanto": str(rng.choice([20, 30, 50, 80, 100, 150])),
        "n": str(n),
        "k": str(rng.randint(1, n)),
        "cuota": str(cuota),
        "total": f"{cuota * n:,}".replace(",", "."),
        "tea": str(tea),
        "tcea": str(tea + rng.randint(2, 15)),
        "dias": str(rng.choice([3, 5, 10, 15, 30])),
        "fecha": f"{rng.randint(1, 28)} de {rng.choice(MESES)}",
    }


def _strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def _informal_style(text: str, rng: random.Random) -> str:
    """Imita la escritura de chat: minúsculas, sin tildes, abreviaturas, emojis."""
    if rng.random() < 0.5:
        text = text.lower()
    if rng.random() < 0.5:
        text = _strip_accents(text)
    if rng.random() < 0.4:
        text = text.replace(" que ", " q ").replace(" por ", " x ")
    if rng.random() < 0.4:
        text = f"{rng.choice(EMOJIS)} {text}"
    return text


def _compose_offer(family: int, rng: random.Random) -> tuple[list[str], dict[str, int]]:
    pick = lambda name: rng.choice(_family_pool(POOLS[name], family))  # noqa: E731
    middle: list[str] = []
    labels = dict.fromkeys(config.LABELS, 0)

    if rng.random() < 0.35:  # oferta sin señales
        middle.append(pick("CONDICIONES_CLARAS"))
        if rng.random() < 0.5:
            middle.append(pick("NEGACIONES_SEGURAS"))
    else:
        if rng.random() < 0.45:
            middle.append(pick("PAGO_ANTICIPADO"))
            labels["pago_anticipado"] = 1
        if rng.random() < 0.40:
            middle.append(pick("ACCESO_INVASIVO"))
            labels["acceso_invasivo"] = 1
        if rng.random() < 0.35:
            middle.append(pick("PRESION"))
            labels["amenaza_presion"] = 1
        conditions = rng.random()
        if conditions < 0.35:
            middle.append(pick("CONDICIONES_CLARAS"))
        elif conditions < 0.70:
            middle.append(pick("CONDICIONES_OPACAS"))
            labels["condiciones_opacas"] = 1
        else:
            labels["condiciones_opacas"] = 1  # no menciona condiciones
        if rng.random() < 0.10:  # los estafadores también usan avisos "de confianza"
            middle.append(pick("NEGACIONES_SEGURAS"))

    rng.shuffle(middle)
    parts = [pick("APERTURAS"), *middle]
    if rng.random() < 0.8:
        parts.append(pick("CIERRES"))
    return parts, labels


def _compose_collection(family: int, rng: random.Random) -> tuple[list[str], dict[str, int]]:
    pick = lambda name: rng.choice(_family_pool(POOLS[name], family))  # noqa: E731
    labels = dict.fromkeys(config.LABELS, 0)
    parts = [pick("COBRANZA_BASE")]
    if rng.random() < 0.5:
        parts.append(pick("AMENAZA"))
        labels["amenaza_presion"] = 1
    if rng.random() < 0.6:
        parts.append(pick("COBRANZA_CIERRE"))
    return parts, labels


def generate(n: int = 600, seed: int = config.RANDOM_STATE) -> pd.DataFrame:
    for name, pool in POOLS.items():
        if len(pool) % N_FAMILIES:
            raise ValueError(f"El pool {name} debe tener un múltiplo de {N_FAMILIES} frases")

    rng = random.Random(seed)
    rows: list[dict] = []
    seen: set[str] = set()
    attempts = 0
    while len(rows) < n:
        attempts += 1
        if attempts > n * 50:
            raise RuntimeError("No se pudieron generar suficientes mensajes únicos")
        family = len(rows) % N_FAMILIES
        compose = _compose_collection if rng.random() < 0.2 else _compose_offer
        parts, labels = compose(family, rng)
        values = _amounts(rng)
        text = _informal_style(" ".join(p.format(**values) for p in parts), rng)
        if text in seen:
            continue
        seen.add(text)
        rows.append({
            "id": f"SYN-{len(rows) + 1:04d}",
            "mensaje": text,
            **labels,
            "fuente": "sintetico",
            "grupo_similitud": f"F{family + 1}",
            "revision": "pendiente",
        })
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=600)
    parser.add_argument("--seed", type=int, default=config.RANDOM_STATE)
    parser.add_argument("--out", type=Path, default=config.DATASET_PATH)
    args = parser.parse_args()

    df = generate(args.n, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False, encoding="utf-8")

    print(f"{len(df)} mensajes -> {args.out}")
    print(df[list(config.LABELS)].sum().to_string())
    no_signal = (df[list(config.LABELS)].sum(axis=1) == 0).mean()
    print(f"sin señales: {no_signal:.0%}")


if __name__ == "__main__":
    main()
