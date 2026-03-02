from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DB_DIR = str(BASE_DIR / "chroma_db")
DATA_JSON_FILES = sorted(BASE_DIR.glob("data_*.json"))
