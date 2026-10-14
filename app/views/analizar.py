import streamlit as st

from sipan import config
from sipan.analyzer import analyze
from sipan.preprocessing import InputError
from ui_common import EXAMPLES, PAGES, RESULT_KEY, TEXT_KEY, get_model

st.session_state.setdefault(TEXT_KEY, "")


def _use_example() -> None:
    st.session_state[TEXT_KEY] = EXAMPLES[st.session_state["example_choice"]]


st.title("Analizar mensaje")
st.write("Copia y pega el texto de la oferta de préstamo que recibiste.")

st.info(
    "🔒 No necesitas crear una cuenta ni dar tu DNI o contactos. "
    "El texto se analiza en el momento y **no se guarda**. "
    "Teléfonos, DNI, correos, enlaces y cuentas se ocultan antes del análisis.",
)

model = get_model()
if model is None:
    st.warning(
        "El modelo de Machine Learning no está disponible. "
        "El análisis usará solo reglas documentadas."
    )

with st.expander("¿No tienes un mensaje a la mano? Usa un ejemplo ficticio"):
    st.selectbox("Ejemplo", list(EXAMPLES), key="example_choice")
    st.button("Usar este ejemplo", on_click=_use_example)

st.text_area(
    "Texto de la oferta",
    key=TEXT_KEY,
    height=200,
    max_chars=config.MAX_TEXT_LENGTH,
    placeholder="Ej.: «Te prestamos S/ 1.000 al toque, solo deposita S/ 30 de trámite…»",
)

if st.button("Analizar", type="primary", icon=":material/search:"):
    try:
        st.session_state[RESULT_KEY] = analyze(
            st.session_state[TEXT_KEY], model=model, use_default_model=False
        )
    except InputError as exc:
        st.error(str(exc))
    else:
        st.switch_page(PAGES["resultado"])
