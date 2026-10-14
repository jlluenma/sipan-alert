import streamlit as st

import theme
from sipan import config
from sipan.analyzer import analyze
from sipan.preprocessing import InputError
from ui_common import EXAMPLES, PAGES, RESULT_KEY, TEXT_KEY, get_model

st.session_state.setdefault(TEXT_KEY, "")


def _use_example() -> None:
    choice = st.session_state.get("example_choice")
    if choice:
        st.session_state[TEXT_KEY] = EXAMPLES[choice]


with st.container(key="sa-page-content"):
    theme.page_header("Pega el mensaje", "Cópialo tal cual desde WhatsApp, SMS o Facebook.")

    model = get_model()
    if model is None:
        st.warning("El modelo de IA no está disponible. Revisaremos el mensaje solo con reglas.")

    st.text_area(
        "Mensaje de la oferta",
        key=TEXT_KEY,
        height=180,
        max_chars=config.MAX_TEXT_LENGTH,
        placeholder="Ej.: Te prestamos S/ 1.000 al toque, solo deposita S/ 30 de trámite…",
        label_visibility="collapsed",
    )

    st.pills("¿No tienes uno a la mano? Prueba un ejemplo:", list(EXAMPLES),
             key="example_choice", on_change=_use_example)

    st.html(
        f'<p class="sa-privacy">{theme.icon("lock")}'
        "<span>No guardamos tu mensaje. Antes de revisarlo ocultamos teléfonos, DNI, correos y cuentas.</span></p>"
    )

    if st.button("Revisar mensaje", type="primary", icon=":material/search:"):
        try:
            st.session_state[RESULT_KEY] = analyze(
                st.session_state[TEXT_KEY], model=model, use_default_model=False
            )
        except InputError as exc:
            st.error(str(exc), icon=":material/edit_note:")
        else:
            st.switch_page(PAGES["resultado"])

theme.render_footer(PAGES["inicio"])
