"""Acceso voluntario antes de enviar un mensaje al analizador."""
from __future__ import annotations

import streamlit as st

from sipan.auth import AuthService, current_user, sign_in
from sipan.persistence.database import DatabaseNotConfigured


def require_login_to_analyze(location: str) -> bool:
    """Muestra el acceso bajo demanda y devuelve si se puede usar el analizador."""
    if current_user():
        return True

    visible_key = f"login-required-{location}"
    if not st.session_state.get(visible_key):
        st.text_area(
            "Mensaje de la oferta",
            height=180,
            placeholder="Inicia sesión para pegar el mensaje y revisarlo.",
            disabled=True,
            label_visibility="collapsed",
            key=f"disabled-message-{location}",
        )
        if st.button("Iniciar sesión para escribir", icon=":material/login:", key=f"open-login-{location}"):
            st.session_state[visible_key] = True
            st.rerun()
        return False

    with st.container(key="sa-account-card"):
        st.subheader("Accede para analizar el mensaje")
        st.caption("Tu cuenta permite conservar tus aportes y consultar su estado.")
        login_tab, register_tab = st.tabs(["Iniciar sesión", "Crear cuenta"])
        with login_tab:
            with st.form(f"login-form-{location}"):
                email = st.text_input("Correo", placeholder="nombre@correo.com", autocomplete="email", key=f"login-email-{location}")
                password = st.text_input("Contraseña", type="password", autocomplete="current-password", key=f"login-password-{location}")
                submitted = st.form_submit_button("Ingresar", type="primary")
            if submitted:
                try:
                    user = AuthService().authenticate(email, password)
                    if user is None:
                        st.error("Correo o contraseña incorrectos.")
                    else:
                        sign_in(user)
                        st.session_state.pop(visible_key, None)
                        st.rerun()
                except DatabaseNotConfigured as exc:
                    st.error(str(exc))
        with register_tab:
            with st.form(f"register-form-{location}"):
                email = st.text_input("Correo para la cuenta", placeholder="nombre@correo.com", autocomplete="email", key=f"register-email-{location}")
                password = st.text_input("Contraseña nueva", type="password", autocomplete="new-password", key=f"register-password-{location}")
                confirmed = st.text_input("Repite la contraseña", type="password", autocomplete="new-password", key=f"register-confirmed-{location}")
                submitted = st.form_submit_button("Crear cuenta")
            if submitted:
                if password != confirmed:
                    st.error("Las contraseñas no coinciden.")
                else:
                    try:
                        sign_in(AuthService().register(email, password))
                        st.session_state.pop(visible_key, None)
                        st.rerun()
                    except (ValueError, RuntimeError, DatabaseNotConfigured) as exc:
                        st.error(str(exc))
    return False
