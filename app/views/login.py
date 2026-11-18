import streamlit as st

import theme
from sipan.auth import authenticate
from ui_common import AUTH_KEY, PAGES

if st.session_state.get(AUTH_KEY):
    st.switch_page(PAGES["inicio"])

with st.container(key="sa-page-content"):
    theme.page_header("Entrar", "Usa el usuario que te asignó el equipo.")

    username = st.text_input("Usuario", key="login_username")
    password = st.text_input("Contraseña", key="login_password", type="password")

    if st.button("Entrar", type="primary", icon=":material/login:"):
        user = authenticate(username, password)
        if user is None:
            st.error("Usuario o contraseña incorrectos.", icon=":material/error:")
        else:
            st.session_state[AUTH_KEY] = user
            st.rerun()

    st.html(
        f'<p class="sa-privacy">{theme.icon("lock")}'
        "<span>Guardamos solo el nombre de usuario y un hash de la contraseña. "
        "El texto que analizas no se guarda.</span></p>"
    )

theme.render_footer(PAGES["inicio"])
