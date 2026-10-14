import pytest

from sipan import config
from sipan.preprocessing import InputError, anonymize, normalize_for_model, validate_input


class TestValidateInput:
    @pytest.mark.parametrize("text", [None, "", "   ", "\n\t  "])
    def test_empty_text_is_rejected(self, text):
        with pytest.raises(InputError, match="Pega el texto"):
            validate_input(text)

    def test_too_short(self):
        with pytest.raises(InputError, match="muy corto"):
            validate_input("hola")

    def test_too_long(self):
        with pytest.raises(InputError, match="supera el máximo"):
            validate_input("préstamo " * (config.MAX_TEXT_LENGTH // 5))

    @pytest.mark.parametrize("text", ["1234567890 999", "!!!!????####$$$$", "💰💰💰💰💰💰💰💰💰💰💰"])
    def test_without_words(self, text):
        with pytest.raises(InputError, match="no contiene palabras"):
            validate_input(text)

    def test_strips_and_removes_control_characters(self):
        assert validate_input("  Te presto​ S/ 500 hoy\x00  ") == "Te presto S/ 500 hoy"

    def test_special_characters_and_typos_are_accepted(self):
        text = "t3 prest@mos s/500 ¡¡al toq!! 🔥🔥 deposita ya q no ay tiempo"
        assert validate_input(text) == text

    def test_max_length_is_inclusive(self):
        text = "a" * config.MAX_TEXT_LENGTH
        assert validate_input(text) == text


class TestAnonymize:
    @pytest.mark.parametrize("raw, tag", [
        ("Llama al 987654321.", "TELEFONO"),
        ("Llama al 987 654 321, gracias", "TELEFONO"),
        ("WhatsApp +51 912-345-678", "TELEFONO"),
        ("Mi DNI es 45678912.", "DNI"),
        ("Escribe a prestamos.ya@gmail.com", "CORREO"),
        ("Entra a https://bit.ly/abc123", "URL"),
        ("Descarga en prestafacil.pe/app", "URL"),
        ("CCI 00219100123456789012", "CUENTA"),
        ("Cuenta 191-2345678-0-12 del BCP", "CUENTA"),
    ])
    def test_identifiers_are_masked(self, raw, tag):
        result = anonymize(raw)
        assert f"[{tag}]" in result.text
        assert result.replaced.get(tag) == 1

    @pytest.mark.parametrize("raw", [
        "Préstamo de S/ 1.500 en 12 cuotas de S/ 150",
        "Total 10.000.000 y TCEA 45.5%",
        "Monto S/ 2,000 a 24 meses",
    ])
    def test_amounts_are_not_masked(self, raw):
        result = anonymize(raw)
        assert result.text == raw
        assert not result.found_identifiers


def test_normalize_for_model_tokens():
    out = normalize_for_model("💰 Deposita S/ 30 para LIBERAR tu préstamo, TCEA 45%; 20 cuotas. Llama 987654321")
    assert out == ("deposita tok_monto para liberar tu prestamo tcea tok_porcentaje "
                   "tok_num cuotas llama tok_telefono")


def test_normalize_handles_dataset_placeholders():
    assert "tok_cuenta" in normalize_for_model("deposita a la cuenta [CUENTA]")
