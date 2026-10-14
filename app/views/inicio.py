import streamlit as st

import theme
from sipan import config
from sipan.analyzer import analyze
from sipan.preprocessing import InputError
from ui_common import EXAMPLES, PAGES, RESULT_KEY, TEXT_KEY, get_model

# Mensaje ficticio; los resaltados y las señales del ejemplo los produce el analizador de reglas.
DEMO = ("Tu crédito fue aprobado sin evaluación. Para recibirlo hoy debes depositar S/ 120 "
        "por gastos de activación. Solo por hoy.")
demo = analyze(DEMO, use_default_model=False)

with st.container(key="sa-hero-wrap"):
    st.html(
        '<section class="sa-hero" id="top">'
        '<p class="sa-hero__eyebrow">Prevención financiera inteligente</p>'
        '<h1>¿Recibiste una oferta de préstamo?</h1>'
        '<p class="sa-lead">Pega el texto de la oferta y revisa posibles riesgos. Revísalo antes de pagar o compartir tus datos.</p>'
        '</section>'
    )

    if get_model() is None:
        st.warning("El modelo de IA no está disponible. Revisaremos el mensaje solo con reglas.")

    with st.container(key="sa-hero-form"):
        st.text_area(
            "Texto de la oferta",
            key=TEXT_KEY,
            height=116,
            max_chars=config.MAX_TEXT_LENGTH,
            placeholder="Pega aquí el texto de la oferta…",
        )
        example_col, submit_col = st.columns([1, 1], vertical_alignment="center")
        with example_col:
            st.html('<a class="sa-example-link" href="#ejemplo-analisis">Ver un ejemplo ↗</a>')
        with submit_col:
            if st.button("Analizar oferta", type="primary", icon=":material/search:", width="stretch"):
                try:
                    st.session_state[RESULT_KEY] = analyze(
                        st.session_state[TEXT_KEY], model=get_model(), use_default_model=False
                    )
                except InputError as exc:
                    st.error(str(exc), icon=":material/edit_note:")
                else:
                    st.switch_page(PAGES["resultado"])
        st.html(
            f'<p class="sa-privacy">{theme.icon("lock")} No incluyas datos personales.</p>'
        )

st.html(theme.landing_sections(demo))

with st.container(key="sa-cta-footer"):
    with st.container(key="sa-cta"):
        text_col, button_col = st.columns([1, .3], vertical_alignment="center")
        with text_col:
            st.html(
                '<div class="sa-cta-row" id="que-hacer"><div>'
                '<h2>¿Tienes dudas sobre una oferta de préstamo?</h2>'
                '<p>Revisa sus posibles señales de riesgo antes de compartir información o realizar un pago.</p>'
                '</div></div>'
            )
        with button_col:
            st.page_link(PAGES["analizar"], label="Analizar oferta ↗")

    theme.render_footer(PAGES["inicio"], is_home=True)
