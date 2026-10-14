"""Pruebas de la interfaz Streamlit (4 vistas) con AppTest, sin navegador."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from sipan import config, guidance

APP = str(Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py")


@pytest.fixture
def app(model, monkeypatch):
    # La app usa el modelo del fixture (entrenado en temporal), no models/.
    import ui_common

    ui_common.get_model.clear()
    monkeypatch.setattr(ui_common, "load_model", lambda: model)
    return AppTest.from_file(APP, default_timeout=60).run()


@pytest.fixture(autouse=True)
def _app_on_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(APP).parent))


def _texts(at):
    return " ".join(str(e.value) for e in [*at.markdown, *at.info, *at.caption, *at.error, *at.title])


def _analyze(at, text):
    at.switch_page("views/analizar.py").run()
    at.text_area(key="offer_text").input(text).run()
    next(b for b in at.button if b.label == "Analizar").click().run()
    return at


def test_home_page(app):
    assert not app.exception
    assert app.title[0].value == "🛡️ SipánAlert IA"
    assert "No acusa a nadie de fraude" in _texts(app)


def test_analyze_flow_shows_signal_and_limits(app):
    at = _analyze(app, "Deposita S/ 30 para liberar tu préstamo de S/ 500.")
    assert not at.exception
    assert at.title[0].value == "Resultado del análisis"
    texts = _texts(at)
    assert guidance.LABEL_INFO["pago_anticipado"].title in texts
    assert guidance.LIMITS_NOTICE in texts


def test_empty_input_shows_error(app):
    at = app.switch_page("views/analizar.py").run()
    next(b for b in at.button if b.label == "Analizar").click().run()
    assert at.title[0].value == "Analizar mensaje"
    assert "Pega el texto" in at.error[0].value


def test_example_button_fills_text(app):
    at = app.switch_page("views/analizar.py").run()
    next(b for b in at.button if b.label == "Usar este ejemplo").click().run()
    assert at.text_area(key="offer_text").value


def test_result_without_analysis(app):
    at = app.switch_page("views/resultado.py").run()
    assert "Todavía no has analizado" in _texts(at)


def test_guidance_page_lists_official_sources_and_contacts(app):
    at = _analyze(app, "Si no pagas hoy, tus familiares sabrán de tu deuda.")
    at.switch_page("views/orientacion.py").run()
    texts = _texts(at)
    assert not at.exception
    assert guidance.LABEL_INFO["amenaza_presion"].title in texts
    for source in guidance.SOURCES.values():
        assert source.url in texts
    assert "1818" in texts and "0-800-10840" in texts


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


def test_user_markdown_is_escaped(app):
    at = _analyze(app, "**Deposita** S/ 30 ![x](http://a.b/c.png) para liberar tu préstamo")
    quotes = [m.value for m in at.markdown if m.value.startswith(">")]
    # La oración se corta en "!", así que la evidencia empieza en "[x](...".
    assert quotes and all("\\[x\\]\\(" in q for q in quotes)


def test_text_area_limit_matches_config(app):
    at = app.switch_page("views/analizar.py").run()
    assert at.text_area(key="offer_text").max_chars == config.MAX_TEXT_LENGTH
