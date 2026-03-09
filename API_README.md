# 🌿 Plant Disease API — React Integration Guide

> Complete API documentation for integrating with React frontend.

---

## 📌 Backend Info

| Item             | Value                          |
| ---------------- | ------------------------------ |
| **Framework**    | FastAPI 0.115.6                |
| **Python**       | 3.11.10                        |
| **Base URL**     | `http://localhost:8000`        |
| **Content-Type** | `multipart/form-data` (POST)   |
| **Version**      | 2.0.0                          |

---

## 🚀 Running the Backend

**Using venv:**

```bash
# 1. Make sure Python 3.11 is installed
python3.11 --version

# 2. Create a virtual environment
python3.11 -m venv venv

# 3. Activate it
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate          # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file with your API keys
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# 6. Build the knowledge base (run once)
python infrastructure/create_db.py

# 7. Start the server
uvicorn api:app --reload --port 8000
```

The server will be available at `http://localhost:8000`

---

## 📡 API Endpoints

### 1. Health Check ✅

```
GET /api/health
```

**Response:**

```json
{ 
  "status": "ok", 
  "db_ready": true 
}
```

**Usage:** Check if backend is running and database is ready before allowing user interactions.

---

### 2. List Available Crops 🌾

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

**Usage:** 
- Display crop selection dropdown with `name_ar` or `name_en`
- User **must** select a crop before chatting or uploading images
- Use the `slug` value as `crop_type` parameter in subsequent API calls

---

### 3. Text Chat 💬

```
POST /api/chat
Content-Type: multipart/form-data
```

**Form Fields:**

| Field          | Type   | Required | Default | Description                                       |
| -------------- | ------ | -------- | ------- | ------------------------------------------------- |
| `message`      | string | ✅       | -       | User's text message                               |
| `crop_type`    | string | ❌       | `""`    | Crop slug from `/api/crops` (optional - for more specific answers) |
| `lang`         | string | ❌       | `"ar"`  | Response language: `"ar"` or `"en"`               |
| `chat_history` | string | ❌       | `"[]"`  | JSON string of previous messages array            |

**Response:**

```json
{
  "success": true,
  "reply": "Late blight is caused by Phytophthora infestans...",
  "crop_type": "tomato"
}
```

**Example (JavaScript):**

```js
const formData = new FormData();
formData.append("message", "ما هو مرض اللفحة المتأخرة؟");
formData.append("crop_type", "tomato"); // optional - can be empty for general questions
formData.append("lang", "ar");
formData.append("chat_history", JSON.stringify(chatHistory));

const res = await fetch("http://localhost:8000/api/chat", {
  method: "POST",
  body: formData,
});
const data = await res.json();
console.log(data.reply);
```

---

### 4. Image Analysis 📸

```
POST /api/analyze
Content-Type: multipart/form-data
```

**Form Fields:**

| Field          | Type   | Required | Default | Description                                       |
| -------------- | ------ | -------- | ------- | ------------------------------------------------- |
| `image`        | file   | ✅       | -       | Plant image (jpg, jpeg, png)                      |
| `crop_type`    | string | ✅       | -       | Crop slug from `/api/crops`                       |
| `lang`         | string | ❌       | `"ar"`  | Response language: `"ar"` or `"en"`               |
| `message`      | string | ❌       | `""`    | Optional question about the image                 |

**Response:**

```json
{
  "success": true,
  "reply": "🌱 **المرض:** اللفحة المتأخرة\n\n🔬 **السبب:** فطر Phytophthora infestans...\n\n💊 **العلاج:** ...",
  "crop_type": "tomato",
  "details": {
    "symptom_scores": [
      {
        "disease_name_ar": "اللفحة المتأخرة",
        "disease_name_en": "Late Blight",
        "score": 95
      }
    ],
    "plantnet_result": "...",
    "web_evidence": [
      {
        "title": "Late Blight Management",
        "url": "https://..."
      }
    ],
    "verification_result": "...",
    "source": "...",
    "vision_error": false
  }
}
```

**Example (JavaScript):**

```js
const formData = new FormData();
formData.append("image", fileInput.files[0]);
formData.append("crop_type", selectedCrop);
formData.append("lang", "ar");
formData.append("message", ""); // optional

const res = await fetch("http://localhost:8000/api/analyze", {
  method: "POST",
  body: formData,
});
const data = await res.json();

// Display main reply
console.log(data.reply);

// Show details in expandable section
console.log(data.details.symptom_scores);
```

---

### 5. Build Database (Admin) 🔧

```
POST /api/build-db
```

**Response:**

```json
{
  "success": true,
  "message": "Database built successfully"
}
```

**Usage:** Only needed if database is not ready (when `db_ready: false` in health check).

---

## 🎯 Complete React Integration Flow

### Step 1: App Initialization

```js
// On app mount
useEffect(() => {
  // Check health
  fetch("http://localhost:8000/api/health")
    .then(res => res.json())
    .then(data => {
      if (!data.db_ready) {
        alert("Database not ready! Contact admin.");
      }
    });

  // Load crops
  fetch("http://localhost:8000/api/crops")
    .then(res => res.json())
    .then(data => {
      setCrops(data.crops);
    });
}, []);
```

### Step 2: Text Chat (Crop Optional)

```js
// Text chat - crop_type is optional
const sendMessage = async (message) => {
  const formData = new FormData();
  formData.append("message", message);
  formData.append("crop_type", selectedCrop || ""); // optional
  formData.append("lang", lang);
  formData.append("chat_history", JSON.stringify(chatHistory));

  const res = await fetch("http://localhost:8000/api/chat", {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  
  // Add to chat history
  setChatHistory([
    ...chatHistory,
    { role: "user", content: message },
    { role: "assistant", content: data.reply }
  ]);
};
```

