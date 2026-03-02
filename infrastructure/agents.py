import os
import base64
import re
from io import BytesIO
import requests
from langchain_groq import ChatGroq
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import HumanMessage
from PIL import Image
from domain.models import State
from dotenv import load_dotenv
from infrastructure.prompts import VISION_PROMPT
from config import CHROMA_DB_DIR
from shared.utils import to_int, to_float

load_dotenv(override=True)

_groq_api_key = os.getenv("GROQ_API_KEY")
_vision_model = os.getenv("GROQ_VISION_MODEL", "llama-3.2-11b-vision-preview")
_text_model = os.getenv("GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")
_embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
_tavily_api_key = os.getenv("TAVILY_API_KEY")
_plantnet_api_key = os.getenv("PLANTNET_API_KEY")
_trusted_domains = [
    "extension.umn.edu",
    "ucanr.edu",
    "cabi.org",
    "plantwiseplusknowledgebank.org",
    "apsnet.org",
]

vision_llm = ChatGroq(
    model=_vision_model,
    temperature=0,
    api_key=_groq_api_key
)

text_llm = ChatGroq(
    model=_text_model,
    temperature=0,
    api_key=_groq_api_key
)

embedding = HuggingFaceEmbeddings(model_name=_embedding_model)
vdb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embedding)


def _build_filter(crop_type: str):
    if crop_type:
        return {"crop_type": crop_type}
    return None


def _tokenize(text: str):
    return set(re.findall(r"\b\w+\b", (text or "").lower()))


def _keyword_overlap_score(query: str, text: str) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0.0
    t_tokens = _tokenize(text)
    if not t_tokens:
        return 0.0
    return len(q_tokens.intersection(t_tokens)) / max(1, len(q_tokens))


def _hybrid_retrieve(query: str, crop_type: str, k: int):
    filter_dict = _build_filter(crop_type)
    total = vdb._collection.count()
    candidate_k = min(max(k * 3, 8), total)
    candidates = vdb.similarity_search(query, k=candidate_k, filter=filter_dict)
    alpha = to_float(os.getenv("HYBRID_ALPHA", 0.7), 0.7)

    scored = []
    for idx, doc in enumerate(candidates):
        dense_rank_score = 1.0 / (idx + 1)
        lexical_score = _keyword_overlap_score(query, doc.page_content)
        score = alpha * dense_rank_score + (1.0 - alpha) * lexical_score
        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:k]]


def _retrieve_context(query: str, crop_type: str, retrieval_mode: str, k: int):
    mode = (retrieval_mode or os.getenv("RETRIEVAL_MODE", "mmr")).lower()
    filter_dict = _build_filter(crop_type)
    total = vdb._collection.count()
    fetch_k = min(to_int(os.getenv("RETRIEVAL_FETCH_K", max(10, k * 3)), max(10, k * 3)), total)
    fetch_k = max(fetch_k, k)  # fetch_k must be >= k for MMR
    lambda_mult = to_float(os.getenv("RETRIEVAL_LAMBDA_MULT", 0.4), 0.4)

    if mode == "hybrid":
        return _hybrid_retrieve(query=query, crop_type=crop_type, k=k)

    if mode == "similarity":
        retriever = vdb.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k, "filter": filter_dict},
        )
        return retriever.invoke(query)

    retriever = vdb.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": k,
            "fetch_k": fetch_k,
            "lambda_mult": lambda_mult,
            "filter": filter_dict,
        },
    )
    return retriever.invoke(query)


def _format_retrieved_context(context_docs):
    if not context_docs:
        return "No retrieved context."

    rows = []
    for idx, doc in enumerate(context_docs, start=1):
        metadata = getattr(doc, "metadata", {}) or {}
        page_content = getattr(doc, "page_content", "") or ""
        rows.append(
            (
                f"[Doc {idx}]\n"
                f"disease_name_ar: {metadata.get('disease_name_ar', '')}\n"
                f"disease_name_en: {metadata.get('disease_name_en', '')}\n"
                f"crop_type: {metadata.get('crop_type', '')}\n"
                f"treatment_organic_ar: {metadata.get('treatment_organic_ar', '')}\n"
                f"treatment_chemical_ar: {metadata.get('treatment_chemical_ar', '')}\n"
                f"content: {page_content}\n"
            )
        )
    return "\n".join(rows)


