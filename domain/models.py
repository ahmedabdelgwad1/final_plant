from typing import Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph import add_messages


class State(TypedDict, total=False):
    chat_history: Annotated[list, add_messages]
    crop_type: Optional[str]
    retrieval_mode: Optional[str]
    retrieval_k: Optional[int]
    query: Optional[str]
    image_path: Optional[str]
    ui_lang: Optional[str]
    vision_description: str
    vision_error: Optional[str]
    context: Optional[list]
    response: str
    verification_status: Optional[str]
    verification_result: Optional[str]
    symptom_scores: Optional[list[dict]]
    web_evidence: Optional[list[dict]]
    decision_disease_ar: Optional[str]
    decision_disease_en: Optional[str]
    plantnet_status: Optional[str]
    plantnet_result: Optional[str]
    plantnet_data: Optional[dict]
    evidence_data: Optional[list[dict]]
    final_disease: Optional[str]
    final_confidence: Optional[float]
    source: Optional[str]