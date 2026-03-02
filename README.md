# Plant Disease Diagnosis Assistant

AI-powered plant disease diagnosis system with a **chatbot interface** that combines **computer vision**, a **vector knowledge base**, and **web evidence** to identify crop diseases from leaf images.

## Features

- **Chat-first UI** – Conversational interface using `st.chat_message`; chat freely and get diagnosis results inside the conversation.
- **Image Analysis** – Upload a leaf photo; the vision model extracts visual symptoms automatically.
- **Knowledge Base Retrieval** – Diseases are matched against a ChromaDB vector store built from structured JSON data files.
- **PlantNet Verification** – Optional cross-check with the PlantNet disease API.
- **Web Evidence** – Fetches trusted agricultural sources (Tavily) to support the diagnosis.
- **Bilingual UI** – Full Arabic and English interface.
- **Follow-up Chat** – Ask follow-up questions about the diagnosed disease or treatment.

## Project Structure

```
app.py                  # Streamlit UI entry point
config.py               # Paths & constants
data_tomato.json        # Tomato disease knowledge
data_wheat.json         # Wheat disease knowledge
requirements.txt        # Python dependencies
application/
  workflow.py           # LangGraph workflow definition
domain/
  models.py             # State schema (TypedDict)
infrastructure/
  agents.py             # Vision, retrieval, evidence, PlantNet & response agents
  create_db.py          # Build ChromaDB from data_*.json files
  prompts.py            # LLM prompt templates
shared/
  i18n.py               # Arabic / English translations
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

### 3. Run

```bash
streamlit run app.py
```

On first launch, click **"Build Knowledge Base"** to index the disease data into ChromaDB.

## Adding New Crops

1. Create a `data_<crop>.json` file following the same schema as `data_tomato.json`.
2. Restart the app and rebuild the knowledge base.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key for LLM inference |
| `TAVILY_API_KEY` | No | Tavily API key for web evidence search |
| `PLANTNET_API_KEY` | No | PlantNet API key for disease verification |
| `GROQ_VISION_MODEL` | No | Vision model name (default: `llama-3.2-11b-vision-preview`) |
| `GROQ_TEXT_MODEL` | No | Text model name (default: `llama-3.3-70b-versatile`) |
| `EMBEDDING_MODEL` | No | HuggingFace embedding model (default: `BAAI/bge-base-en-v1.5`) |

## License

MIT