def _extract_suspected_disease(context_docs):
    if not context_docs:
        return None
    metadata = getattr(context_docs[0], "metadata", {}) or {}
    return metadata.get("disease_name_en") or metadata.get("disease_name_ar")


def _score_context_matches(vision_desc: str, context_docs):
    rows = []
    for idx, doc in enumerate(context_docs or []):
        metadata = getattr(doc, "metadata", {}) or {}
        name_ar = metadata.get("disease_name_ar", "")
        name_en = metadata.get("disease_name_en", "")
        text = getattr(doc, "page_content", "") or ""
        score = round(_keyword_overlap_score(vision_desc, text) * 100, 1)
        rows.append(
            {
                "doc_index": idx,
                "disease_name_ar": name_ar,
                "disease_name_en": name_en,
                "score": score,
            }
        )
    rows.sort(key=lambda x: x["score"], reverse=True)
    return rows


def _search_web_evidence(disease_name: str, crop_type: str, max_items: int = 3):
    if not _tavily_api_key or not disease_name:
        return []

    query = (
        f"{crop_type} {disease_name} symptoms diagnosis "
        "site:extension.umn.edu OR site:ucanr.edu OR site:cabi.org OR site:apsnet.org"
    )
    payload = {
        "api_key": _tavily_api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": 8,
        "include_images": False,
    }
    try:
        response = requests.post("https://api.tavily.com/search", json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Error in tavily web evidence: {e}")
        return []

    out = []
    for item in data.get("results", []):
        url = item.get("url", "")
        if not isinstance(url, str) or not url.startswith("http"):
            continue
        if not any(domain in url for domain in _trusted_domains):
            continue
        content = (item.get("content") or "").strip()
        out.append(
            {
                "title": (item.get("title") or "").strip(),
                "url": url,
                "snippet": content[:300],
            }
        )
        if len(out) >= max_items:
            break
    return out


def _guess_mime_type(image_path: str) -> str:
    ext = os.path.splitext((image_path or "").lower())[1]
    if ext == ".png":
        return "image/png"
    if ext in {".webp"}:
        return "image/webp"
    return "image/jpeg"


def _normalize_for_match(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", (text or "").lower()).strip()


def _disease_aliases(disease_name: str):
    normalized = _normalize_for_match(disease_name)
    aliases = {normalized}
    _ALIAS_MAP = {
        "late blight": ["late blight", "phytophthora infestans", "blight"],
        "powdery mildew": ["powdery mildew", "oidium", "leveillula taurica", "mildew"],
        "leaf mold": ["leaf mold", "passalora fulva", "mold"],
        "yellow rust": ["yellow rust", "stripe rust", "puccinia striiformis"],
        "stripe rust": ["stripe rust", "yellow rust", "puccinia striiformis"],
        "stem rust": ["stem rust", "black rust", "puccinia graminis"],
        "black rust": ["black rust", "stem rust", "puccinia graminis"],
        "loose smut": ["loose smut", "ustilago tritici", "smut"],
        "septoria": ["septoria", "septoria tritici", "zymoseptoria tritici", "blotch"],
        "fusarium": ["fusarium", "fusarium head blight", "scab", "fusarium graminearum"],
        "head blight": ["head blight", "fusarium head blight", "scab"],
        "sunn pest": ["sunn pest", "wheat bug", "eurygaster integriceps"],
    }
    for key, extra_aliases in _ALIAS_MAP.items():
        if key in normalized:
            aliases.update(extra_aliases)
    return {a.strip() for a in aliases if a.strip()}


def _collect_texts(obj):
    texts = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if isinstance(v, (str, int, float)) and (
                "disease" in lk or "name" in lk or "scientific" in lk or "common" in lk
            ):
                texts.append(str(v))
            else:
                texts.extend(_collect_texts(v))
    elif isinstance(obj, list):
        for item in obj:
            texts.extend(_collect_texts(item))
    return texts


def _extract_plantnet_result_label(item):
    if not isinstance(item, dict):
        return ""
    species = item.get("species") if isinstance(item.get("species"), dict) else {}
    candidates = [
        species.get("scientificNameWithoutAuthor", ""),
        species.get("scientificName", ""),
        species.get("commonName", ""),
    ]
    common_names = species.get("commonNames")
    if isinstance(common_names, list) and common_names:
        candidates.extend(common_names[:2])
    candidates.extend(_collect_texts(item))
    for raw in candidates:
        text = str(raw).strip()
        if len(text) >= 3 and text.lower() not in {"leaf", "disease", "plant"}:
            return text
    return "Unknown disease label"


def _plantnet_top_candidates_text(results, max_items: int = 3):
    lines = []
    if not isinstance(results, list):
        return ""
    for idx, item in enumerate(results[:max_items], start=1):
        if not isinstance(item, dict):
            continue
        label = _extract_plantnet_result_label(item)
        score = 0.0
        try:
            score = float(item.get("score", 0.0))
        except Exception:
            score = 0.0
        lines.append(f"{idx}) {label} ({round(score * 100, 1)}%)")
    return "\n".join(lines)


def _plantnet_disease_verify(image_path: str, expected_disease: str):
    if not _plantnet_api_key:
        return "skipped", "تم تخطي فحص PlantNet (الأمراض) لعدم توفر PLANTNET_API_KEY.", []
    if not image_path or not os.path.exists(image_path):
        return "skipped", "تم تخطي فحص PlantNet (الأمراض) لعدم وجود صورة.", []
    if not expected_disease:
        return "skipped", "تم تخطي فحص PlantNet (الأمراض) لعدم وجود مرض متوقع.", []

    endpoint = f"https://my-api.plantnet.org/v2/diseases/identify?api-key={_plantnet_api_key}"
    mime = _guess_mime_type(image_path)
    try:
        with open(image_path, "rb") as f:
            files = {"images": ("leaf_image", f.read(), mime)}
        response = requests.post(endpoint, files=files, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except Exception as e:
        return "error", f"فشل فحص PlantNet (الأمراض): {e}", []

    results = payload.get("results")
    if not results:
        return "unknown", "PlantNet (الأمراض) لم يرجع نتائج كافية من الصورة.", []
    top_candidates = _plantnet_top_candidates_text(results)
    diseases = []
    for item in (results or [])[:5]:
        if not isinstance(item, dict):
            continue
        label = _extract_plantnet_result_label(item)
        try:
            conf = float(item.get("score", 0.0))
        except Exception:
            conf = 0.0
        diseases.append({"name": label, "confidence": conf})

    aliases = _disease_aliases(expected_disease)
    candidates = _collect_texts(payload)
    normalized_blob = " | ".join(_normalize_for_match(x) for x in candidates if x)
    matched = any(alias in normalized_blob for alias in aliases)

    top_score = 0.0
    if isinstance(results, list) and results:
        try:
            top_score = float((results[0] or {}).get("score", 0.0))
        except Exception:
            top_score = 0.0

    if matched and top_score >= 0.2:
        return "confirmed", (
            f"PlantNet (الأمراض) يدعم التشخيص المتوقع '{expected_disease}' "
            f"بدرجة تقريبية {round(top_score * 100, 1)}%.\n"
            f"أبرز ترشيحات PlantNet:\n{top_candidates}"
        ), diseases
    if matched:
        return "unknown", (
            f"PlantNet (الأمراض) وجد إشارات توافق مع '{expected_disease}' لكن بثقة منخفضة "
            f"({round(top_score * 100, 1)}%).\n"
            f"أبرز ترشيحات PlantNet:\n{top_candidates}"
        ), diseases
    return (
        "mismatch",
        f"PlantNet (الأمراض) لم يدعم التشخيص المتوقع '{expected_disease}'.\n"
        f"أبرز ترشيحات PlantNet:\n{top_candidates}",
        diseases,
    )


def _normalize_confidence(value):
    try:
        num = float(value)
    except Exception:
        return 0.0
    if num > 1:
        num = num / 100.0
    return max(0.0, min(1.0, num))


def _token_set(text: str):
    return set(_normalize_for_match(text).split())


def _canonicalize_disease_name(raw_name: str, state: State) -> str:
    raw_norm = _normalize_for_match(raw_name)
    if not raw_norm:
        return raw_name

    known = []
    for item in state.get("evidence_data") or []:
        name = (item or {}).get("name")
        if name:
            known.append(name)
    for doc in state.get("context") or []:
        md = getattr(doc, "metadata", {}) or {}
        if md.get("disease_name_en"):
            known.append(md["disease_name_en"])
        if md.get("disease_name_ar"):
            known.append(md["disease_name_ar"])

    dedup = []
    seen = set()
    for n in known:
        key = _normalize_for_match(n)
        if key and key not in seen:
            seen.add(key)
            dedup.append(n)
    known = dedup

    # Try matching against known disease names from context/evidence first
    for candidate in known:
        cand_norm = _normalize_for_match(candidate)
        if not cand_norm:
            continue
        # Check if any alias of the raw name matches this known disease
        raw_aliases = _disease_aliases(raw_name)
        cand_aliases = _disease_aliases(candidate)
        if raw_aliases & cand_aliases:
            return candidate

    best_name = raw_name
    best_score = 0.0
    raw_tokens = _token_set(raw_norm)
    for candidate in known:
        cand_norm = _normalize_for_match(candidate)
        if not cand_norm:
            continue
        if raw_norm in cand_norm or cand_norm in raw_norm:
            return candidate
        cand_tokens = _token_set(cand_norm)
        if not raw_tokens or not cand_tokens:
            continue
        overlap = len(raw_tokens.intersection(cand_tokens)) / max(1, len(raw_tokens.union(cand_tokens)))
        if overlap > best_score:
            best_score = overlap
            best_name = candidate

    if best_score >= 0.25:
        return best_name
    if known:
        return known[0]
    return raw_name


def _find_doc_for_disease(context_docs, disease_ar: str, disease_en: str):
    for doc in context_docs or []:
        metadata = getattr(doc, "metadata", {}) or {}
        if metadata.get("disease_name_ar") == disease_ar or metadata.get("disease_name_en") == disease_en:
            return doc
    return context_docs[0] if context_docs else None


def _build_final_response(disease_ar, disease_en, top_doc, lang="ar"):
    if not disease_ar and not disease_en:
        if lang == "en":
            return "Not enough data for a reliable diagnosis. Please upload a clearer image or describe the symptoms."
        return "لا توجد بيانات كافية لإخراج تشخيص موثوق. يُفضّل رفع صورة أوضح وذكر الأعراض النصية."

    meta = getattr(top_doc, "metadata", {}) if top_doc else {}

    if lang == "en":
        pathogen = (meta or {}).get("pathogen_type_en", "")
        description = (meta or {}).get("short_description_en", "")
        cause_parts = [p for p in [pathogen, description] if p]
        cause = " — ".join(cause_parts) if cause_parts else "Cause not currently available."

        treatment_organic = (meta or {}).get("treatment_organic_ar", "")
        treatment_chemical = (meta or {}).get("treatment_chemical_ar", "")
        treatment_summary = (meta or {}).get("treatment_summary_en", "")
        treatment_lines = []
        if treatment_summary:
            treatment_lines.append(treatment_summary)
        else:
            if treatment_organic:
                treatment_lines.append(f"• **Organic:** {treatment_organic}")
            if treatment_chemical:
                treatment_lines.append(f"• **Chemical:** {treatment_chemical}")
        treatment = "\n".join(treatment_lines) if treatment_lines else "Detailed treatment not available in the current database."

        disease_display = disease_en or disease_ar
        lines = [
            f"🌱 **Disease:** {disease_display}",
            f"🔬 **Cause:** {cause}",
            f"💊 **Treatment:**\n{treatment}",
        ]
    else:
        pathogen = (meta or {}).get("pathogen_type_ar", "")
        description = (meta or {}).get("short_description_ar", "")
        cause_parts = [p for p in [pathogen, description] if p]
        cause = " — ".join(cause_parts) if cause_parts else "السبب غير متوفر حاليًا."

        treatment_organic = (meta or {}).get("treatment_organic_ar", "")
        treatment_chemical = (meta or {}).get("treatment_chemical_ar", "")
        treatment_lines = []
        if treatment_organic:
            treatment_lines.append(f"• **عضوي:** {treatment_organic}")
        if treatment_chemical:
            treatment_lines.append(f"• **كيميائي:** {treatment_chemical}")
        treatment = "\n".join(treatment_lines) if treatment_lines else "العلاج التفصيلي غير متوفر في قاعدة البيانات الحالية."

        disease_display = disease_ar or disease_en
        lines = [
            f"🌱 **المرض:** {disease_display}",
            f"🔬 **السبب:** {cause}",
            f"💊 **العلاج:**\n{treatment}",
        ]
    return "\n\n".join(lines)


def encode_image(image_path: str):
    """Read any image format and normalize it to JPEG for VLM compatibility."""
    with Image.open(image_path) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=92)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def vision_agent(state: State):
    image_path = state.get("image_path")
    query = state.get("query", "")
    crop_type = state.get("crop_type", "")

    if not image_path:
        return {"vision_description": f"Crop: {crop_type}. {query}".strip(), "vision_error": None}

    try:
        base64_image = encode_image(image_path)
        crop_hint = f"\nTarget crop: {crop_type}." if crop_type else ""
        message = HumanMessage(
            content=[
                {"type": "text", "text": VISION_PROMPT + crop_hint},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
            ]
        )
        response = vision_llm.invoke([message])
        vision_desc = response.content.strip()
        print(f"👁️ Vision Analysis: {vision_desc}")
        return {"vision_description": vision_desc, "vision_error": None}
    except Exception as e:
        print(f"❌ Error in vision_agent: {e}")
        fallback_desc = f"Crop: {crop_type}. {query}".strip() if query else "Error analyzing image."
        return {"vision_description": fallback_desc, "vision_error": str(e)}


def retriever_agent(state: State):
    vision_desc = state.get("vision_description")
    crop_type = state.get("crop_type")
    retrieval_mode = state.get("retrieval_mode")
    k = to_int(state.get("retrieval_k"), to_int(os.getenv("RETRIEVAL_K", 4), 4))
    try:
        if not vision_desc:
            return {"context": []}
        result = _retrieve_context(
            query=vision_desc,
            crop_type=crop_type,
            retrieval_mode=retrieval_mode,
            k=k,
        )
        return {"context": result}
    except Exception as e:
        print(f"❌ Error in retriever_agent: {e}")
        return {"context": []}


def response_agent(state: State):
    context = state.get("context")
    disease_ar = state.get("decision_disease_ar", "")
    disease_en = state.get("decision_disease_en", "")
    lang = state.get("ui_lang", "ar")

    if (not disease_ar and not disease_en) and (context or []):
        fallback_meta = getattr(context[0], "metadata", {}) or {}
        disease_ar = fallback_meta.get("disease_name_ar", "")
        disease_en = fallback_meta.get("disease_name_en", "")

    final_disease = state.get("final_disease")
    if final_disease:
        disease_en = final_disease

    top_doc = _find_doc_for_disease(context, disease_ar, disease_en)
    response_text = _build_final_response(
        disease_ar=disease_ar,
        disease_en=disease_en,
        top_doc=top_doc,
        lang=lang,
    )

    return {"response": response_text}


def verify_agent(state: State):
    plantnet_data = state.get("plantnet_data") or {}
    diseases = []
    if isinstance(plantnet_data, dict):
        diseases = plantnet_data.get("diseases") or []

    best_plantnet = None
    for item in diseases:
        if not isinstance(item, dict):
            continue
        conf = _normalize_confidence(item.get("confidence", 0.0))
        if conf >= 0.7:
            if best_plantnet is None or conf > best_plantnet["confidence"]:
                best_plantnet = {"name": item.get("name", ""), "confidence": conf}

    if best_plantnet and best_plantnet.get("name"):
        canonical_name = _canonicalize_disease_name(best_plantnet["name"], state)
        return {
            "final_disease": canonical_name,
            "final_confidence": best_plantnet["confidence"],
            "source": "PlantNet",
            "verification_status": "confirmed",
            "verification_result": "Final decision selected from PlantNet diseases (>= 0.7).",
        }

    evidence_data = state.get("evidence_data")
    if not evidence_data:
        evidence_data = []
        for row in state.get("symptom_scores") or []:
            evidence_data.append(
                {
                    "name": row.get("disease_name_en") or row.get("disease_name_ar"),
                    "confidence": _normalize_confidence(row.get("score", 0)),
                }
            )

    best_evidence = None
    for item in evidence_data:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        conf = _normalize_confidence(item.get("confidence", 0.0))
        if not name:
            continue
        if best_evidence is None or conf > best_evidence["confidence"]:
            best_evidence = {"name": name, "confidence": conf}

    if best_evidence:
        return {
            "final_disease": best_evidence["name"],
            "final_confidence": best_evidence["confidence"],
            "source": "Knowledge Base",
            "verification_status": "unknown",
            "verification_result": "Final decision selected from evidence fallback.",
        }

    return {
        "final_disease": None,
        "final_confidence": 0.0,
        "source": "Knowledge Base",
        "verification_status": "unknown",
        "verification_result": "No PlantNet or evidence candidates were available.",
    }


def plantnet_agent(state: State):
    image_path = state.get("image_path")
    expected_disease = state.get("decision_disease_en") or state.get("decision_disease_ar") or ""
    status, result, diseases = _plantnet_disease_verify(
        image_path=image_path,
        expected_disease=expected_disease,
    )
    return {
        "plantnet_status": status,
        "plantnet_result": result,
        "plantnet_data": {"diseases": diseases},
    }


def evidence_agent(state: State):
    vision_desc = state.get("vision_description", "")
    context = state.get("context") or []
    crop_type = state.get("crop_type", "plant")
    suspected_disease = _extract_suspected_disease(context)

    scores = _score_context_matches(vision_desc, context)
    top = scores[0] if scores else {}
    decision_disease_ar = top.get("disease_name_ar") or ""
    decision_disease_en = top.get("disease_name_en") or suspected_disease or ""
    web_evidence = _search_web_evidence(decision_disease_en, crop_type, max_items=3)

    evidence_data = []
    for row in scores:
        evidence_data.append(
            {
                "name": row.get("disease_name_en") or row.get("disease_name_ar"),
                "confidence": _normalize_confidence(row.get("score", 0)),
            }
        )

    return {
        "symptom_scores": scores,
        "web_evidence": web_evidence,
        "evidence_data": evidence_data,
        "decision_disease_ar": decision_disease_ar,
        "decision_disease_en": decision_disease_en,
    }


def chat_response(user_message: str, crop_type: str = None, chat_history: list = None, lang: str = "ar"):
    try:
        from infrastructure.prompts import chat_prompt_extend

        k = to_int(os.getenv("RETRIEVAL_K", 4), 4)
        retrieval_mode = os.getenv("RETRIEVAL_MODE", "mmr")
        context_docs = _retrieve_context(query=user_message, crop_type=crop_type, retrieval_mode=retrieval_mode, k=k)

        content = _format_retrieved_context(context_docs)

        # Build a short chat history string for context
        history_lines = []
        if chat_history:
            for msg in chat_history[-6:]:
                role = "المستخدم" if msg.get("role") == "user" else "المساعد"
                text = msg.get("content", "")[:200]
                if text:
                    history_lines.append(f"{role}: {text}")
        history_str = "\n".join(history_lines)

        prompt = chat_prompt_extend(
            user_message=user_message,
            content=content,
            chat_history=history_str,
            lang=lang,
        )

        message = HumanMessage(content=prompt)
        response = text_llm.invoke([message])
        text = getattr(response, "content", str(response)).strip()
        return {"text": text, "context_count": len(context_docs or [])}
    except Exception as e:
        return {"text": f"خطأ في الشات: {e}", "context_count": 0}
