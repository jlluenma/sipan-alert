"""Textos de orientación preventiva y fuentes oficiales (US-03, US-04).

Todo el contenido usa lenguaje de "señal observada": nunca afirma que una
oferta sea fraude. Enlaces tomados de las referencias del APF1 y verificados
(HTTP 200) el 2026-10-14; teléfonos según comunicaciones oficiales de SBS y MININTER.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OfficialSource:
    name: str
    description: str
    url: str


@dataclass(frozen=True)
class Contact:
    name: str
    value: str
    use: str


@dataclass(frozen=True)
class LabelInfo:
    short: str  # nombre de 2-3 palabras para etiquetas y resaltados
    icon: str  # nombre de Material Symbols
    title: str
    explanation: str
    recommendations: tuple[str, ...]


SOURCES = {
    "sbs_informalidad": OfficialSource(
        "SBS — Modalidades de informalidad",
        "Cómo operan los préstamos y captaciones de dinero no autorizados.",
        "https://www.sbs.gob.pe/usuarios/aprende-con-la-sbs/modalidades-de-informalidad",
    ),
    "sbs_aplicativos": OfficialSource(
        "SBS advierte sobre aplicativos que ofrecen préstamos",
        "Alerta sobre apps que piden acceso a contactos, fotos y videos y luego presionan a los deudores.",
        "https://www.sbs.gob.pe/noticia/detallenoticia/idnoticia/3899",
    ),
    "mininter_gota": OfficialSource(
        "MININTER — «El préstamo gota a gota es un delito»",
        "Campaña oficial con información para reconocer y denunciar la extorsión por préstamos.",
        "https://www.gob.pe/institucion/mininter/campa%C3%B1as/25968-el-prestamo-gota-a-gota-es-un-delito",
    ),
    "sbs_finanzas": OfficialSource(
        "SBS — Guía «Domina tus finanzas»",
        "Guía de educación financiera: crédito, tasas y costo total.",
        "https://www.sbs.gob.pe/Portals/0/jer/mat_edu_finan/Jovenes%20y%20adultos/Guias/Domina-tus-finanzas.pdf",
    ),
}

CONTACTS = (
    Contact("SBS — línea gratuita", "0-800-10840",
            "Consultar si una empresa está autorizada o reportar préstamos informales."),
    Contact("SBS — correo de informalidad", "informalidad@sbs.gob.pe",
            "Enviar información sobre personas o empresas que prestan sin autorización."),
    Contact("MININTER — Central Única de Denuncias", "1818",
            "Denunciar amenazas o extorsión relacionadas con préstamos."),
    Contact("Policía Nacional del Perú", "105",
            "Emergencias o amenazas inmediatas; también puedes acudir a la comisaría más cercana."),
)

LABEL_INFO: dict[str, LabelInfo] = {
    "pago_anticipado": LabelInfo(
        short="Pago por adelantado",
        icon="payments",
        title="Pide un pago antes de entregarte el préstamo",
        explanation=(
            "El mensaje solicita dinero (comisión, seguro, garantía o trámite) antes del desembolso. "
            "La SBS ha alertado sobre ofertas que piden depósitos previos y luego no entregan el préstamo."
        ),
        recommendations=(
            "No deposites, yapees ni transfieras dinero para «liberar», «activar» o «asegurar» un préstamo.",
            "Antes de cualquier pago, consulta a la SBS (0-800-10840) si la empresa está autorizada.",
            "Si ya pagaste, guarda comprobantes y capturas: te servirán para denunciar.",
        ),
    ),
    "acceso_invasivo": LabelInfo(
        short="Pide tus datos",
        icon="contacts",
        title="Pide acceso a tus datos personales",
        explanation=(
            "El mensaje pide acceso a contactos, fotos, mensajes, claves u otros datos que no son "
            "necesarios para evaluar un préstamo. La SBS ha advertido que algunas apps usan esos "
            "datos para presionar a los deudores."
        ),
        recommendations=(
            "No autorices acceso a contactos, galería, mensajes ni ubicación para obtener un préstamo.",
            "No instales aplicaciones fuera de las tiendas oficiales (archivos APK).",
            "Nunca compartas claves de banca, contraseñas ni códigos de verificación.",
        ),
    ),
    "amenaza_presion": LabelInfo(
        short="Amenaza o presión",
        icon="campaign",
        title="Contiene amenazas o presión para decidir rápido",
        explanation=(
            "El mensaje usa amenazas (avisar a tu familia, publicar fotos, ir a tu casa) o presión "
            "artificial (solo por hoy, no lo consultes) para que actúes sin revisar."
        ),
        recommendations=(
            "La prisa es motivo para detenerte: una oferta formal te deja revisar y consultar.",
            "Si recibes amenazas, guarda capturas y denuncia en la Central Única de Denuncias (1818) "
            "o en la comisaría más cercana.",
            "En una emergencia, llama a la Policía (105).",
        ),
    ),
    "condiciones_opacas": LabelInfo(
        short="Condiciones ocultas",
        icon="visibility_off",
        title="No muestra las condiciones económicas",
        explanation=(
            "El mensaje ofrece dinero sin indicar cuotas, tasa (TCEA), plazo o costo total, o pospone "
            "esa información. Sin esos datos no puedes saber cuánto terminarías pagando."
        ),
        recommendations=(
            "Pide por escrito: monto que recibirás, número y valor de cuotas, fechas de pago, TCEA y cargos.",
            "Una empresa formal debe entregarte la hoja resumen y el cronograma antes de firmar.",
            "No aceptes condiciones que «se explican después» del desembolso.",
        ),
    ),
}

GENERAL_RECOMMENDATIONS = (
    "Verifica que la empresa esté autorizada por la SBS antes de dar datos o dinero.",
    "No compartas DNI, claves ni datos de tus contactos por chat.",
    "Consulta con alguien de confianza antes de aceptar una oferta urgente.",
    "Si recibes amenazas, no estás solo: denuncia al 1818 o en la comisaría.",
)

LIMITS_NOTICE = (
    "Este resultado es orientativo. SipánAlert IA identifica señales en el texto que pegaste; "
    "no determina si una empresa o persona comete fraude ni certifica que un prestamista sea legítimo."
)
NO_SIGNALS_NOTICE = (
    "No se observaron las señales definidas en este texto. Esto no garantiza que la oferta sea segura: "
    "el análisis solo cubre lo que dice el mensaje."
)
SYNTHETIC_MODEL_NOTICE = (
    "Prototipo académico: el modelo se entrenó con mensajes sintéticos y puede equivocarse con "
    "redacciones nuevas."
)
