import json
import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from config import CHROMA_DB_DIR, DATA_JSON_FILES
from infrastructure.create_db import create_database
from application.workflow import Workflow
from infrastructure.agents import chat_response
from shared.i18n import t
from shared.utils import to_int, slugify_crop

load_dotenv(override=True)

# ── helpers ──────────────────────────────────────────────────────────────────


def is_db_ready() -> bool:
    db_path = Path(CHROMA_DB_DIR)
    return db_path.exists() and any(db_path.iterdir())


def load_crop_options(lang: str) -> dict[str, str]:
    options: dict[str, str] = {}
    for path in DATA_JSON_FILES:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        crop_type = data.get("crop_type") or slugify_crop(data.get("crop_en", ""))
        crop_label = data.get("crop_ar") if lang == "ar" else data.get("crop_en")
        if crop_label and crop_type:
            options[crop_label] = crop_type
    if not options:
        return {"طماطم": "tomato"} if lang == "ar" else {"Tomato": "tomato"}
    return options


def _add_msg(role: str, content: str, **extra):
    st.session_state["messages"].append({"role": role, "content": content, **extra})


def _run_analysis(crop_slug: str, image_path: str | None, query: str, lang: str = "ar"):
    retrieval_mode = os.getenv("RETRIEVAL_MODE", "mmr").lower()
    retrieval_k = to_int(os.getenv("RETRIEVAL_K", 4), 4)
    initial_state = {
        "chat_history": [],
        "crop_type": crop_slug,
        "retrieval_mode": retrieval_mode,
        "retrieval_k": retrieval_k,
        "query": query or None,
        "image_path": image_path,
        "ui_lang": lang,
    }
    return Workflow().run(initial_state)


# ── language gate ────────────────────────────────────────────────────────────


def render_language_gate():
    st.markdown(
        "<div style='text-align:center; padding-top:15vh'>",
        unsafe_allow_html=True,
    )
    st.title(t("login_title"))
    st.caption(t("login_caption"))
    col1, col2 = st.columns(2)
    with col1:
        if st.button("العربية", use_container_width=True, type="primary"):
            st.session_state["ui_lang"] = "ar"
    with col2:
        if st.button("English", use_container_width=True):
            st.session_state["ui_lang"] = "en"
    chosen = st.session_state.get("ui_lang")
    if chosen:
        st.success("تم اختيار العربية." if chosen == "ar" else "English selected.")
    if st.button(t("continue"), type="primary", disabled=not chosen, use_container_width=True):
        st.session_state["entered_app"] = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ── page config & session state ──────────────────────────────────────────────

