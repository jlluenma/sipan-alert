"""Entrada de la app Streamlit: streamlit run app/streamlit_app.py"""

import sys
from pathlib import Path

# Permite importar el paquete `sipan` sin instalarlo.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

import theme  # noqa: E402
from ui_common import PAGES, current_user, logout  # noqa: E402

st.set_page_config(
    page_title="SipánAlert IA",
    page_icon=str(ROOT / "app" / "assets" / "logo-icon.png"),
    layout="wide",
)
theme.inject_css()

user = current_user()
# El login es opcional (habilita funciones futuras como el historial). El
# analizador funciona sin sesión, así que el default es siempre Inicio.
pages = [
    st.Page(PAGES["inicio"], title="Inicio", icon=":material/home:", default=True),
    st.Page(PAGES["analizar"], title="Revisar mensaje", icon=":material/search:"),
    st.Page(PAGES["resultado"], title="Resultado", visibility="hidden"),
    st.Page(PAGES["orientacion"], title="Qué hacer", icon=":material/support:"),
    st.Page(PAGES["login"], title="Entrar", visibility="hidden"),
]
navigation = st.navigation(pages, position="hidden")
theme.navbar(
    PAGES["inicio"],
    PAGES["orientacion"],
    PAGES["login"],
    is_home=navigation.url_path == "",
    username=user.username if user else None,
    on_logout=logout if user else None,
)
navigation.run()
