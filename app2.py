import json
import os
import tempfile
from pathlib import Path
import logging

import streamlit as st
from dotenv import load_dotenv

from config import CHROMA_DB_DIR, DATA_JSON_FILES
from infrastructure.create_db import create_database
from application.workflow import Workflow
from infrastructure.agents import chat_response
from shared.i18n import t
from shared.utils import to_int, slugify_crop

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        "chat_history": st.session_state.get("messages", []),
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
        """
        <div style='text-align:center; padding-top:10vh'>
            <div style='
                background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
                padding: 3rem 2rem;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                max-width: 600px;
                margin: 0 auto;
            '>
                <h1 style='
                    background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-size: 2.5rem;
                    margin-bottom: 1rem;
                    font-weight: 800;
                '>🌿 Plant Disease Assistant</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f"<p style='text-align:center; font-size:1.2rem; color:#555; margin-bottom:2rem'>{t('login_caption')}</p>",
            unsafe_allow_html=True,
        )

        col_ar, col_en = st.columns(2)
        with col_ar:
            if st.button("🇸🇦 العربية", use_container_width=True, type="primary", key="btn_arabic"):
                st.session_state["ui_lang"] = "ar"
                st.rerun()
        with col_en:
            if st.button("🇬🇧 English", use_container_width=True, key="btn_english"):
                st.session_state["ui_lang"] = "en"
                st.rerun()

        chosen = st.session_state.get("ui_lang")
        if chosen:
            st.success("✅ تم اختيار العربية" if chosen == "ar" else "✅ English selected")
            st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
            if st.button("▶️ " + t("continue"), type="primary", use_container_width=True, key="btn_continue"):
                st.session_state["entered_app"] = True
                st.rerun()


# ── page config & session state ──────────────────────────────────────────────

st.set_page_config(
    page_title="Plant Disease Assistant",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Professional CSS styling
st.markdown(
    """
    <style>
    /* Hide Streamlit elements for clean interface */
    [data-testid="stSidebar"]       { display: none !important; }
    [data-testid="collapsedControl"]{ display: none !important; }
    #MainMenu                       { display: none !important; }
    footer                          { display: none !important; }
    header                          { display: none !important; }

    /* Main container styling */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 900px;
    }

    /* Custom scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #4CAF50, #2E7D32); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #66BB6A, #4CAF50); }

    /* Chat messages styling */
    .stChatMessage {
        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
        border-radius: 15px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        border-left: 4px solid transparent;
        animation: fadeIn 0.5s ease-out;
    }
    .stChatMessage:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        transform: translateY(-2px);
    }

    /* User message styling */
    [data-testid="stChatMessageContent"]:has(> div[data-testid="stMarkdownContainer"] > p:first-child) {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-left-color: #4CAF50;
    }

    /* Bot message styling */
    .stChatMessage[data-testid="chat-message-assistant"] {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        border-left-color: #2196F3;
    }

    /* Input field styling */
    .stChatInputContainer {
        border-radius: 25px;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 0.5rem;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    .stChatInputContainer:focus-within {
        border-color: #4CAF50;
        box-shadow: 0 4px 16px rgba(76, 175, 80, 0.2);
    }

    /* Button styling */
    .stButton > button {
        border-radius: 12px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
        color: black;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #66BB6A 0%, #81C784 100%);
    }

    /* Success / Warning / Error boxes */
    .stSuccess {
        background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
        border-radius: 12px; padding: 1rem;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 8px rgba(76, 175, 80, 0.15);
    }
    .stWarning {
        background: linear-gradient(135deg, #FFF3E0 0%, #FFE082 100%);
        border-radius: 12px; padding: 1rem;
        border-left: 4px solid #FF9800;
        box-shadow: 0 2px 8px rgba(255, 152, 0, 0.15);
    }
    .stError {
        background: linear-gradient(135deg, #FFEBEE 0%, #FFCDD2 100%);
        border-radius: 12px; padding: 1rem;
        border-left: 4px solid #F44336;
        box-shadow: 0 2px 8px rgba(244, 67, 54, 0.15);
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #F5F5F5 0%, #E0E0E0 100%);
        border-radius: 12px; padding: 0.8rem 1rem; font-weight: 600;
        transition: all 0.3s ease;
    }
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #E0E0E0 0%, #BDBDBD 100%);
    }

    /* Title styling */
    h3 {
        background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }

    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    .stSelectbox > div > div:focus-within {
        border-color: #4CAF50;
        box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
    }

    /* Spinner */
    .stSpinner > div { border-top-color: #4CAF50 !important; }

    /* Horizontal rule */
    hr {
        border: none; height: 2px;
        background: linear-gradient(90deg, transparent 0%, #4CAF50 25%, #4CAF50 75%, transparent 100%);
        margin: 2rem 0; opacity: 0.3;
    }

    /* Image styling in chat */
    .stChatMessage img {
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transition: all 0.3s ease;
    }
    .stChatMessage img:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }

    /* Fade-in animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* Mobile responsive */
    @media (max-width: 768px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        .stChatMessage   { padding: 0.8rem; margin: 0.5rem 0; }
    }
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
    "selected_crop": None,
    "crop_slug": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if not st.session_state["entered_app"]:
    render_language_gate()
    st.stop()

lang = st.session_state["ui_lang"]
crop_options = load_crop_options(lang)

# ── top bar (title + clear + language) ───────────────────────────────────────

st.markdown(
    "<div style='"
    "background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);"
    "padding: 1.5rem 2rem; border-radius: 15px; margin-bottom: 2rem;"
    "box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3);'>"
    "<h2 style='color:black; margin:0; text-align:center; font-weight:700;"
    "text-shadow:0 2px 4px rgba(0,0,0,0.2);'>🌿 " + t("chatbot_title") + "</h2></div>",
    unsafe_allow_html=True,
)

col_clear, col_lang = st.columns(2)
with col_clear:
    if st.button("🗑️ " + t("chat_clear"), use_container_width=True, key="clear_btn"):
        st.session_state["messages"] = []
        st.session_state["last_result"] = None
        st.session_state["pending_image"] = None
        st.rerun()
with col_lang:
    if st.button("🌐 " + t("switch_language"), use_container_width=True, key="lang_btn"):
        st.session_state["entered_app"] = False
        st.rerun()

# ── prerequisites ────────────────────────────────────────────────────────────

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

# ── crop indicator ───────────────────────────────────────────────────────────

if st.session_state.get("selected_crop"):
    col_crop_display, col_crop_change = st.columns([4, 1])
    with col_crop_display:
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#E8F5E9 0%,#C8E6C9 100%);"
            f"padding:0.8rem 1.2rem;border-radius:12px;"
            f"border-left:4px solid #4CAF50;box-shadow:0 2px 8px rgba(76,175,80,0.15);'>"
            f"<span style='font-size:1.05rem;font-weight:600;color:#2E7D32;'>"
            f"🌱 {st.session_state['selected_crop']}</span></div>",
            unsafe_allow_html=True,
        )
    with col_crop_change:
        if st.button("🔄", key="change_crop", help=("تغيير المحصول" if lang == "ar" else "Change crop")):
            st.session_state.update({"selected_crop": None, "crop_slug": None})
            st.rerun()
else:
    # ── Crop not selected yet → show compact inline selector ─────────────────
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        crop_choice = st.selectbox(
            "🌾 " + ("اختر المحصول:" if lang == "ar" else "Select Crop:"),
            options=list(crop_options.keys()),
            key="crop_selector_main",
            label_visibility="collapsed",
            placeholder=("-- اختر نوع النبات --" if lang == "ar" else "-- Select plant --"),
        )
    with col_btn:
        if st.button(
            "✅",
            type="primary",
            use_container_width=True,
            help=("تأكيد اختيار المحصول" if lang == "ar" else "Confirm crop selection"),
        ):
            st.session_state["selected_crop"] = crop_choice
            st.session_state["crop_slug"] = crop_options.get(crop_choice)
            st.rerun()

# ── welcome message (shown once) ─────────────────────────────────────────────

if not st.session_state["messages"]:
    welcome = t("chat_welcome")
    if lang == "ar":
        welcome += "\n\n💬 **اسأل عن أمراض النباتات**\n\n📸 **أو أرفق صورة من شريط الكتابة بالأسفل لتحليلها فوراً**"
    else:
        welcome += "\n\n💬 **Ask about plant diseases**\n\n📸 **Or attach an image from the chat bar below to analyze it instantly**"
    _add_msg("assistant", welcome)

# ── render existing messages ─────────────────────────────────────────────────

for msg in st.session_state["messages"]:
    avatar = "👨‍🌾" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("image"):
            st.image(msg["image"], width=300)
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

# ══════════════════════════════════════════════════════════════════════════════
# ── UNIFIED MULTIMODAL CHAT INPUT (always visible) ───────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

user_input = st.chat_input(
    t("chat_placeholder"),
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    # ── Case A: Image attached ───────────────────────────────────────────
    if hasattr(user_input, "files") and user_input.files:

        # Block image upload if no crop selected
        if not st.session_state.get("crop_slug"):
            warning_msg = "⚠️ " + (
                "اختر نوع المحصول من القائمة بالأعلى الأول، وبعدين ارفع الصورة تاني."
                if lang == "ar"
                else "Please select the crop type from the dropdown above first, then re-upload the image."
            )
            _add_msg("assistant", warning_msg)
            st.rerun()

        uploaded = user_input.files[0]
        img_bytes = uploaded.getvalue()

        user_text = (
            user_input.text.strip()
            if hasattr(user_input, "text") and user_input.text
            else t("chat_image_sent")
        )
        _add_msg("user", user_text, image=img_bytes)

        with st.chat_message("user", avatar="👨‍🌾"):
            st.image(img_bytes, width=300)
            st.markdown(user_text)

        suffix = Path(uploaded.name).suffix or ".jpg"
        image_path = None

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(img_bytes)
                image_path = tmp.name

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner(t("analyzing")):
                    query_text = (
                        user_input.text.strip()
                        if hasattr(user_input, "text") and user_input.text
                        else None
                    )
                    result = _run_analysis(
                        st.session_state["crop_slug"],
                        image_path,
                        query_text,
                        lang=lang,
                    )
                    st.session_state["last_result"] = result
                    response_text = result.get("response", t("empty_result"))
                    if result.get("vision_error"):
                        response_text += f"\n\n⚠️ {t('vision_partial')}"
                    response_text += f"\n\n---\n{t('followup_prompt')}"
                    st.markdown(response_text)
                    _add_msg("assistant", response_text)

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            error_msg = "❌ " + (
                "حدث خطأ أثناء تحليل الصورة." if lang == "ar" else "Error analyzing the image."
            )
            st.error(error_msg)
            _add_msg("assistant", error_msg)

        finally:
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError as e:
                    logger.warning(f"Failed to delete temp file: {e}")

        st.rerun()

    # ── Case B: Text only ────────────────────────────────────────────────
    elif hasattr(user_input, "text") and user_input.text:
        prompt = user_input.text.strip()
        _add_msg("user", prompt)

        with st.chat_message("user", avatar="👨‍🌾"):
            st.markdown(prompt)

        try:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner(t("chat_replying")):
                    reply = chat_response(
                        prompt,
                        crop_type=st.session_state.get("crop_slug"),
                        chat_history=st.session_state["messages"],
                        lang=lang,
                    )
                    text = reply.get("text") if isinstance(reply, dict) else str(reply)
                    text += f"\n\n---\n{t('followup_prompt')}"
                    st.markdown(text)
                    _add_msg("assistant", text)

        except Exception as e:
            logger.error(f"Chat response failed: {e}")
            error_msg = "❌ " + ("حدث خطأ." if lang == "ar" else "Error occurred.")
            st.error(error_msg)
            _add_msg("assistant", error_msg)

        st.rerun()