st.set_page_config(
    page_title="Plant Disease Assistant",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# hide sidebar, hamburger menu, and streamlit footer for a clean ChatGPT look
st.markdown(
    """
    <style>
    [data-testid="stSidebar"]       { display: none !important; }
    [data-testid="collapsedControl"]{ display: none !important; }
    #MainMenu                       { display: none !important; }
    footer                          { display: none !important; }
    header                          { display: none !important; }
    .block-container { padding-top: 1.5rem; padding-bottom: 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

for key, default in {
    "ui_lang": "ar",
    "entered_app": False,
    "messages": [],
    "last_result": None,
    "pending_image": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if not st.session_state["entered_app"]:
    render_language_gate()
    st.stop()

lang = st.session_state["ui_lang"]
crop_options = load_crop_options(lang)

# ── top bar (title + language + clear) ───────────────────────────────────────

col_title, col_clear, col_lang = st.columns([6, 1, 1])
with col_title:
    st.markdown(f"### {t('chatbot_title')}")
with col_clear:
    if st.button("🗑️", help=t("chat_clear")):
        st.session_state["messages"] = []
        st.session_state["last_result"] = None
        st.session_state["pending_image"] = None
        st.rerun()
with col_lang:
    if st.button("🌐", help=t("switch_language")):
        st.session_state["entered_app"] = False
        st.rerun()

if not os.getenv("GROQ_API_KEY"):
    st.error(t("missing_key"))
    st.stop()

if not is_db_ready():
    st.warning(t("db_missing"))
    if st.button(t("build_db"), type="primary"):
        with st.spinner(t("db_building")):
            create_database()
        st.success(t("db_ready"))
        st.rerun()

# ── welcome message (shown once) ─────────────────────────────────────────────

if not st.session_state["messages"]:
    _add_msg("assistant", t("chat_welcome"))

# ── render existing messages ─────────────────────────────────────────────────

for msg in st.session_state["messages"]:
    avatar = "🧑‍🌾" if msg["role"] == "user" else "🌿"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("image"):
            st.image(msg["image"], width=250)
        st.markdown(msg["content"])

# ── details expander (after last analysis) ───────────────────────────────────

result = st.session_state.get("last_result")
if result:
    with st.expander(t("reason_btn")):
        scores = result.get("symptom_scores")
        if scores:
            st.markdown(f"**{t('detail_symptoms')}**")
            for row in scores[:5]:
                name = f"{row.get('disease_name_ar', '')} ({row.get('disease_name_en', '')})"
                st.write(f"- {name}: {row.get('score', 0)}%")
        pn = result.get("plantnet_result")
        if pn:
            st.markdown(f"**{t('detail_plantnet')}**")
            st.write(pn)
        evidence = result.get("web_evidence")
        if evidence:
            st.markdown(f"**{t('detail_evidence')}**")
            for item in evidence[:3]:
                st.write(f"- [{item.get('title', '')}]({item.get('url', '')})")
        vr = result.get("verification_result")
        if vr:
            st.markdown(f"**{t('detail_verify')}**")
            st.write(vr)
        src = result.get("source")
        if src:
            st.write(f"**{t('source')}:** {src}")

# ── upload strip (compact, ChatGPT-style attachment bar) ─────────────────────

upload_col, crop_col = st.columns([3, 2])
with upload_col:
    uploaded_image = st.file_uploader(
        t("upload"), type=["jpg", "jpeg", "png"], label_visibility="collapsed"
    )
with crop_col:
    selected_crop_label = st.selectbox(
        t("crop_label"),
        options=[t("crop_placeholder"), *crop_options.keys()],
        label_visibility="collapsed",
    )
crop_selected = selected_crop_label != t("crop_placeholder")
crop_slug = crop_options.get(selected_crop_label)

# auto-trigger analysis when image is uploaded
if uploaded_image and uploaded_image != st.session_state.get("pending_image"):
    st.session_state["pending_image"] = uploaded_image

    if not crop_selected:
        _add_msg("user", t("chat_image_sent"), image=uploaded_image.getvalue())
        _add_msg("assistant", t("ask_crop_first"))
        st.rerun()
    else:
        img_bytes = uploaded_image.getvalue()
        _add_msg("user", t("chat_image_sent"), image=img_bytes)

        suffix = Path(uploaded_image.name).suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_image.getbuffer())
            image_path = tmp.name

        with st.spinner(t("analyzing")):
            result = _run_analysis(crop_slug, image_path, None, lang=lang)

        st.session_state["last_result"] = result
        response_text = result.get("response", t("empty_result"))
        if result.get("vision_error"):
            response_text += f"\n\n⚠️ {t('vision_partial')}"
        response_text += f"\n\n---\n{t('followup_prompt')}"
        _add_msg("assistant", response_text)
        st.rerun()

# ── chat input (always visible at bottom) ────────────────────────────────────

if prompt := st.chat_input(t("chat_placeholder")):
    _add_msg("user", prompt)

    with st.chat_message("user", avatar="🧑‍🌾"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🌿"):
        with st.spinner(t("chat_replying")):
            reply = chat_response(
                prompt,
                crop_type=crop_slug if crop_selected else None,
                chat_history=st.session_state["messages"],
                lang=lang,
            )
        text = reply.get("text") if isinstance(reply, dict) else str(reply)
        text += f"\n\n---\n{t('followup_prompt')}"
        st.markdown(text)

    _add_msg("assistant", text)


