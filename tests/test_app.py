"""Pruebas de la interfaz Streamlit (4 vistas) con AppTest, sin navegador."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from sipan import config, guidance

APP = str(Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py")


@pytest.fixture(autouse=True)
def _app_on_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(APP).parent))


@pytest.fixture
def app(model, monkeypatch):
    # La app usa el modelo del fixture (entrenado en temporal), no models/.
    import ui_common

    ui_common.get_model.clear()
    monkeypatch.setattr(ui_common, "load_model", lambda: model)
    return AppTest.from_file(APP, default_timeout=60).run()


def _html(at) -> str:
    return " ".join(e.proto.body for e in at.get("html"))


def _analyze(at, text):
    at.switch_page("views/analizar.py").run()
    at.text_area(key="offer_text").input(text).run()
    next(b for b in at.button if b.label == "Revisar mensaje").click().run()
    return at


def test_home_explains_with_highlighted_demo(app):
    assert not app.exception
    html = _html(app)
    assert "Revísalo antes de pagar" in html
    # La demo usa el analizador real: resalta y etiqueta las 3 señales.
    assert html.count('class="sa-mark"') == 3
    for label in ("pago_anticipado", "acceso_invasivo", "amenaza_presion"):
        assert guidance.LABEL_INFO[label].short in html
    assert guidance.LIMITS_SHORT in html
    assert [b.label for b in app.button] == ["Revisar un mensaje"]


def test_analyze_flow_shows_verdict_highlights_and_limits(app):
    at = _analyze(app, "Deposita S/ 30 para liberar tu préstamo de S/ 500.")
    assert not at.exception
    html = _html(at)
    assert "Encontramos" in html and "señal" in html
    assert '<mark class="sa-mark"' in html
    assert guidance.LABEL_INFO["pago_anticipado"].short in html
    assert "Qué hacer:</strong> No deposites" in html
    assert guidance.LIMITS_SHORT in html


def test_offer_without_signals_shows_clear_verdict(app):
    at = _analyze(app, "Oferta de S/ 2.000; tasas, cargos y calendario disponibles en contrato.")
    html = _html(at)
    assert "No encontramos señales de alerta" in html
    assert "no garantiza que la oferta sea segura" in html


def test_empty_input_shows_error(app):
    at = app.switch_page("views/analizar.py").run()
    next(b for b in at.button if b.label == "Revisar mensaje").click().run()
    assert "Pega el mensaje" in _html(at)
    assert "Pega el texto" in at.error[0].value


def test_example_pill_fills_text(app):
    at = app.switch_page("views/analizar.py").run()
    at.get("button_group")[0].set_value("Pago anticipado").run()
    assert at.text_area(key="offer_text").value.startswith("Deposita S/ 30")


def test_result_without_analysis(app):
    at = app.switch_page("views/resultado.py").run()
    assert "Aún no hay resultado" in _html(at)
    assert [b.label for b in at.button] == ["Revisar un mensaje"]


def test_guidance_page_lists_official_sources_and_contacts(app):
    at = _analyze(app, "Si no pagas hoy, tus familiares sabrán de tu deuda.")
    at.switch_page("views/orientacion.py").run()
    html = _html(at)
    assert not at.exception
    assert guidance.LABEL_INFO["amenaza_presion"].short in html
    for source in guidance.SOURCES.values():
        assert source.url in html
    assert 'href="tel:1818"' in html and 'href="tel:080010840"' in html
    assert 'href="mailto:informalidad@sbs.gob.pe"' in html


def test_guidance_without_result_shows_general_tips(app):
    at = app.switch_page("views/orientacion.py").run()
    html = _html(at)
    assert guidance.GENERAL_RECOMMENDATIONS[0] in html


def test_no_personal_data_fields(app):
    """US-05: ninguna vista pide DNI, contactos ni crea cuentas."""
    for page in ("inicio", "analizar", "resultado", "orientacion"):
        at = app.switch_page(f"views/{page}.py").run()
        assert len(at.text_input) == 0
        assert [t.key for t in at.text_area] in ([], ["offer_text"])
        assert len(at.get("file_uploader")) == 0


def test_model_unavailable_warning(monkeypatch):
    import ui_common
    from sipan.model import ModelUnavailable

    def _fail():
        raise ModelUnavailable("x")

    ui_common.get_model.clear()
    monkeypatch.setattr(ui_common, "load_model", _fail)
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.switch_page("views/analizar.py").run()
    assert "no está disponible" in at.warning[0].value
    ui_common.get_model.clear()


def test_user_html_is_escaped(app):
    at = _analyze(app, "<img src=x onerror=alert(1)> <b>Deposita</b> S/ 30 para liberar tu préstamo")
    html = _html(at)
    assert "<img src=x" not in html and "<b>Deposita" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html


def test_text_area_limit_matches_config(app):
    at = app.switch_page("views/analizar.py").run()
    assert at.text_area(key="offer_text").max_chars == config.MAX_TEXT_LENGTH
