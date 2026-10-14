import pytest

from sipan.rules import match_rules, predict_labels

from .conftest import ANNEX_C


@pytest.mark.parametrize("text, label", [
    ("Yapea S/ 50 de seguro y hoy recibes tu dinero.", "pago_anticipado"),
    ("Para liberar tu préstamo deposita S/ 30.", "pago_anticipado"),
    ("Se paga una comisión antes del desembolso.", "pago_anticipado"),
    ("Instala el APK y acepta los permisos de contactos.", "acceso_invasivo"),
    ("Comparte tu clave de banca por internet.", "acceso_invasivo"),
    ("Avisaremos a todos tus contactos que eres moroso.", "amenaza_presion"),
    ("Solo por hoy, decide ya.", "amenaza_presion"),
    ("No le cuentes a tu familia de este préstamo.", "amenaza_presion"),
    ("Sin contrato y sin papeleo, todo por WhatsApp.", "condiciones_opacas"),
    ("Te prestamos S/ 800 sin aval. Escríbenos.", "condiciones_opacas"),
])
def test_rule_detects_signal(text, label):
    assert predict_labels(text)[label] == 1


@pytest.mark.parametrize("text, label", [
    ("Nunca te pediremos depósitos por adelantado.", "pago_anticipado"),
    ("Jamás solicitaremos acceso a tus contactos ni a tu galería.", "acceso_invasivo"),
    ("Nuestra app no requiere permisos de contactos ni fotos.", "acceso_invasivo"),
    ("Si alguien te pide dinero para liberar un préstamo, no lo hagas.", "pago_anticipado"),
    ("Te recordamos que tu cuota de S/ 120 vence el 15 de mayo.", "amenaza_presion"),
    ("Tu préstamo registra 5 días de atraso.", "condiciones_opacas"),
    ("Crédito de S/ 2.000 en 12 cuotas de S/ 210, TCEA 38%.", "condiciones_opacas"),
])
def test_rule_respects_negations_and_safe_context(text, label):
    assert predict_labels(text)[label] == 0


def test_match_returns_sentence_with_evidence():
    text = "Hola vecino. Deposita S/ 30 para liberar tu préstamo. Saludos."
    match = next(m for m in match_rules(text) if m.label == "pago_anticipado")
    assert match.phrase == "Deposita S/ 30 para liberar tu préstamo."


def test_evidence_not_cut_at_thousands_separator():
    text = "Te presto S/ 1.000 al toque, solo yapeame S/ 40 de comision. Gracias."
    match = next(m for m in match_rules(text) if m.label == "pago_anticipado")
    assert match.phrase == "Te presto S/ 1.000 al toque, solo yapeame S/ 40 de comision."


def test_accent_insensitive():
    assert predict_labels("AUTORIZA EL ACCESO A TU GALERIA")["acceso_invasivo"] == 1
    assert predict_labels("autoriza el acceso a tu galería")["acceso_invasivo"] == 1


def test_annex_c_examples():
    assert predict_labels(ANNEX_C["pago"])["pago_anticipado"] == 1
    assert predict_labels(ANNEX_C["acceso"])["acceso_invasivo"] == 1
    assert predict_labels(ANNEX_C["amenaza"])["amenaza_presion"] == 1
    assert not any(predict_labels(ANNEX_C["sin_senales"]).values())
