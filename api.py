"""
FastAPI backend — unified chat API for plant disease diagnosis.

Endpoints:
    GET  /api/health       → health check + database status
    GET  /api/crops        → list available crops (ar & en names)
    POST /api/chat         → text chat (requires crop_type)
    POST /api/analyze      → image analysis (requires crop_type + image)
    POST /api/build-db     → build knowledge base (admin endpoint)
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
    message: str = Form(...),
    crop_type: str = Form(""),
    lang: str = Form("ar"),
    chat_history: str = Form("[]"),
):
    """
    Text-only chat endpoint.
    Requires: message
    Optional: crop_type (if provided, gives more specific answers)
    Returns: conversational reply about plant diseases
    """
    if not message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    # parse chat_history from JSON string
    try:
        history = json.loads(chat_history) if chat_history else []
    except Exception:
        history = []

    result = chat_response(
        user_message=message.strip(),
        crop_type=crop_type.strip() or None,
        chat_history=history,
        lang=lang,
    )
    
    return {
        "success": True,
        "reply": result.get("text", ""),
        "crop_type": crop_type.strip() or None,
    }


@app.post("/api/analyze")
async def analyze_image(
    crop_type: str = Form(...),
    image: UploadFile = File(...),
    lang: str = Form("ar"),
    message: str = Form(""),
):
    """
    Image analysis endpoint.
    Requires: crop_type, image
    Returns: full diagnosis with details (disease, causes, treatment, scores)
    """
    if not crop_type.strip():
        raise HTTPException(status_code=400, detail="crop_type is required. Please select crop first.")
    
    if not _is_db_ready():
        raise HTTPException(status_code=503, detail="Knowledge base not ready. Please build database first.")

    # Save uploaded image temporarily
    suffix = Path(image.filename or "img.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await image.read())
        image_path = tmp.name

    # Run full diagnosis workflow
    result = Workflow().run({
        "chat_history": [],
        "crop_type": crop_type.strip(),
        "retrieval_mode": os.getenv("RETRIEVAL_MODE", "mmr").lower(),
        "retrieval_k": to_int(os.getenv("RETRIEVAL_K", 4), 4),
        "query": message.strip() or None,
        "image_path": image_path,
        "ui_lang": lang,
    })

    # Build response
    response_text = result.get("response", "")
    if result.get("vision_error"):
        warning = "⚠️ حدث خطأ في تحليل الصورة." if lang == "ar" else "⚠️ Error analyzing the image."
        response_text += f"\n\n{warning}"

    # Clean up temp file
    try:
        os.unlink(image_path)
    except:
        pass

    return {
        "success": True,
        "reply": response_text,
        "crop_type": crop_type.strip(),
        "details": {
            "symptom_scores": result.get("symptom_scores", []),
            "plantnet_result": result.get("plantnet_result"),
            "web_evidence": result.get("web_evidence", []),
            "verification_result": result.get("verification_result"),
            "source": result.get("source"),
            "vision_error": result.get("vision_error", False),
        }
    }


@app.post("/api/build-db")
def build_database_endpoint():
    """
    Admin endpoint to build/rebuild the knowledge base.
    """
    try:
        from infrastructure.create_db import create_database
        create_database()
        return {"success": True, "message": "Database built successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to build database: {str(e)}")

