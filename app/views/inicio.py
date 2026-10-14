import streamlit as st

from sipan import guidance
from ui_common import PAGES

st.title("🛡️ SipánAlert IA")
st.markdown(
    "#### Revisa una oferta de préstamo **antes** de responder, pagar o compartir tus datos."
)
st.write(
    "Pega el mensaje que recibiste por WhatsApp, SMS o redes sociales. "
    "SipánAlert IA busca señales que conviene revisar y te orienta con fuentes oficiales."
)

if st.button("Analizar una oferta", type="primary", icon=":material/arrow_forward:"):
    st.switch_page(PAGES["analizar"])

st.divider()

col_does, col_not, col_privacy = st.columns(3)
with col_does:
    st.markdown("**Qué hace**")
    st.markdown(
        "- Busca señales de riesgo en el texto\n"
        "- Explica por qué aparece cada señal\n"
        "- Sugiere qué verificar y dónde"
    )
with col_not:
    st.markdown("**Qué no hace**")
    st.markdown(
        "- No acusa a nadie de fraude\n"
        "- No certifica que un prestamista sea legítimo\n"
        "- No reemplaza a la SBS ni a la Policía"
    )
with col_privacy:
    st.markdown("**Tu privacidad**")
    st.markdown(
        "- Sin cuenta ni registro\n"
        "- No pedimos DNI ni contactos\n"
        "- El texto no se guarda"
    )

st.divider()
st.markdown("**Señales que analiza**")
for info in guidance.LABEL_INFO.values():
    st.markdown(f"- {info.title}")

st.caption(guidance.LIMITS_NOTICE)
