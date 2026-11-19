"""API que reutiliza el núcleo de SipánAlert sin depender de Streamlit."""
from __future__ import annotations

import os
import logging
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.exc import SQLAlchemyError

from sipan.analyzer import AnalysisResult, Signal, analyze
from sipan.auth import AuthService, ROLE_ADMIN, ROLE_REVIEWER
from sipan.faq import FOLLOW_UPS, TOPICS, answer, matching_topic
from sipan.gemini_faq import generate_answer
from sipan.guidance import LABEL_INFO, SOURCES
from sipan.novelty import compare_reviewed_reports, find_patterns
from sipan.persistence.database import DatabaseNotConfigured
from sipan.preprocessing import InputError
from sipan.services import AccountService, LearningService, ReportService

app = FastAPI(title="SipánAlert API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SIPAN_SESSION_SECRET", "sipanalert-local-development-only"),
    same_site="lax",
    https_only=False,
)


class Credentials(BaseModel):
    email: str
    password: str = Field(min_length=10)
    name: str | None = Field(default=None,max_length=80)


class AnalysisInput(BaseModel):
    text: str = Field(max_length=3000)


class ReportInput(BaseModel):
    text: str = Field(max_length=3000)
    consent: bool


class ReviewInput(BaseModel):
    decision: Literal["validado", "rechazado"]
    labels: dict[str, int]
    note: str = Field(default="", max_length=2000)


class ChatInput(BaseModel):
    question: str = Field(min_length=3, max_length=400)
    topic: str | None = None


class DuplicateInput(BaseModel):
    original_id: str


class RoleInput(BaseModel):
    role: Literal["usuario", "revisor", "administrador"]


class AccountUpdate(BaseModel):
    roles: list[Literal["usuario", "revisor", "administrador"]]
    active: bool


class DeleteInput(BaseModel):
    deletion_code: str = Field(min_length=1)


def _http_database_error(exc: DatabaseNotConfigured) -> HTTPException:
    return HTTPException(status_code=503, detail=str(exc))


def current_user(request: Request) -> dict:
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inicia sesión para continuar.")
    return user


def reviewer(user: dict = Depends(current_user)) -> dict:
    if not set(user["roles"]).intersection({ROLE_REVIEWER, ROLE_ADMIN}):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso al panel de revisión.")
    return user


def administrator(user: dict = Depends(current_user)) -> dict:
    if ROLE_ADMIN not in user["roles"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo un administrador puede realizar esta acción.")
    return user


from api.community import community_router
app.include_router(community_router(current_user, reviewer))


def _signal(signal: Signal) -> dict:
    return {
        "label": signal.label,
        "title": signal.title,
        "explanation": signal.explanation,
        "source": signal.source,
        "confidence": signal.confidence,
        "probability": signal.probability,
        "evidence": signal.evidence,
        "recommendations": signal.recommendations,
    }


def _analysis(result: AnalysisResult) -> dict:
    return {
        "signals": [_signal(signal) for signal in result.signals],
        "possibleSignals": [_signal(signal) for signal in result.possible_signals],
        "modelAvailable": result.model_available,
        "modelVersion": result.model_version,
        "identifiersHidden": result.identifiers_hidden,
        "notices": result.notices,
        "analyzedText": result.analyzed_text,
        "highlights": [{"start": h.start, "end": h.end, "label": h.label} for h in result.highlights],
    }


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(credentials: Credentials, request: Request) -> dict:
    try:
        user = AuthService().register(credentials.email, credentials.password, credentials.name)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except DatabaseNotConfigured as exc:
        raise _http_database_error(exc) from exc
    request.session["user"] = user
    return user


@app.post("/api/auth/login")
def login(credentials: Credentials, request: Request) -> dict:
    try:
        user = AuthService().authenticate(credentials.email, credentials.password)
    except DatabaseNotConfigured as exc:
        raise _http_database_error(exc) from exc
    if user is None:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos.")
    request.session["user"] = user
    return user


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request) -> None:
    request.session.clear()


@app.get("/api/auth/me")
def me(user: dict = Depends(current_user)) -> dict:
    return user


@app.post("/api/analyze")
def analyze_offer(payload: AnalysisInput, _: dict = Depends(current_user)) -> dict:
    try:
        from sipan.verification import verification_checks
        result = _analysis(analyze(payload.text))
        result['verification'] = verification_checks(payload.text)
        try:
            reports = LearningService().list_reports("validado")
            result["similarReports"] = compare_reviewed_reports(result["analyzedText"], reports)
        except (DatabaseNotConfigured, SQLAlchemyError):
            logging.getLogger(__name__).warning("No se pudo consultar la similitud con reportes revisados.")
            result["similarReports"] = None
        return result
    except InputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post('/api/verification/search')
def verification_search(payload: AnalysisInput, _:dict=Depends(current_user)):
    from sipan.web_verification import search_official_sources
    return search_official_sources(payload.text)


class EntityQuery(BaseModel):
    query: str = Field(min_length=3, max_length=120)


@app.post('/api/investigation')
def investigation(payload: EntityQuery):
    from sipan.entity_investigation import investigate_entity
    return {"entities": investigate_entity(payload.query)}


