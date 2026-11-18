"""Acceso y registro de cuentas para SipánAlert."""
from __future__ import annotations

import streamlit as st

import theme
from sipan.auth import AuthService, ROLE_ADMIN, ROLE_REVIEWER, current_user, sign_in, sign_out
from sipan.persistence.database import DatabaseNotConfigured
from sipan.services import AccountService
from ui_common import PAGES

with st.container(key="sa-page-content"):
    st.html(
        '<header class="sa-account-intro">'
        f'<span class="sa-account-intro__icon">{theme.icon("account_circle")}</span>'
        '<div><h1>Cuenta</h1><p>Accede para registrar tus aportes y consultar su estado.</p></div>'
        '</header>'
    )
    user = current_user()
    if user:
        st.success(f"Sesión iniciada como {user['email']}.")
        st.caption("Roles: " + ", ".join(user["roles"]))
        if ROLE_ADMIN in user["roles"]:
            st.info("Tienes acceso a la administración de cuentas, revisión humana y dataset evolutivo.")
            if st.button("Abrir panel de administración", type="primary", icon=":material/admin_panel_settings:"):
                st.switch_page(PAGES["aprendizaje"])
        elif ROLE_REVIEWER in user["roles"]:
            st.info("Tienes acceso a la bandeja de revisión humana.")
            if st.button("Abrir panel de revisión", type="primary", icon=":material/rule:"):
                st.switch_page(PAGES["aprendizaje"])
        history = AccountService().report_history(user["id"])
        st.subheader("Mis reportes")
        if history:
            st.dataframe(history, hide_index=True, width="stretch")
        else:
            st.caption("Aún no enviaste reportes para revisión.")
        with st.expander("Eliminar uno de mis reportes"):
            report_id = st.text_input("ID del reporte", key="account-delete-report")
            deletion_code = st.text_input("Código de eliminación", type="password", key="account-delete-code")
            if st.button("Eliminar mi reporte", key="account-delete-button"):
                if AccountService().delete_own_report(user["id"], report_id, deletion_code):
                    st.success("El contenido de tu reporte fue eliminado.")
                    st.rerun()
                else:
                    st.error("El ID o código no corresponde a uno de tus reportes.")
        if st.button("Cerrar sesión", type="secondary"):
            sign_out()
            st.rerun()
    else:
        with st.container(key="sa-account-card"):
            login_tab, register_tab = st.tabs(["Iniciar sesión", "Crear cuenta"])
            with login_tab:
                with st.form("login-form"):
                    email = st.text_input("Correo", placeholder="nombre@correo.com", autocomplete="email")
                    password = st.text_input("Contraseña", type="password", autocomplete="current-password")
                    submitted = st.form_submit_button("Ingresar", type="primary")
                if submitted:
                    try:
                        user = AuthService().authenticate(email, password)
                        if user is None:
                            st.error("Correo o contraseña incorrectos.")
                        else:
                            sign_in(user)
                            if ROLE_ADMIN in user["roles"] or ROLE_REVIEWER in user["roles"]:
                                st.switch_page(PAGES["aprendizaje"])
                            st.rerun()
                    except DatabaseNotConfigured as exc:
                        st.error(str(exc))
            with register_tab:
                with st.form("register-form"):
                    email = st.text_input("Correo para la cuenta", placeholder="nombre@correo.com", autocomplete="email")
                    password = st.text_input("Contraseña nueva", type="password", autocomplete="new-password")
                    confirmed = st.text_input("Repite la contraseña", type="password", autocomplete="new-password")
                    submitted = st.form_submit_button("Crear cuenta")
                if submitted:
                    if password != confirmed:
                        st.error("Las contraseñas no coinciden.")
                    else:
                        try:
                            sign_in(AuthService().register(email, password))
                            st.success("Cuenta creada.")
                            st.rerun()
                        except (ValueError, RuntimeError, DatabaseNotConfigured) as exc:
                            st.error(str(exc))

theme.render_footer(PAGES["inicio"])
