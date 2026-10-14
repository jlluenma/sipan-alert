import streamlit as st

import theme
from sipan import guidance
from ui_common import PAGES, get_result

result = get_result()

with st.container(key="sa-page-content"):
    theme.page_header("Qué hacer ahora")

    if result is not None and result.has_signals:
        theme.section_title("Para tu mensaje")
        st.html(theme.tips_by_signal(result.signals))
    else:
        theme.section_title("Antes de aceptar un préstamo")
        st.html(theme.checklist(guidance.GENERAL_RECOMMENDATIONS))

    theme.section_title("¿Necesitas ayuda? Llama o escribe")
    st.html(theme.contact_cards())

    theme.section_title("Fuentes oficiales")
    st.html(theme.source_links())

    if result is None:
        if st.button("Revisar un mensaje", type="primary", icon=":material/search:"):
            st.switch_page(PAGES["analizar"])
    elif st.button("Volver al resultado", icon=":material/arrow_back:"):
        st.switch_page(PAGES["resultado"])

    st.html(f'<p class="sa-fine">{guidance.LIMITS_NOTICE}</p>')

theme.render_footer(PAGES["inicio"])
