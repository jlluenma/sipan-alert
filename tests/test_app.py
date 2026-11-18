"""Pruebas de la interfaz Streamlit (5 vistas: login + 4 vistas protegidas) con AppTest."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from sipan import config, guidance
from sipan.auth import AuthUser, upsert_user

APP = str(Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py")


@pytest.fixture(autouse=True)
def _app_on_path(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(APP).parent))


@pytest.fixture
def auth_db(monkeypatch, tmp_path):
    """SQLite temporal con un usuario de prueba, aislado por test."""
    db = tmp_path / "users.db"
    monkeypatch.setattr("sipan.auth.DB_PATH", db)
    upsert_user("tester", "clave-de-prueba", path=db)
    return db


def _primed_app(model, monkeypatch) -> AppTest:
    import ui_common

    ui_common.get_model.clear()
    monkeypatch.setattr(ui_common, "load_model", lambda: model)
    return AppTest.from_file(APP, default_timeout=60)


@pytest.fixture
def anon_app(model, monkeypatch, auth_db):
    """App sin sesión: la landing está abierta y «Entrar» es solo un enlace del navbar."""
    return _primed_app(model, monkeypatch).run()


@pytest.fixture
def app(model, monkeypatch, auth_db):
    """App con sesión ya iniciada como 'tester'. Reemplaza el fixture previo."""
    at = _primed_app(model, monkeypatch)
    at.session_state["auth_user"] = AuthUser(username="tester")
    return at.run()


def _html(at) -> str:
    return " ".join(e.proto.body for e in at.get("html"))


def _analyze(at, text):
    at.switch_page("views/analizar.py").run()
    at.text_area(key="offer_text").input(text).run()
    next(b for b in at.button if b.label == "Revisar mensaje").click().run()
    return at


# --- Flujo de autenticación (US-AUTH) ---

def test_anonymous_lands_on_home(anon_app):
    """Sin sesión la landing es accesible; «Entrar» queda como enlace del navbar."""
    assert not anon_app.exception
    assert "¿Recibiste una oferta de préstamo?" in _html(anon_app)
    # «Entrar» vive como page_link del navbar, no en el HTML inline.
    assert "Entrar" in [p.label for p in anon_app.get("page_link")]
    # La landing no pide credenciales ni texto del usuario.
    assert [t.key for t in anon_app.text_input] == []


def test_anonymous_can_analyze_offer(anon_app):
    """Login opcional: el analizador funciona sin iniciar sesión."""
    at = _analyze(anon_app, "Deposita S/ 30 para liberar tu préstamo de S/ 500.")
    assert not at.exception
    html = _html(at)
    assert "Encontramos" in html and "señal" in html
    assert guidance.LABEL_INFO["pago_anticipado"].short in html


def test_successful_login_goes_to_home(anon_app):
    at = anon_app.switch_page("views/login.py").run()
    at.text_input(key="login_username").input("tester").run()
    at.text_input(key="login_password").input("clave-de-prueba").run()
    next(b for b in at.button if b.label == "Entrar").click().run()
    assert not at.exception
    html = _html(at)
    assert "¿Recibiste una oferta de préstamo?" in html


def test_wrong_login_shows_error(anon_app):
    at = anon_app.switch_page("views/login.py").run()
    at.text_input(key="login_username").input("tester").run()
    at.text_input(key="login_password").input("mala-clave").run()
    next(b for b in at.button if b.label == "Entrar").click().run()
    assert any("incorrectos" in e.value.lower() for e in at.error)


def test_logout_clears_session(app):
    assert app.session_state.get("auth_user") is not None
    next(b for b in app.button if b.label == "Salir").click().run()
    assert app.session_state.get("auth_user") is None
    # Tras cerrar sesión el navbar vuelve a mostrar «Entrar» y el botón «Salir» desaparece.
    assert "Entrar" in [p.label for p in app.get("page_link")]
    assert "Salir" not in [b.label for b in app.button]


def test_navbar_shows_username_when_authenticated(app):
    html = _html(app)
    assert "tester" in html
    assert "sa-nav-user" in html


# --- Comportamiento ya existente (ahora con usuario autenticado) ---

def test_home_explains_with_highlighted_demo(app):
    assert not app.exception
    html = _html(app)
    assert "Revísalo antes de pagar" in html
    assert html.count('class="sa-mark"') == 2
    for label in ("pago_anticipado", "amenaza_presion", "condiciones_opacas"):
        assert guidance.LABEL_INFO[label].short in html
    assert guidance.LIMITS_SHORT in html
    labels = [b.label for b in app.button]
    assert "Analizar oferta" in labels
    assert "Salir" in labels


def test_home_form_analyzes_directly(app):
    app.text_area(key="offer_text").input("Deposita S/ 30 para liberar tu préstamo de S/ 500.").run()
    next(b for b in app.button if b.label == "Analizar oferta").click().run()
    assert not app.exception
    assert guidance.LABEL_INFO["pago_anticipado"].short in _html(app)


def test_footer_links_point_to_official_sources(app):
    html = _html(app)
    assert guidance.SOURCES["sbs_informalidad"].url in html
    assert guidance.SOURCES["mininter_gota"].url in html
    assert 'href="/orientacion"' in html


def test_analyze_flow_shows_verdict_highlights_and_limits(app):
    at = _analyze(app, "Deposita S/ 30 para liberar tu préstamo de S/ 500.")
    assert not at.exception
    html = _html(at)
    assert "Encontramos" in html and "señal" in html
    assert '<mark class="sa-mark"' in html
    assert guidance.LABEL_INFO["pago_anticipado"].short in html
    assert "Qué hacer:</strong> No deposites" in html
    assert guidance.LIMITS_SHORT in html


def test_result_shows_when_model_is_unavailable(monkeypatch, auth_db):
    import ui_common

    ui_common.get_model.clear()
    monkeypatch.setattr(ui_common, "load_model", lambda: None)
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["auth_user"] = AuthUser(username="tester")
    at = _analyze(at.run(), "Deposita S/ 30 para liberar tu préstamo.")
    assert guidance.MODEL_UNAVAILABLE_NOTICE in _html(at)
    ui_common.get_model.clear()


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
    html = _html(at)
    assert "Aún no hay resultado" in html
    assert "Revisar un mensaje" in [b.label for b in at.button]
    assert 'href="/#como-funciona"' in html


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
    """US-05 + US-AUTH: las vistas de análisis no piden datos personales.

    El formulario de login (tester y contraseña) no cuenta: no se pide DNI,
    correo ni teléfono. Verificado aparte.
    """
    for page in ("inicio", "analizar", "resultado", "orientacion"):
        at = app.switch_page(f"views/{page}.py").run()
        assert len(at.text_input) == 0, f"{page} no debe pedir texto plano al usuario"
        assert [t.key for t in at.text_area] in ([], ["offer_text"])
        assert len(at.get("file_uploader")) == 0


def test_login_form_only_asks_username_and_password(anon_app):
    """US-AUTH: el login no pide DNI, correo ni teléfono."""
    at = anon_app.switch_page("views/login.py").run()
    keys = [t.key for t in at.text_input]
    assert keys == ["login_username", "login_password"]
    assert len(at.text_area) == 0
    assert len(at.get("file_uploader")) == 0


def test_model_unavailable_warning(monkeypatch, auth_db):
    import ui_common
    from sipan.model import ModelUnavailable

    def _fail():
        raise ModelUnavailable("x")

    ui_common.get_model.clear()
    monkeypatch.setattr(ui_common, "load_model", _fail)
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["auth_user"] = AuthUser(username="tester")
    at = at.run()
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
