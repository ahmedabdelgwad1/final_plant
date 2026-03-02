# Plant Disease Diagnosis Assistant

AI-powered plant disease diagnosis system that combines **computer vision**, a **vector knowledge base**, and **web evidence** to identify crop diseases from leaf images. Includes a **chatbot UI** (Streamlit) and a **REST API** (FastAPI) for frontend integration.

## Features

- **Chat Interface** – Conversational chatbot; send text or upload images and get diagnosis inside the conversation.
- **REST API** – Single unified `/api/chat` endpoint for React / mobile / any frontend.
- **Image Analysis** – Upload a leaf photo; the vision model extracts visual symptoms automatically.
- **Knowledge Base** – Diseases matched against a ChromaDB vector store built from structured JSON data (5 crops, 21 diseases).
- **PlantNet Verification** – Optional cross-check with the PlantNet disease API.
- **Web Evidence** – Fetches trusted agricultural sources (Tavily) to support the diagnosis.
- **Bilingual** – Full Arabic and English support (UI + API responses).
- **Follow-up Chat** – Ask follow-up questions about the diagnosed disease or treatment.

## Supported Crops

| Crop | Diseases |
|---|---|
| Apple | 4 |
| Potato | 4 |
| Rice | 4 |
| Tomato | 3 |
| Wheat | 6 |

## Project Structure

```
app.py                  # Streamlit chatbot UI
api.py                  # FastAPI REST API for frontend integration
config.py               # Paths & constants
requirements.txt        # Python dependencies
.env.example            # Environment variables template
data_apple.json         # Apple disease knowledge
data_potato.json        # Potato disease knowledge
data_rice.json          # Rice disease knowledge
data_tomato.json        # Tomato disease knowledge
data_wheat.json         # Wheat disease knowledge
application/
  workflow.py           # LangGraph workflow definition
domain/
  models.py             # State schema (TypedDict)
infrastructure/
  agents.py             # Vision, retrieval, evidence, PlantNet & response agents
  create_db.py          # Build ChromaDB from data_*.json files
  prompts.py            # LLM prompt templates (AR + EN)
shared/
  i18n.py               # Arabic / English UI translations
  utils.py              # Utility helpers
```

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/<your-username>/plant-disease-assistant.git
cd plant-disease-assistant
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (required)
# Optionally add TAVILY_API_KEY and PLANTNET_API_KEY
```

### 3. Build Knowledge Base

```bash
python -c "from infrastructure.create_db import create_database; create_database()"
```

### 4. Run Streamlit UI

```bash
streamlit run app.py
```

### 5. Run REST API (for React / frontend integration)

```bash
uvicorn api:app --reload --port 8000
```

## API Endpoints

### `GET /api/health`
Health check. Returns `{"status": "ok", "db_ready": true}`.

### `GET /api/crops`
List available crops. Returns:
```json
{"crops": [{"slug": "apple", "name_ar": "تفاح", "name_en": "Apple"}, ...]}
```

### `POST /api/chat` (FormData)
Unified chat endpoint — handles both text chat and image diagnosis.

| Field | Type | Required | Description |
|---|---|---|---|
| `message` | text | No* | User's text message |
| `image` | file | No* | Leaf image for diagnosis |
| `crop_type` | text | No | Crop slug (e.g. `apple`, `tomato`) |
| `lang` | text | No | `ar` or `en` (default: `ar`) |
| `chat_history` | text | No | JSON string of previous messages |

\* At least one of `message` or `image` is required.

**Response:**
```json
{"reply": "The response text"}
```

**Scenarios:**
- **Text only** → conversational reply
- **Image + crop_type** → disease diagnosis (disease + cause + treatment)
- **Image without crop_type** → asks user to select crop first

## Adding New Crops

1. Create a `data_<crop>.json` file following the same schema as `data_tomato.json`.
2. Rebuild the knowledge base (run step 3 above or click "Build" in Streamlit).

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key for LLM inference |
| `TAVILY_API_KEY` | No | Tavily API key for web evidence search |
| `PLANTNET_API_KEY` | No | PlantNet API key for disease verification |
| `GROQ_VISION_MODEL` | No | Vision model (default: `llama-3.2-11b-vision-preview`) |
| `GROQ_TEXT_MODEL` | No | Text model (default: `llama-3.3-70b-versatile`) |
| `EMBEDDING_MODEL` | No | Embedding model (default: `BAAI/bge-base-en-v1.5`) |
| `RETRIEVAL_MODE` | No | `mmr`, `similarity`, or `hybrid` (default: `mmr`) |
| `RETRIEVAL_K` | No | Number of retrieved documents (default: `4`) |

## License

MIT