@app.post('/api/investigation/news')
def investigation_news(payload: EntityQuery, _: dict = Depends(current_user)):
    from sipan.web_verification import search_official_sources
    return search_official_sources(payload.query, entity_news=True)


@app.post("/api/chat")
def chat(payload: ChatInput) -> dict:
    """Asistente preventivo: Gemini si está configurado, catálogo local si no."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    reply = generate_answer(payload.question, api_key) if api_key else None
    topic = matching_topic(payload.question)
    previous = next((item for item in TOPICS if item[2] == payload.topic), None)
    follow_up = None
    # Follow-up buttons have explicit catalog actions, not keyword answers.
    for candidate in ([previous] if previous else list(TOPICS)):
        for prompt, actions in FOLLOW_UPS[candidate[2]]:
            if payload.question == prompt:
                topic = candidate
                follow_up = '\n'.join('- ' + LABEL_INFO[candidate[2]].recommendations[index] for index in actions)
                break
    choices = list(reply.choices) if reply else [item[0] for item in FOLLOW_UPS[topic[2]]] if topic else [item[0] for item in TOPICS]
    return {
        "message": follow_up or (reply.message if reply else answer(payload.question)),
        "choices": choices,
        "provider": "gemini" if reply else "local",
        "topic": topic[2] if topic else payload.topic,
        "sourceUrl": SOURCES[topic[3]].url if topic else None,
        "sourceName": SOURCES[topic[3]].name if topic else None,
    }


@app.get("/api/chat/topics")
def chat_topics() -> dict:
    return {"message": "¿Qué pasó con la oferta de préstamo? Elige una situación o escribe tu pregunta.",
            "choices": [item[0] for item in TOPICS]}


@app.post("/api/reports", status_code=status.HTTP_201_CREATED)
def submit_report(payload: ReportInput, user: dict = Depends(current_user)) -> dict:
    if not payload.consent:
        raise HTTPException(status_code=400, detail="Necesitamos tu consentimiento para guardar el reporte.")
    try:
        result = analyze(payload.text)
        probabilities = {
            signal.label: signal.probability
            for signal in (*result.signals, *result.possible_signals)
            if signal.probability is not None
        }
        report_id, deletion_code, duplicate_of = ReportService().submit(
            result.analyzed_text, probabilities, result.model_version, user["id"]
        )
    except (InputError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DatabaseNotConfigured as exc:
        raise _http_database_error(exc) from exc
    return {"id": report_id, "deletionCode": deletion_code, "duplicateOf": duplicate_of}


@app.get("/api/reports/mine")
def my_reports(user: dict = Depends(current_user)) -> list[dict]:
    try:
        return AccountService().report_history(user["id"])
    except DatabaseNotConfigured as exc:
        raise _http_database_error(exc) from exc


@app.post("/api/reports/{report_id}/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_own_report(report_id: str, payload: DeleteInput, user: dict = Depends(current_user)) -> None:
    try:
        if not AccountService().delete_own_report(user["id"], report_id, payload.deletion_code):
            raise HTTPException(status_code=404, detail="El ID o código no corresponde a uno de tus reportes.")
    except DatabaseNotConfigured as exc:
        raise _http_database_error(exc) from exc


@app.get("/api/review/reports")
def review_reports(_: dict = Depends(reviewer)) -> list[dict]:
    try:
        return LearningService().list_reports()
    except DatabaseNotConfigured as exc:
        raise _http_database_error(exc) from exc


@app.get("/api/review/patterns")
def emerging_patterns(_: dict = Depends(reviewer)) -> list[dict]:
    try:
        return find_patterns(LearningService().list_reports())
    except DatabaseNotConfigured as exc:
        raise _http_database_error(exc) from exc


@app.post("/api/review/reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def review_report(report_id: str, payload: ReviewInput, user: dict = Depends(reviewer)) -> None:
    try:
        ReportService().review(report_id, payload.decision, payload.labels, payload.note, user["id"])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/review/reports/{report_id}/duplicate", status_code=status.HTTP_204_NO_CONTENT)
def duplicate_report(report_id: str, payload: DuplicateInput, _: dict = Depends(reviewer)) -> None:
    try:
        ReportService().mark_duplicate(report_id, payload.original_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/review/dataset")
def create_dataset(_: dict = Depends(administrator)) -> dict:
    try:
        return LearningService().create_dataset_version()
    except DatabaseNotConfigured as exc:
        raise _http_database_error(exc) from exc


@app.get("/api/admin/users")
def users(_: dict = Depends(administrator)) -> list[dict]:
    try:
        return AuthService().users()
    except DatabaseNotConfigured as exc:
        raise _http_database_error(exc) from exc


@app.post("/api/admin/users", status_code=201)
def create_account(payload: Credentials, _: dict = Depends(administrator)) -> dict:
    try:
        return AuthService().register(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/admin/users/{email}/update", status_code=204)
def update_account(email: str, payload: AccountUpdate, actor: dict = Depends(administrator)) -> None:
    try:
        AuthService().update_account(email, payload.roles, payload.active, actor['id'])
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/admin/users/{email}/role", status_code=status.HTTP_204_NO_CONTENT)
def grant_role(email: str, payload: RoleInput, _: dict = Depends(administrator)) -> None:
    try:
        AuthService().grant_role(email, payload.role)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
