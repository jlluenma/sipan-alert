import streamlit as st

from sipan.analyzer import Signal
from ui_common import PAGES, clear_analysis, escape_markdown, get_result

SOURCE_TEXT = {
    "modelo y reglas": "Modelo de Machine Learning y regla documentada",
    "modelo": "Modelo de Machine Learning",
    "reglas": "Regla documentada",
}
CONFIDENCE_TEXT = {
    "alta": "confianza alta",
    "media": "confianza media",
    "baja": "confianza baja",
    "regla": "coincidencia con una regla",
}
IDENTIFIER_NAMES = {
    "TELEFONO": "teléfono(s)", "DNI": "DNI", "CORREO": "correo(s)",
    "URL": "enlace(s)", "CUENTA": "cuenta(s) bancaria(s)",
}


def render_signal(signal: Signal, possible: bool = False) -> None:
    with st.container(border=True):
        icon = "❔" if possible else "⚠️"
        st.markdown(f"#### {icon} {signal.title}")
        st.write(signal.explanation)
        st.caption(f"Origen: {SOURCE_TEXT[signal.source]} · {CONFIDENCE_TEXT[signal.confidence]}")

        if signal.evidence:
            st.markdown("**Frase del mensaje que activó la señal:**")
            for phrase in signal.evidence:
                st.markdown(f"> {escape_markdown(phrase)}")

        with st.expander("Detalle técnico"):
            if signal.probability is not None:
                st.write(f"Probabilidad estimada por el modelo: {signal.probability:.0%} "
                         "(no es una certeza ni una probabilidad de fraude).")
            if signal.model_terms:
                st.write("Términos que más influyeron en el modelo: "
                         + ", ".join(f"«{t}»" for t in signal.model_terms))
            for description in signal.rule_descriptions:
                st.write(f"Regla: {description}")


result = get_result()
st.title("Resultado del análisis")

if result is None:
    st.info("Todavía no has analizado ningún mensaje.")
    if st.button("Analizar un mensaje", type="primary"):
        st.switch_page(PAGES["analizar"])
    st.stop()

if result.identifiers_hidden:
    hidden = ", ".join(f"{n} {IDENTIFIER_NAMES.get(k, k.lower())}"
                       for k, n in result.identifiers_hidden.items())
    st.caption(f"🔒 Antes de analizar ocultamos: {hidden}.")

if result.has_signals:
    count = len(result.signals)
    st.markdown(f"### Se {'observó' if count == 1 else 'observaron'} {count} "
                f"{'señal' if count == 1 else 'señales'} que conviene revisar")
    for signal in result.signals:
        render_signal(signal)
else:
    st.markdown("### No se observaron las señales definidas en el texto")

if result.possible_signals:
    st.markdown("#### Posibles señales (confianza baja)")
    st.caption("El modelo encontró indicios débiles. Revisa estos puntos con cuidado.")
    for signal in result.possible_signals:
        render_signal(signal, possible=True)

st.divider()
for notice in result.notices:
    st.info(notice)

col_guide, col_new = st.columns(2)
with col_guide:
    if st.button("Ver orientación", type="primary", icon=":material/support:", width="stretch"):
        st.switch_page(PAGES["orientacion"])
with col_new:
    if st.button("Analizar otro mensaje", icon=":material/refresh:", width="stretch"):
        clear_analysis()
        st.switch_page(PAGES["analizar"])
