import json
import os

import streamlit as st

import theme
from sipan.faq import FOLLOW_UPS, TOPICS, answer, matching_topic
from sipan.gemini_faq import generate_answer
from sipan.guidance import LABEL_INFO, SOURCES
from sipan.preprocessing import anonymize
from ui_common import PAGES


with st.container(key="sa-page-content"):
    theme.page_header("Asistente SIPAN Alert")
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    use_gemini = bool(api_key) and st.checkbox("Usar Gemini para guiar el caso", value=True)
    if use_gemini:
        st.caption("Gemini activo. Google recibe la consulta y hasta tres turnos previos de Gemini. Evita incluir datos personales.")
    elif not api_key:
        st.caption("Modo guiado local. Gemini se activa cuando el servidor tiene GEMINI_API_KEY.")

    history = st.session_state.setdefault("faq_guided_turns", [])
    if history and st.button("Nueva conversación"):
        history.clear()

    if not history:
        with st.chat_message("assistant"):
            st.write("¿Qué pasó con la oferta de préstamo? Elige una situación o escribe tu pregunta.")
    for turn in history:
        with st.chat_message("user"):
            st.text(turn["question"])
        with st.chat_message("assistant"):
            if turn["fallback"]:
                st.caption("Gemini no está disponible. Respuesta del catálogo local.")
            st.markdown(turn["response"])

    previous = history[-1] if history else None
    topic = previous["topic"] if previous else None
    selected_question = None
    selected_response = None
    choices = previous["choices"] if previous and use_gemini else ()
    for index, choice in enumerate(choices):
        if st.button(choice, key=f"faq_gemini_choice_{index}"):
            selected_question = choice

    if topic and not choices:
        _, _, label, source_key = topic
        for index, (prompt, actions) in enumerate(FOLLOW_UPS[label]):
            if st.button(prompt, key=f"faq_followup_{label}_{index}"):
                selected_question = prompt
                selected_response = "\n".join(
                    f"- {LABEL_INFO[label].recommendations[action]}" for action in actions
                )
        source = SOURCES[source_key]
        st.link_button("Consultar fuente oficial", source.url)

    if topic is None or st.toggle("Elegir otro tema", key="faq_show_topics"):
        for index, (prompt, _, _, _) in enumerate(TOPICS):
            if st.button(prompt, key=f"faq_topic_{index}"):
                selected_question = prompt

    typed_question = st.chat_input("Escribe tu pregunta", max_chars=400)
    question = (typed_question or selected_question or "").strip()
    if question:
        safe_question = anonymize(question).text
        detected_topic = matching_topic(safe_question)
        turn_topic = (topic if selected_response else detected_topic) or topic
        response = selected_response
        attempted_gemini = use_gemini
        reply = None
        if attempted_gemini:
            context = [turn for turn in history if turn["gemini"]][-3:]
            conversation = [
                {"usuario": turn["question"], "asistente": turn["response"]}
                for turn in context
            ]
            conversation.append({"usuario": safe_question})
            with st.spinner("Gemini está revisando tu caso…"):
                reply = generate_answer(json.dumps(conversation, ensure_ascii=False), api_key)
        history.append({
            "question": safe_question,
            "response": reply.message if reply else response or answer(safe_question),
            "choices": reply.choices if reply else (),
            "topic": turn_topic,
            "fallback": attempted_gemini and reply is None,
            "gemini": reply is not None,
        })
        del history[:-10]
        st.rerun()

theme.render_footer(PAGES["inicio"])
