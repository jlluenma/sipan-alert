import streamlit as st

from sipan import guidance
from ui_common import PAGES, get_result

st.title("Orientación preventiva")

result = get_result()
if result is not None and result.has_signals:
    st.markdown("### Para las señales observadas en tu mensaje")
    for signal in result.signals:
        with st.container(border=True):
            st.markdown(f"**{signal.title}**")
            for tip in signal.recommendations:
                st.markdown(f"- {tip}")
elif result is not None:
    st.info(guidance.NO_SIGNALS_NOTICE)

st.markdown("### Antes de aceptar cualquier préstamo")
for tip in guidance.GENERAL_RECOMMENDATIONS:
    st.markdown(f"- {tip}")

st.markdown("### Fuentes oficiales")
for source in guidance.SOURCES.values():
    st.markdown(f"- [{source.name}]({source.url}) — {source.description}")

st.markdown("### ¿A quién acudir?")
for contact in guidance.CONTACTS:
    st.markdown(f"- **{contact.name}: {contact.value}** — {contact.use}")

st.divider()
st.caption(guidance.LIMITS_NOTICE)

if result is None:
    if st.button("Analizar un mensaje", type="primary"):
        st.switch_page(PAGES["analizar"])
elif st.button("Volver al resultado", icon=":material/arrow_back:"):
    st.switch_page(PAGES["resultado"])
