import os
import json

from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from dotenv import load_dotenv
from config import CHROMA_DB_DIR, DATA_JSON_FILES
from shared.utils import slugify_crop

load_dotenv(override=True)


def _to_list(value):
    if isinstance(value, list):
        return [str(v) for v in value if v]
    if value:
        return [str(value)]
    return []


def _safe_join(values):
    return ", ".join([v for v in values if v])


def create_database():
    """Build the Chroma vector DB from all data_*.json files."""
    if not DATA_JSON_FILES:
        print("No data_*.json files found.")
        return

    documents = []
    for json_path in DATA_JSON_FILES:
        print(f"Reading {json_path.name} ...")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"  Error reading {json_path.name}: {e}")
            continue

        diseases = data.get("diseases", [])
        print(f"  Found {len(diseases)} diseases")

        for item in diseases:
            disease_name_en = item.get("disease_name_en", "")
            disease_name_ar = item.get("disease_name_ar", "")

            core_visual = item.get("core_visual_identity", {})
            visual_features = item.get("visual_features", {})

            short_description_en = item.get("short_description_en", "")
            short_description_ar = item.get("short_description_ar", "")

            features_en = _safe_join(
                _to_list(visual_features.get("colors_en"))
                + _to_list(visual_features.get("texture_en"))
                + _to_list(visual_features.get("shapes_en"))
                + _to_list(visual_features.get("locations_en"))
                + _to_list(visual_features.get("progression_en"))
            )
            features_ar = _safe_join(
                _to_list(visual_features.get("colors_ar"))
                + _to_list(visual_features.get("texture_ar"))
                + _to_list(visual_features.get("shapes_ar"))
                + _to_list(visual_features.get("locations_ar"))
                + _to_list(visual_features.get("progression_ar"))
            )

            common_en = _safe_join(_to_list(item.get("common_vlm_phrases_en")))
            common_ar = _safe_join(_to_list(item.get("common_vlm_phrases_ar")))
            confidence_words = _safe_join(_to_list(item.get("confidence_keywords")))

            content = (
                f"Disease EN: {disease_name_en}\n"
                f"Disease AR: {disease_name_ar}\n"
                f"Core visual EN: {core_visual.get('en', '')}\n"
                f"Core visual AR: {core_visual.get('ar', '')}\n"
                f"Short description EN: {short_description_en}\n"
                f"Short description AR: {short_description_ar}\n"
                f"Visual features EN: {features_en}\n"
                f"Visual features AR: {features_ar}\n"
                f"Common phrases EN: {common_en}\n"
                f"Common phrases AR: {common_ar}\n"
                f"Confidence keywords: {confidence_words}\n"
            )

            crop_type = (
                item.get("crop_type")
                or data.get("crop_type")
                or slugify_crop(data.get("crop_en", "unknown"))
            )

            metadata = {
                "id": item.get("id", ""),
                "crop_type": crop_type,
                "disease_name_ar": disease_name_ar,
                "disease_name_en": disease_name_en,
                "pathogen_type_ar": item.get("pathogen_type_ar", ""),
                "short_description_ar": item.get("short_description_ar", ""),
                "treatment_chemical_ar": item.get("treatment_chemical_ar", ""),
                "treatment_organic_ar": item.get("treatment_organic_ar", ""),
                "favorable_conditions_ar": item.get("favorable_conditions_ar", ""),
                "treatment_summary_ar": item.get("treatment_summary_ar", ""),
                "treatment_summary_en": item.get("treatment_summary_en", ""),
            }

            documents.append(Document(page_content=content, metadata=metadata))

    print(f"Total documents: {len(documents)}")

    embedding_model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
    print(f"Embedding model: {embedding_model}")
    embedding = HuggingFaceEmbeddings(model_name=embedding_model)

    try:
        if os.path.exists(CHROMA_DB_DIR):
            import shutil
            shutil.rmtree(CHROMA_DB_DIR)
            print("Removed old database")

        Chroma.from_documents(
            documents=documents,
            embedding=embedding,
            persist_directory=CHROMA_DB_DIR,
        )
        print("Database created successfully!")
    except Exception as e:
        print(f"Error creating database: {e}")


if __name__ == "__main__":
    create_database()