### Step 3: Image Upload (Crop Required)

```js
// Image analysis - crop_type is REQUIRED
const handleImageUpload = (imageFile) => {
  // Check if crop is selected
  if (!selectedCrop) {
    // Show modal/popup to select crop first
    setShowCropSelector(true);
    setPendingImage(imageFile);
    return;
  }
  
  analyzeImage(imageFile);
};

const analyzeImage = async (imageFile) => {
  const formData = new FormData();
  formData.append("image", imageFile);
  formData.append("crop_type", selectedCrop); // required!
  formData.append("lang", lang);

  setLoading(true);
  const res = await fetch("http://localhost:8000/api/analyze", {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  setLoading(false);

  // Display result
  setAnalysisResult(data);
  
  // Add to chat
  setChatHistory([
    ...chatHistory,
    { role: "user", content: "[صورة تم رفعها]", image: URL.createObjectURL(imageFile) },
    { role: "assistant", content: data.reply }
  ]);
};
```

---

## 💬 Chat History Format

```js
const chatHistory = [
  { role: "user", content: "ما هو مرض اللفحة المتأخرة؟" },
  { role: "assistant", content: "اللفحة المتأخرة هو مرض..." },
  { role: "user", content: "كيف أعالجه؟" },
  { role: "assistant", content: "العلاج يشمل..." }
];

// Send as JSON string
formData.append("chat_history", JSON.stringify(chatHistory));
```

- Only the **last 6 messages** are used for context
- `role`: `"user"` or `"assistant"`
- `content`: Message text (Markdown supported)

---

## 🌐 CORS

CORS is configured to allow all origins (`*`), so you can run React on any port:

```
✅ http://localhost:3000
✅ http://localhost:5173
✅ http://127.0.0.1:3000
```

---

## ⚠️ Error Handling

| Status | Error                                              | Action                                    |
| ------ | -------------------------------------------------- | ----------------------------------------- |
| `200`  | Success                                            | Display `reply`                           |
| `400`  | Missing required fields                            | Show error message to user                |
| `503`  | Database not ready                                 | Contact backend admin                     |
| `500`  | Internal server error                              | Retry or contact support                  |

**Example:**

```js
try {
  const res = await fetch("http://localhost:8000/api/chat", {
    method: "POST",
    body: formData,
  });
  
  if (!res.ok) {
    const error = await res.json();
    alert(error.detail);
    return;
  }
  
  const data = await res.json();
  // Use data.reply
} catch (e) {
  console.error("Network error:", e);
  alert("فشل الاتصال بالخادم");
}
```

---

## 📝 Important Notes

1. **Markdown Rendering**: All responses are in Markdown format. Use `react-markdown` or similar library:
   ```bash
   npm install react-markdown
   ```

2. **Image Formats**: Supported formats are JPG, JPEG, PNG.

3. **Language**: Send `lang: "ar"` for Arabic or `lang: "en"` for English. The entire response will be in that language.

4. **Crop Selection**: User **must** select crop before any interaction. This is enforced by requiring `crop_type` in all endpoints.

5. **Details Object**: The `/api/analyze` endpoint returns a `details` object with additional information:
   - `symptom_scores`: Array of possible diseases with confidence scores
   - `plantnet_result`: Plant verification result
   - `web_evidence`: Related articles/resources
   - Use these for "Show Details" or "More Info" sections in your UI

---

## 🔑 Environment Variables (Backend)

| Variable            | Required | Description                              |
| ------------------- | -------- | ---------------------------------------- |
| `GROQ_API_KEY`      | ✅       | Groq API key (required for AI)           |
| `PLANTNET_API_KEY`  | ❌       | PlantNet verification (optional)         |
| `TAVILY_API_KEY`    | ❌       | Additional web search (optional)         |
| `RETRIEVAL_MODE`    | ❌       | `mmr` or `similarity` (default: `mmr`)   |
| `RETRIEVAL_K`       | ❌       | Number of docs to retrieve (default: 4)  |

---

## 🎨 Suggested UI Flow

```
┌─────────────────────────────────────────┐
│  1. Language Selection (ar/en)          │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  2. Chat Interface (Direct Access)      │
│     ┌─────────────────────────────────┐ │
│     │  Chat History                   │ │
│     │  (Messages)                     │ │
│     └─────────────────────────────────┘ │
│                                         │
│     [💬 Text Input]  (always available) │
│     [📸 Upload Image] ← if no crop →   │
│                         show selector   │
└─────────────────────────────────────────┘
                ↓
        (when uploading image)
                ↓
┌─────────────────────────────────────────┐
│  3. Crop Selection Modal/Popup          │
│     "Please select crop first"          │
│     [Dropdown with crop names]          │
│     [Confirm & Analyze]                 │
└─────────────────────────────────────────┘
```

**Key Points:**
- Chat is available immediately (no forced crop selection)
- Crop becomes required only when uploading an image
- Once crop is selected, it's remembered for subsequent images

---

## 🧪 Testing the API

You can test the API using `curl` or Postman:

**List crops:**
```bash
curl http://localhost:8000/api/crops
```

**Text chat:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -F "message=What is late blight?" \
  -F "crop_type=tomato" \
  -F "lang=en"
```

**Image analysis:**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "image=@/path/to/image.jpg" \
  -F "crop_type=tomato" \
  -F "lang=en"
```

---

## 📞 Support

If you have any questions about the API integration, contact the backend team or refer to the FastAPI auto-generated docs at:

```
http://localhost:8000/docs
```

---

**Good luck with your React integration! 🚀**
