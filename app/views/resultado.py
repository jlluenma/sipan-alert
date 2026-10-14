import streamlit as st

import theme
from sipan import guidance
from ui_common import PAGES, clear_analysis, get_result

IDENTIFIER_NAMES = {
    "TELEFONO": ("teléfono", "teléfonos"), "DNI": ("DNI", "DNI"), "CORREO": ("correo", "correos"),
    "URL": ("enlace", "enlaces"), "CUENTA": ("cuenta", "cuentas"),
}

result = get_result()

if result is None:
    with st.container(key="sa-page-content"):
        theme.page_header("Aún no hay resultado", "Pega un mensaje para revisarlo.")
        if st.button("Revisar un mensaje", type="primary", icon=":material/search:"):
            st.switch_page(PAGES["analizar"])
    theme.render_footer(PAGES["inicio"])
    st.stop()

with st.container(key="sa-page-content"):
    theme.page_header("Resultado de tu revisión", "Revisa las señales identificadas antes de tomar una decisión.")

    hidden = ""
    if result.identifiers_hidden:
        items = ", ".join(f"{n} {IDENTIFIER_NAMES.get(k, (k.lower(),) * 2)[n != 1]}"
                          for k, n in result.identifiers_hidden.items())
        hidden = f'<p class="sa-hidden-ids">{theme.icon("lock")}Ocultamos {items} antes de revisar.</p>'

    st.html(
        theme.verdict(result)
        + theme.chat_bubble(result.analyzed_text, result.highlights, sender="Tu mensaje")
        + hidden
    )

    if result.signals:
        theme.section_title("Lo que encontramos")
        st.html("".join(theme.signal_card(s) for s in result.signals))

    if result.possible_signals:
        theme.section_title("Podría haber, revisa con cuidado")
        st.html("".join(theme.signal_card(s, possible=True) for s in result.possible_signals))

    col_guide, col_new = st.columns(2)
    with col_guide:
        if st.button("Ver qué hacer", type="primary", icon=":material/support:", width="stretch"):
            st.switch_page(PAGES["orientacion"])
    with col_new:
        if st.button("Revisar otro mensaje", icon=":material/refresh:", width="stretch"):
            clear_analysis()
            st.switch_page(PAGES["analizar"])

    hidden_notices = {guidance.LIMITS_NOTICE, guidance.NO_SIGNALS_NOTICE}
    extra = [
        notice for notice in result.notices
        if notice not in hidden_notices
        and not notice.startswith("El modelo de Machine Learning no está disponible en este momento")
    ]
    if extra:
        st.html(f'<p class="sa-fine">{" ".join(extra)}</p>')

theme.render_footer(PAGES["inicio"])
