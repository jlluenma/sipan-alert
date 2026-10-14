import streamlit as st

import theme
from sipan import guidance
from sipan.analyzer import analyze
from ui_common import PAGES

# Mensaje ficticio; los resaltados los produce el analizador real (solo reglas).
DEMO = ("¡Hola! Te prestamos S/ 1.000 hoy mismo. Deposita S/ 30 de trámite para recibirlo. "
        "Autoriza el acceso a tus contactos en la app. Solo por hoy.")
demo = analyze(DEMO, use_default_model=False)

st.html(
    '<section class="sa-hero">'
    "<h1>¿Te ofrecieron un préstamo por chat? Revísalo antes de pagar.</h1>"
    '<p class="sa-lead">Pega el mensaje y te marcamos lo que debes revisar.</p>'
    + theme.chat_bubble(demo.analyzed_text, demo.highlights, sender="Ejemplo de mensaje ficticio")
    + "</section>"
)

if st.button("Revisar un mensaje", type="primary", icon=":material/search:"):
    st.switch_page(PAGES["analizar"])

st.html(
    '<ol class="sa-steps">'
    "<li><b>1</b><span>Pega el mensaje que recibiste</span></li>"
    "<li><b>2</b><span>Marcamos las señales de alerta</span></li>"
    "<li><b>3</b><span>Te decimos qué hacer y a quién llamar</span></li>"
    "</ol>"
    '<ul class="sa-trust">'
    f"<li>{theme.icon('lock')}No guardamos tu mensaje</li>"
    f"<li>{theme.icon('person_off')}Sin registro ni DNI</li>"
    f"<li>{theme.icon('volunteer_activism')}Gratis</li>"
    "</ul>"
    f'<p class="sa-fine">{guidance.LIMITS_SHORT} Prototipo académico de la UTP Chiclayo.</p>'
)
