# 🌿 Plant Disease API — React Integration Guide

> This file is for the React developer to integrate the frontend with the backend API.

---

## 📌 Backend Info

| Item             | Value                          |
| ---------------- | ------------------------------ |
| **Framework**    | FastAPI 0.115.6                |
| **Python**       | 3.11.10                        |
| **Base URL**     | `http://localhost:8000`        |
| **Content-Type** | `multipart/form-data` (POST)   |

---

## 🚀 Running the Backend

```bash
# 1. Make sure Python 3.11 is installed
python3.11 --version

# 2. Install dependencies
pip install -r requirements.txt

# 3. Build the knowledge base (run once)
python infrastructure/create_db.py

# 4. Start the server
uvicorn api:app --reload --port 8000
```

The server will be available at `http://localhost:8000`

---

## 📡 API Endpoints

### 1. Health Check

```
GET /api/health
```

**Response:**

```json
{ "status": "ok", "db_ready": true }
```

---

### 2. List Available Crops

```
GET /api/crops
```

**Response:**

```json
{
  "crops": [
    { "slug": "tomato", "name_ar": "طماطم", "name_en": "Tomato" },
    { "slug": "wheat",  "name_ar": "قمح",   "name_en": "Wheat" },
    { "slug": "potato", "name_ar": "بطاطس", "name_en": "Potato" },
    { "slug": "rice",   "name_ar": "أرز",   "name_en": "Rice" },
    { "slug": "apple",  "name_ar": "تفاح",  "name_en": "Apple" }
  ]
}
```

> Use the `slug` value as the `crop_type` when sending an image.

---

### 3. Chat (Main Endpoint)

```
POST /api/chat
Content-Type: multipart/form-data
```

**Form Fields:**

| Field          | Type   | Required | Default | Description                                       |
| -------------- | ------ | -------- | ------- | ------------------------------------------------- |
| `message`      | string | ❌       | `""`    | User's text message                               |
| `image`        | file   | ❌       | `null`  | Plant image (jpg, png, webp)                      |
| `crop_type`    | string | ❌       | `""`    | Crop slug — required when sending an image        |
| `lang`         | string | ❌       | `"ar"`  | Response language: `"ar"` or `"en"`               |
| `chat_history` | string | ❌       | `"[]"`  | JSON string of previous messages array            |

**Response (always):**

```json
{ "reply": "..." }
```

---

## 🔀 Three Scenarios

### Scenario 1: Text Only (Chat)

```js
const formData = new FormData();
formData.append("message", "What is the most dangerous tomato disease?");
formData.append("lang", "en");
formData.append("chat_history", JSON.stringify(chatHistory));

const res = await fetch("http://localhost:8000/api/chat", {
  method: "POST",
  body: formData,
});
const data = await res.json();
console.log(data.reply);
```

### Scenario 2: Image + Crop (Diagnosis)

```js
const formData = new FormData();
formData.append("image", fileInput.files[0]);
formData.append("crop_type", "tomato");
formData.append("lang", "en");
formData.append("message", ""); // optional text with image

const res = await fetch("http://localhost:8000/api/chat", {
  method: "POST",
  body: formData,
});
const data = await res.json();
console.log(data.reply);
// → 🌱 **Disease:** Late Blight
// → 🔬 **Cause:** Phytophthora infestans — ...
// → 💊 **Treatment:** ...
```

### Scenario 3: Image Without Crop

```js
const formData = new FormData();
formData.append("image", fileInput.files[0]);
// crop_type is missing!

const res = await fetch("http://localhost:8000/api/chat", {
  method: "POST",
  body: formData,
});
const data = await res.json();
console.log(data.reply);
// → "Please select the crop type first."
```

> The API will ask the user to select a crop — show a dropdown populated from `/api/crops`.

---

## 💬 Chat History Format

Send `chat_history` as a JSON string containing an array of messages:

```js
const chatHistory = [
  { role: "user", content: "What is late blight?" },
  { role: "assistant", content: "Late blight is a disease caused by..." },
  { role: "user", content: "How do I treat it?" },
];

formData.append("chat_history", JSON.stringify(chatHistory));
```

- `role`: `"user"` or `"assistant"`
- `content`: The message text
- The backend only uses the **last 6 messages** for context

---

## 🌐 CORS

CORS is open for all origins (`*`), so you can run React on any port:

```
http://localhost:3000  ✅
http://localhost:5173  ✅
http://127.0.0.1:3000  ✅
```

---

## ⚠️ Error Handling

| Status | Meaning                                            |
| ------ | -------------------------------------------------- |
| `200`  | Success — response is in `reply`                   |
| `400`  | No message or image was sent                       |
| `503`  | Knowledge base not built yet (run `create_db.py`)  |

```js
try {
  const res = await fetch("http://localhost:8000/api/chat", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json();
    console.error(err.detail);
    return;
  }
  const data = await res.json();
  // use data.reply
} catch (e) {
  console.error("Network error:", e);
}
```

---

## 🧩 Suggested React Flow

```
1. App loads → GET /api/crops → populate crop dropdown
2. User types a message → POST /api/chat (text only)
3. User uploads an image → show crop dropdown
4. User selects crop + sends → POST /api/chat (image + crop)
5. Display reply (supports Markdown — use react-markdown)
6. Keep chat_history array in state, send it with each request
```

---

## 📝 Notes

- The response is **Markdown** formatted — use `react-markdown` to render it.
- Supported image formats: **JPG, PNG, WebP**.
- `lang` accepts `"ar"` (Arabic) or `"en"` (English) — controls the entire response language.
- If there's an issue with the image, the response will include a `⚠️` warning.
- A `.env` file must exist in the backend root with at least `GROQ_API_KEY`.

---

## 🔑 Environment Variables (Backend)

| Variable            | Required | Description                              |
| ------------------- | -------- | ---------------------------------------- |
| `GROQ_API_KEY`      | ✅       | Groq API key (required)                  |
| `PLANTNET_API_KEY`  | ❌       | PlantNet verification (optional)         |
| `TAVILY_API_KEY`    | ❌       | Additional web search (optional)         |

> The backend is my responsibility — you don't need to modify it. Just run it and use the API.
