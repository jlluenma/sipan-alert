import streamlit as st

import theme
from sipan import config, guidance
from sipan.persistence.database import DatabaseNotConfigured
from sipan.services import ReportService
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

    theme.section_title("¿Quieres aportar este mensaje para mejorar el sistema?")
    st.caption("Solo se guarda si das tu consentimiento. Revisa y elimina nombres u otros datos personales antes de compartirlo.")
    share_text = st.text_area(
        "Texto anonimizado que compartirás", value=result.analyzed_text, max_chars=config.MAX_TEXT_LENGTH,
        key="voluntary_report_text",
    )
    consent = st.checkbox(
        "Autorizo guardar este texto anonimizado para revisión humana y mejora futura del sistema.",
        key="voluntary_report_consent",
    )
    if st.button("Compartir para revisión", icon=":material/volunteer_activism:", disabled=not consent):
        probabilities = {signal.label: signal.probability for signal in result.signals + result.possible_signals
                         if signal.probability is not None}
        try:
            report_id, deletion_code, duplicate_of = ReportService().submit(
                share_text, probabilities, result.model_version,
            )
        except (ValueError, DatabaseNotConfigured) as exc:
            st.error(str(exc))
        else:
            st.success("Recibimos el aporte para revisión humana.")
            st.code(f"ID del aporte: {report_id}\nCódigo de eliminación: {deletion_code}", language=None)
            st.warning("Guarda el código de eliminación. SipánAlert no podrá mostrarlo otra vez.")
            if duplicate_of:
                st.info(f"Detectamos que puede ser similar a un aporte anterior ({duplicate_of}). Un revisor decidirá si corresponde marcarlo como duplicado.")

    col_guide, col_new = st.columns(2)
    with col_guide:
        if st.button("Ver qué hacer", type="primary", icon=":material/support:", width="stretch"):
            st.switch_page(PAGES["orientacion"])
    with col_new:
        if st.button("Revisar otro mensaje", icon=":material/refresh:", width="stretch"):
            clear_analysis()
            st.switch_page(PAGES["analizar"])

    extra = [n for n in result.notices if n not in (guidance.LIMITS_NOTICE, guidance.NO_SIGNALS_NOTICE)]
    st.html(f'<p class="sa-fine">{" ".join([guidance.LIMITS_SHORT, *extra])}</p>')

theme.render_footer(PAGES["inicio"])
