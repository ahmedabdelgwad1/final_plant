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
        """
        <div style='text-align:center; padding-top:10vh'>
            <div style='
                background: linear-gradient(135deg, #1e3a1f 0%, #142b15 100%);
                padding: 3rem 2rem;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4);
                max-width: 600px;
                margin: 0 auto;
                color: #ffffff;
            '>
                <h1 style='
                    background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
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
            f"<p style='text-align:center; font-size:1.2rem; color:#e0e0e0; margin-bottom:2rem'>{t('login_caption')}</p>",
            unsafe_allow_html=True
        )
        
        col_ar, col_en = st.columns(2)
        with col_ar:
            if st.button(
                "🇸🇦 العربية",
                use_container_width=True,
                type="primary",
                key="btn_arabic"
            ):
                st.session_state["ui_lang"] = "ar"
                st.rerun()
        with col_en:
            if st.button(
                "🇬🇧 English",
                use_container_width=True,
                key="btn_english"
            ):
                st.session_state["ui_lang"] = "en"
                st.rerun()
        
        chosen = st.session_state.get("ui_lang")
        if chosen:
            st.success(
                "✅ تم اختيار العربية" if chosen == "ar" else "✅ English selected"
            )
            st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)
            if st.button(
                "▶️ " + t("continue"),
                type="primary",
                use_container_width=True,
                key="btn_continue"
            ):
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
        padding-bottom: 1rem;
        max-width: 900px;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #1e1e1e;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #4CAF50, #2E7D32);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #66BB6A, #4CAF50);
    }
    
    /* Text colors everywhere */
    * {
        color: #ffffff !important;
    }
    
    /* Chat messages styling */
    .stChatMessage {
        background: linear-gradient(135deg, #1e3a1f 0%, #142b15 100%);
        border-radius: 15px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
        transition: all 0.3s ease;
        border-left: 4px solid transparent;
    }
    
    .stChatMessage:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.6);
        transform: translateY(-2px);
    }
    
    /* User message styling */
    [data-testid="stChatMessageContent"]:has(> div[data-testid="stMarkdownContainer"] > p:first-child) {
        background: linear-gradient(135deg, #1e3a1f 0%, #142b15 100%);
        border-left-color: #4CAF50;
    }
    
    /* Bot message styling */
    .stChatMessage[data-testid="chat-message-assistant"] {
        background: linear-gradient(135deg, #0d293e 0%, #081a27 100%);
        border-left-color: #2196F3;
    }
    
    /* Input field styling */
    .stChatInputContainer {
        border-radius: 25px;
        background: linear-gradient(135deg, #2b3a2f 0%, #1d2b20 100%);
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        padding: 0.5rem;
        border: 2px solid #4CAF50;
        transition: all 0.3s ease;
    }
    
    .stChatInputContainer:focus-within {
        border-color: #66BB6A;
        box-shadow: 0 4px 16px rgba(76, 175, 80, 0.4);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 12px;
        background: #1e3a1f;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: 1px solid #4CAF50;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        background: #2E7D32;
    }
    
    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        border: none;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%);
    }
    
    /* Success box styling */
    .stSuccess {
        background: linear-gradient(135deg, #1e3a1f 0%, #142b15 100%);
        border-radius: 12px;
        padding: 1rem;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 2px 8px rgba(76, 175, 80, 0.2);
    }
    
    /* Warning box styling */
    .stWarning {
        background: #3e2703;
        border-radius: 12px;
        padding: 1rem;
        border-left: 4px solid #FF9800;
        box-shadow: 0 2px 8px rgba(255, 152, 0, 0.2);
    }
    
    /* Error box styling */
    .stError {
        background: #3a1616;
        border-radius: 12px;
        padding: 1rem;
        border-left: 4px solid #F44336;
        box-shadow: 0 2px 8px rgba(244, 67, 54, 0.2);
    }
    
    /* File uploader styling */
    .stFileUploader {
        background: linear-gradient(135deg, #0d293e 0%, #081a27 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border: 2px dashed #2196F3;
        transition: all 0.3s ease;
    }
    
    .stFileUploader:hover {
        border-color: #4fc3f7;
        background: linear-gradient(135deg, #15456b 0%, #0d293e 100%);
        transform: scale(1.02);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #2b3a2f 0%, #1d2b20 100%);
        border-radius: 12px;
        padding: 0.8rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #374a3c 0%, #2b3a2f 100%);
    }
    
    /* Title styling */
    h3 {
        background: linear-gradient(135deg, #4CAF50 0%, #81C784 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
    
    /* Spinner styling */
    .stSpinner > div {
        border-top-color: #4CAF50 !important;
    }
    
    /* Horizontal rule styling */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            #4CAF50 25%, 
            #4CAF50 75%, 
            transparent 100%);
        margin: 2rem 0;
        opacity: 0.3;
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
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .stChatMessage {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        .stChatMessage {
            padding: 0.8rem;
            margin: 0.5rem 0;
        }
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

# ── top bar (title + language + clear) ───────────────────────────────────────

st.markdown(
    """
    <div style='
        background: linear-gradient(135deg, #4CAF50 0%, #66BB6A 100%);
        padding: 1.5rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3);
    '>
        <h2 style='
            color: white;
            margin: 0;
            text-align: center;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        '>🌿 """ + t('chatbot_title') + """</h2>
    </div>
    """,
    unsafe_allow_html=True
)

col_clear, col_lang = st.columns([1, 1])
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

# ── crop indicator (optional - shown if selected) ────────────────────────────

crop_slug = st.session_state.get("crop_slug")
selected_crop_label = st.session_state.get("selected_crop")

if selected_crop_label:
    st.markdown(
        f"""
        <div style='
            background: linear-gradient(135deg, #E8F5E9 0%, #C8E6C9 100%);
            padding: 1rem 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            border-left: 4px solid #4CAF50;
            box-shadow: 0 2px 8px rgba(76, 175, 80, 0.15);
            display: flex;
            align-items: center;
            justify-content: space-between;
        '>
            <span style='font-size: 1.1rem; font-weight: 600; color: #2E7D32;'>
                🌱 {selected_crop_label}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("🔄 " + ("تغيير المحصول" if lang == "ar" else "Change crop"), key="change_crop"):
        st.session_state["selected_crop"] = None
        st.session_state["crop_slug"] = None
        st.rerun()

# ── welcome message (shown once) ─────────────────────────────────────────────

if not st.session_state["messages"]:
    welcome = t("chat_welcome")
    if lang == "ar":
        welcome += "\n\n💬 **اسأل عن أمراض النباتات**"
        welcome += "\n\n📸 **أو اضغط على زر الكاميرا لتحليل صورة**"
    else:
        welcome += "\n\n💬 **Ask about plant diseases**"
        welcome += "\n\n📸 **Or click the camera button to analyze an image**"
    _add_msg("assistant", welcome)

# ── render existing messages ─────────────────────────────────────────────────

for msg in st.session_state["messages"]:
    avatar = "👨‍🌾" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        if msg.get("image"):
            st.image(msg["image"], width=300, use_container_width=False)
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

# ── camera/upload button (always visible) ───────────────────────────────────

st.markdown(
    """
    <div style='
        margin: 2rem 0 1.5rem 0;
        padding: 0.5rem 0;
        border-top: 2px solid #e0e0e0;
    '></div>
    """,
    unsafe_allow_html=True
)

# Show crop selector if image upload is attempted without crop
if "show_crop_selector" not in st.session_state:
    st.session_state["show_crop_selector"] = False

st.markdown(
    f"""
    <div style='
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 4px 12px rgba(33, 150, 243, 0.15);
    '>
        <p style='
            text-align: center;
            font-weight: 600;
            color: #1976D2;
            margin: 0;
            font-size: 1.1rem;
        '>📸 {"ارفع صورة لتحليل المرض" if lang == "ar" else "Upload Image for Disease Analysis"}</p>
    </div>
    """,
    unsafe_allow_html=True
)

col_camera, col_crop_selector = st.columns([2, 3])

with col_camera:
    uploaded_image = st.file_uploader(
        "📸 " + ("اختر صورة" if lang == "ar" else "Choose Image"),
        type=["jpg", "jpeg", "png"],
        help=("التقط صورة أو ارفع من المعرض" if lang == "ar" else "Take photo or upload from gallery"),
        key="image_uploader",
        label_visibility="collapsed"
    )

# If there's a new image uploaded, always ask to set/confirm the crop
is_new_image = uploaded_image and uploaded_image != st.session_state.get("pending_image")

if is_new_image:
    with col_crop_selector:
        st.markdown(
            f"""
            <div style='
                background: #3e2703;
                padding: 0.8rem;
                border-radius: 10px;
                border-left: 4px solid #FF9800;
                margin-bottom: 0.8rem;
            '>
                <p style='margin: 0; color: #FFA726; font-weight: 600;'>
                    ⚠️ {"برجاء تحديد المحصول لهذه الصورة" if lang == "ar" else "Please select the crop for this image"}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Determine index of currently selected crop if any, to make it easier, or default to 0
        default_idx = 0
        current_sel = st.session_state.get("selected_crop")
        if current_sel in crop_options:
            opts_list = list(crop_options.keys())
            default_idx = opts_list.index(current_sel) + 1
            
        crop_choice = st.selectbox(
            "🌾 " + ("اختر المحصول:" if lang == "ar" else "Select Crop:"),
            options=["", *crop_options.keys()],
            index=default_idx,
            key="crop_selector_for_image"
        )
        if crop_choice:
            if st.button(
                "✅ " + ("تأكيد وتحليل" if lang == "ar" else "Confirm & Analyze"),
                type="primary",
                use_container_width=True,
                key="confirm_crop"
            ):
                st.session_state["selected_crop"] = crop_choice
                st.session_state["crop_slug"] = crop_options.get(crop_choice)
                
                st.session_state["pending_image"] = uploaded_image
                
                img_bytes = uploaded_image.getvalue()
                _add_msg("user", t("chat_image_sent"), image=img_bytes)

                suffix = Path(uploaded_image.name).suffix or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_image.getbuffer())
                    image_path = tmp.name

                with st.spinner(t("analyzing")):
                    result = _run_analysis(st.session_state["crop_slug"], image_path, None, lang=lang)

                st.session_state["last_result"] = result
                response_text = result.get("response", t("empty_result"))
                if result.get("vision_error"):
                    response_text += f"\n\n⚠️ {t('vision_partial')}"
                response_text += f"\n\n---\n{t('followup_prompt')}"
                _add_msg("assistant", response_text)
                st.rerun()

# ── chat input (always visible at bottom) ────────────────────────────────────

chat_placeholder = "💬 " + ("اسأل عن أي أمراض تصيب النباتات..." if lang == "ar" else "Ask about any plant diseases...")

if prompt := st.chat_input(chat_placeholder):
    _add_msg("user", prompt)

    with st.chat_message("user", avatar="🧑‍🌾"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🌿"):
        with st.spinner(t("chat_replying")):
            reply = chat_response(
                prompt,
                crop_type=crop_slug,
                chat_history=st.session_state["messages"],
                lang=lang,
            )
        text = reply.get("text") if isinstance(reply, dict) else str(reply)
        text += f"\n\n---\n{t('followup_prompt')}"
        st.markdown(text)

    _add_msg("assistant", text)
    st.rerun()


