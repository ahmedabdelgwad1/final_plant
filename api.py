"""
FastAPI backend — exposes the plant disease diagnosis as a REST API.

Endpoints:
    POST /api/chat          → free-text chat with the assistant
    POST /api/analyze       → upload image + crop type → disease diagnosis
    GET  /api/crops         → list available crops
    GET  /api/health        → health check
"""

import os
import tempfile
import json
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(override=True)

from config import DATA_JSON_FILES, CHROMA_DB_DIR
from application.workflow import Workflow
from infrastructure.agents import chat_response
from shared.utils import to_int, slugify_crop

app = FastAPI(title="Plant Disease API", version="1.0.0")

# Allow React dev server (localhost:3000) and any origin in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── helpers ──────────────────────────────────────────────────────────────────


def _load_crops() -> list[dict]:
    """Return list of {slug, name_ar, name_en} from data files."""
    crops = []
    for path in DATA_JSON_FILES:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        slug = data.get("crop_type") or slugify_crop(data.get("crop_en", ""))
        crops.append({
            "slug": slug,
            "name_ar": data.get("crop_ar", ""),
            "name_en": data.get("crop_en", ""),
        })
    return crops


def _is_db_ready() -> bool:
    db = Path(CHROMA_DB_DIR)
    return db.exists() and any(db.iterdir())


# ── request / response models ───────────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    crop_type: str | None = None
    chat_history: list[dict] = []


class ChatResponse(BaseModel):
    reply: str
    context_count: int = 0


class AnalysisResponse(BaseModel):
    response: str
    disease_ar: str = ""
    disease_en: str = ""
    source: str = ""
    vision_error: str | None = None


# ── endpoints ────────────────────────────────────────────────────────────────


@app.get("/api/health")
def health():
    return {"status": "ok", "db_ready": _is_db_ready()}


@app.get("/api/crops")
def list_crops():
    """Return available crop types."""
    return {"crops": _load_crops()}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Free-text chat with the plant disease assistant."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    result = chat_response(
        user_message=req.message,
        crop_type=req.crop_type,
        chat_history=req.chat_history,
    )
    return ChatResponse(
        reply=result.get("text", ""),
        context_count=result.get("context_count", 0),
    )


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(
    crop_type: str = Form(...),
    query: str = Form(""),
    image: UploadFile = File(None),
):
    """
    Upload a leaf image (optional query text) → run the full
    diagnosis workflow and return disease + cause + treatment.
    """
    if not _is_db_ready():
        raise HTTPException(status_code=503, detail="Knowledge base not built yet.")

    if not image and not query.strip():
        raise HTTPException(status_code=400, detail="Provide an image or symptom text.")

    image_path = None
    if image:
        suffix = Path(image.filename or "img.jpg").suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await image.read())
            image_path = tmp.name

    retrieval_mode = os.getenv("RETRIEVAL_MODE", "mmr").lower()
    retrieval_k = to_int(os.getenv("RETRIEVAL_K", 4), 4)

    initial_state = {
        "chat_history": [],
        "crop_type": crop_type,
        "retrieval_mode": retrieval_mode,
        "retrieval_k": retrieval_k,
        "query": query.strip() or None,
        "image_path": image_path,
    }

    result = Workflow().run(initial_state)

    return AnalysisResponse(
        response=result.get("response", ""),
        disease_ar=result.get("decision_disease_ar", ""),
        disease_en=result.get("decision_disease_en", ""),
        source=result.get("source", ""),
        vision_error=result.get("vision_error"),
    )
