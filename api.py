"""
FastAPI backend — unified chat API for plant disease diagnosis.

Endpoints:
    POST /api/chat    → text chat OR image + crop → diagnosis (single endpoint)
    GET  /api/crops   → list available crops
    GET  /api/health  → health check
"""

import os
import tempfile
import json
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(override=True)

from config import DATA_JSON_FILES, CHROMA_DB_DIR
from application.workflow import Workflow
from infrastructure.agents import chat_response
from shared.utils import to_int, slugify_crop

app = FastAPI(title="Plant Disease API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── helpers ──────────────────────────────────────────────────────────────────


def _load_crops() -> list[dict]:
    crops = []
    for path in DATA_JSON_FILES:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        slug = data.get("crop_type") or slugify_crop(data.get("crop_en", ""))
        crops.append({"slug": slug, "name_ar": data.get("crop_ar", ""), "name_en": data.get("crop_en", "")})
    return crops


def _is_db_ready() -> bool:
    db = Path(CHROMA_DB_DIR)
    return db.exists() and any(db.iterdir())


# ── endpoints ────────────────────────────────────────────────────────────────


@app.get("/api/health")
def health():
    return {"status": "ok", "db_ready": _is_db_ready()}


@app.get("/api/crops")
def list_crops():
    return {"crops": _load_crops()}


@app.post("/api/chat")
async def chat(
    message: str = Form(""),
    crop_type: str = Form(""),
    lang: str = Form("ar"),
    chat_history: str = Form("[]"),
    image: UploadFile = File(None),
):
    """
    Unified chat endpoint.
    - Text only  → conversational reply
    - Image + crop_type → disease diagnosis (disease + cause + treatment)
    - Image without crop_type → asks user to choose crop first
    """
    # parse chat_history from JSON string
    try:
        history = json.loads(chat_history) if chat_history else []
    except Exception:
        history = []

    has_image = image is not None
    has_text = bool(message.strip())

    if not has_image and not has_text:
        raise HTTPException(status_code=400, detail="Send a message or an image.")

    # ── Image flow: run full diagnosis workflow ──────────────────────────
    if has_image:
        if not _is_db_ready():
            raise HTTPException(status_code=503, detail="Knowledge base not built yet.")

        if not crop_type.strip():
            hint = "من فضلك اختر نوع النبات الأول." if lang == "ar" else "Please select the crop type first."
            return {"reply": hint}

        suffix = Path(image.filename or "img.jpg").suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await image.read())
            image_path = tmp.name

        result = Workflow().run({
            "chat_history": [],
            "crop_type": crop_type.strip(),
            "retrieval_mode": os.getenv("RETRIEVAL_MODE", "mmr").lower(),
            "retrieval_k": to_int(os.getenv("RETRIEVAL_K", 4), 4),
            "query": message.strip() or None,
            "image_path": image_path,
            "ui_lang": lang,
        })

        reply = result.get("response", "")
        if result.get("vision_error"):
            warning = "⚠️ حدث خطأ في تحليل الصورة." if lang == "ar" else "⚠️ Error analyzing the image."
            reply += f"\n\n{warning}"

        return {"reply": reply}

    # ── Text-only flow: conversational chat ──────────────────────────────
    result = chat_response(
        user_message=message.strip(),
        crop_type=crop_type.strip() or None,
        chat_history=history,
        lang=lang,
    )
    return {"reply": result.get("text", "")}

