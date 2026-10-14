"""Entrada de la app Streamlit: streamlit run app/streamlit_app.py"""

import sys
from pathlib import Path

# Permite importar el paquete `sipan` sin instalarlo.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

import theme  # noqa: E402
from ui_common import PAGES  # noqa: E402

st.set_page_config(
    page_title="SipánAlert IA",
    page_icon=str(ROOT / "app" / "assets" / "logo-icon.png"),
    layout="wide",
)
theme.inject_css()

navigation = st.navigation(
    [
        st.Page(PAGES["inicio"], title="Inicio", icon=":material/home:", default=True),
        st.Page(PAGES["analizar"], title="Revisar mensaje", icon=":material/search:"),
        st.Page(PAGES["resultado"], title="Resultado", visibility="hidden"),
        st.Page(PAGES["orientacion"], title="Qué hacer", icon=":material/support:"),
    ],
    position="hidden",
)
theme.navbar(PAGES["inicio"], PAGES["orientacion"], is_home=navigation.url_path == "")
navigation.run()
