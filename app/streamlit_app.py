"""Entrada de la app Streamlit: streamlit run app/streamlit_app.py"""

import sys
from pathlib import Path

# Permite importar el paquete `sipan` sin instalarlo.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

from sipan import guidance  # noqa: E402
from ui_common import PAGES  # noqa: E402

st.set_page_config(page_title="SipánAlert IA", page_icon="🛡️", layout="centered")

navigation = st.navigation([
    st.Page(PAGES["inicio"], title="Inicio", icon=":material/home:", default=True),
    st.Page(PAGES["analizar"], title="Analizar mensaje", icon=":material/edit_note:"),
    st.Page(PAGES["resultado"], title="Resultado", icon=":material/fact_check:"),
    st.Page(PAGES["orientacion"], title="Orientación", icon=":material/support:"),
])

with st.sidebar:
    st.markdown("**SipánAlert IA**")
    st.caption(guidance.LIMITS_NOTICE)
    st.caption("No pedimos cuenta, DNI ni contactos. El texto que pegas no se guarda.")

navigation.run()
