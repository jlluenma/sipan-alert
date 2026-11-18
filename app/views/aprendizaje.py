"""Panel local de revisión para el piloto de aprendizaje continuo."""

from __future__ import annotations

import streamlit as st

import theme
from sipan import config, guidance
from sipan.novelty import find_patterns
from sipan.persistence.database import DatabaseNotConfigured
from sipan.services import LearningService
from sipan.auth import AuthService, ROLE_ADMIN, ROLE_REVIEWER, ROLE_USER, require_role
from ui_common import PAGES


def _labels_editor(report: dict) -> dict[str, int]:
    predicted = report["prediction"]
    st.caption("Marca las señales observadas en el texto. Esta decisión queda registrada.")
    return {
        label: int(st.checkbox(guidance.LABEL_INFO[label].short,
                               value=bool(predicted.get(label, 0) >= 0.5), key=f"{report['id']}-{label}"))
        for label in config.LABELS
    }


try:
    reviewer = require_role(ROLE_REVIEWER, ROLE_ADMIN)
except PermissionError as exc:
    st.error(str(exc))
    st.stop()

service = LearningService()
try:
    reports = service.list_reports()
except DatabaseNotConfigured as exc:
    st.error(str(exc))
    st.stop()
pending = [report for report in reports if report["status"] == "pendiente"]
validated = [report for report in reports if report["status"] == "validado"]
rejected = [report for report in reports if report["status"] == "rechazado"]

with st.container(key="sa-page-content"):
    panel_title = "Panel de administración" if ROLE_ADMIN in reviewer["roles"] else "Panel de revisión humana"
    theme.page_header(panel_title, "Revisa aportes consentidos y prepara datasets reproducibles con control humano.")
    first, second, third = st.columns(3)
    first.metric("Pendientes", len(pending))
    second.metric("Validados", len(validated))
    third.metric("Rechazados", len(rejected))

    theme.section_title("Posibles patrones emergentes")
    patterns = find_patterns(reports)
    if not patterns:
        st.info("Aún no hay dos aportes suficientemente similares para formar un grupo candidato.")
    for pattern in patterns:
        st.markdown(
            f"**{pattern['id']}** · {pattern['count']} aportes · similitud media {pattern['similarity']:.0%}  \n"
            f"Términos frecuentes: {', '.join(pattern['common_terms']) or 'sin términos representativos'}"
        )
        st.caption("Es una agrupación estadística para revisión. No confirma una modalidad ni atribuye responsabilidad.")

    theme.section_title("Bandeja de revisión")
    if pending:
        choices = {f"{report['id']} · {report['received_at']}": report for report in pending}
        selected = choices[st.selectbox("Aporte pendiente", list(choices))]
        st.text_area("Texto compartido", selected["content"], disabled=True, key=f"content-{selected['id']}")
        labels = _labels_editor(selected)
        note = st.text_area("Observación o justificación", key=f"note-{selected['id']}")
        action_col, duplicate_col = st.columns(2)
        with action_col:
            if st.button("Validar etiquetas", type="primary", key=f"validate-{selected['id']}"):
                service.reports.review(selected["id"], "validado", labels, note, reviewer["id"])
                st.rerun()
            if st.button("Rechazar o dejar insuficiente", key=f"reject-{selected['id']}"):
                service.reports.review(selected["id"], "rechazado", labels, note or "Información insuficiente o aporte irrelevante.", reviewer["id"])
                st.rerun()
        with duplicate_col:
            candidates = [report["id"] for report in reports if report["id"] != selected["id"]]
            duplicate_of = st.selectbox("Marcar como duplicado de", ["Elegir aporte", *candidates], key=f"duplicate-{selected['id']}")
            if st.button("Registrar duplicado", disabled=duplicate_of == "Elegir aporte", key=f"duplicate-button-{selected['id']}"):
                service.reports.mark_duplicate(selected["id"], duplicate_of)
                st.rerun()
    else:
        st.info("No hay aportes pendientes de revisión.")

    theme.section_title("Dataset evolutivo")
    st.caption("La exportación contiene solo aportes validados, sin duplicados. Los casos pendientes y rechazados quedan fuera.")
    if st.button("Crear versión del dataset", disabled=not validated):
        manifest = service.create_dataset_version()
        st.success(f"Versión {manifest['version']} creada con {manifest['eligible_reports']} aportes validados.")
        st.json(manifest)

    if ROLE_ADMIN in reviewer["roles"]:
        theme.section_title("Administración de cuentas")
        users = AuthService().users()
        accounts = {f"{account['email']} · {', '.join(account['roles'])}": account for account in users}
        if accounts:
            selected_account = accounts[st.selectbox("Cuenta", list(accounts), key="role-account")]
            role = st.selectbox("Agregar rol", [ROLE_USER, ROLE_REVIEWER, ROLE_ADMIN], key="role-name")
            if st.button("Asignar rol", key="grant-role"):
                AuthService().grant_role(selected_account["email"], role)
                st.success("Rol asignado.")
                st.rerun()

    with st.expander("Eliminar un aporte mediante su código"):
        report_id = st.text_input("ID del aporte", key="delete-report-id")
        deletion_code = st.text_input("Código de eliminación", type="password", key="delete-report-code")
        if st.button("Eliminar aporte", key="delete-report"):
            if service.reports.delete(report_id, deletion_code):
                st.success("El contenido del aporte fue eliminado.")
                st.rerun()
            else:
                st.error("El ID o el código de eliminación no son válidos.")

theme.render_footer(PAGES["inicio"])
