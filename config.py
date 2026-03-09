import os
from pathlib import Path
from dotenv import load_dotenv

# Force load .env if it exists (mostly for local development)
load_dotenv(override=True)

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Data files paths
DATA_JSON_FILES = [
    DATA_DIR / "data_apple.json",
    DATA_DIR / "data_potato.json",
    DATA_DIR / "data_rice.json",
    DATA_DIR / "data_tomato.json",
    DATA_DIR / "data_wheat.json"
]

# Ensure CHROMA_DB_DIR exists
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)
