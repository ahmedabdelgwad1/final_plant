# 🎯 Frontend Integration Guide - Plant Disease Diagnosis System

**Version:** 1.0  
**Last Updated:** March 9, 2026  
**Target Audience:** React Developer

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Environment Setup](#environment-setup)
3. [API Endpoints Specification](#api-endpoints-specification)
4. [Critical Integration Rules](#critical-integration-rules)
5. [Complete React Component](#complete-react-component)
6. [Common Pitfalls & Troubleshooting](#common-pitfalls--troubleshooting)
7. [Testing Checklist](#testing-checklist)

---

## 🏗️ Architecture Overview

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                     React Frontend                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • Chat Interface                                    │   │
│  │  • Image Upload with Crop Selection                 │   │
│  │  • Markdown Rendering (react-markdown)              │   │
│  │  • State Management (chat history)                  │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ HTTP (FormData)
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  • /api/crops (GET)    - List available crops       │   │
│  │  • /api/chat (POST)    - Text chat (optional crop)  │   │
│  │  • /api/analyze (POST) - Image analysis (+ crop)    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  LangGraph + Groq AI + ChromaDB Vector Store        │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

### Key Components

- **FastAPI Backend:** Python-based REST API running on port 8000
- **LangGraph:** Orchestrates the AI workflow for disease diagnosis
- **Groq API:** LLM provider for generating responses
- **ChromaDB:** Vector database storing plant disease knowledge
- **CORS Enabled:** All origins allowed for development

---

## 🔧 Environment Setup

### Backend Setup

```bash
# Navigate to project directory
cd /Users/apple/Desktop/final_plant

# Activate virtual environment
source venv/bin/activate
# OR if using conda
# conda activate plant_disease

# Start the FastAPI server
uvicorn api:app --reload --port 8000
```

**Verify Backend is Running:**
```bash
curl http://localhost:8000/api/health
# Expected: {"status":"ok","db_ready":true}
```

**Interactive API Docs:**
- Open `http://localhost:8000/docs` in browser

---

### Frontend Setup

#### 1. Install Dependencies

```bash
npm install react-markdown
# OR
yarn add react-markdown
```

#### 2. Configure Environment Variables

**Create `.env` file in your React project root:**

**For Vite:**
```env
VITE_API_URL=http://localhost:8000
```

**For Create React App:**
```env
REACT_APP_API_URL=http://localhost:8000
```

**⚠️ IMPORTANT:** 
- **Vite:** Environment variables MUST start with `VITE_`
- **CRA:** Environment variables MUST start with `REACT_APP_`
- Restart dev server after changing `.env`

#### 3. Access Environment Variables

```jsx
// Works for both Vite and CRA
const API_URL = import.meta.env.VITE_API_URL || process.env.REACT_APP_API_URL;

// Always provide fallback
if (!API_URL) {
  console.error("API_URL not configured in .env file!");
}
```

---

## 📡 API Endpoints Specification

### 1. Get Available Crops

**Endpoint:** `GET /api/crops`

**Purpose:** Retrieve list of supported crops for dropdown selection

**Request:**
```jsx
const response = await fetch(`${API_URL}/api/crops`);
const data = await response.json();
```

**Response:**
```json
{
  "crops": [
    {
      "slug": "tomato",
      "name_ar": "طماطم",
      "name_en": "Tomato"
    },
    {
      "slug": "potato",
      "name_ar": "بطاطس",
      "name_en": "Potato"
    }
    // ... more crops
  ]
}
```

**Usage:**
- Call on component mount to populate crop selector dropdown
- Store in state for crop selection

---

### 2. Text Chat Endpoint

**Endpoint:** `POST /api/chat`

**Purpose:** Send text messages and receive AI-powered responses

**Parameters (FormData):**

| Parameter     | Type   | Required | Description                                      |
|---------------|--------|----------|--------------------------------------------------|
| `message`     | string | ✅ Yes   | User's text message                              |
| `crop_type`   | string | ❌ No    | Crop slug (e.g., "tomato"). Can be empty string. |
| `lang`        | string | ❌ No    | Language: "ar" or "en" (default: "ar")          |
| `chat_history`| string | ❌ No    | JSON stringified array of previous messages      |

**Request Example:**
```jsx
const formData = new FormData();
formData.append("message", "What causes leaf spots?");
formData.append("crop_type", "tomato");  // Optional!
formData.append("lang", "en");
formData.append("chat_history", JSON.stringify([
  { role: "user", content: "Hello" },
  { role: "assistant", content: "How can I help?" }
]));

const response = await fetch(`${API_URL}/api/chat`, {
  method: "POST",
  body: formData
});
```

**Response:**
```json
{
  "reply": "## Leaf Spots in Tomatoes\n\nLeaf spots are commonly caused by...",
  "crop_type": "tomato"
}
```

**Key Rules:**
- ✅ `crop_type` is **OPTIONAL** (can send empty string or omit)
- ✅ `chat_history` enables context-aware conversations
- ✅ Response is in **Markdown format**

---

### 3. Image Analysis Endpoint

**Endpoint:** `POST /api/analyze`

**Purpose:** Upload plant disease images for diagnosis

**Parameters (FormData):**

| Parameter   | Type   | Required | Description                                 |
|-------------|--------|----------|---------------------------------------------|
| `image`     | File   | ✅ Yes   | Image file (JPEG, PNG)                      |
| `crop_type` | string | ✅ Yes   | Crop slug - **STRICTLY REQUIRED**           |
| `lang`      | string | ❌ No    | Language: "ar" or "en"                     |
| `message`   | string | ❌ No    | Optional text description with the image    |

**Request Example:**
```jsx
const formData = new FormData();
formData.append("image", imageFile);
formData.append("crop_type", "tomato");  // REQUIRED!
formData.append("lang", "en");
formData.append("message", "Found these spots on my leaves");

const response = await fetch(`${API_URL}/api/analyze`, {
  method: "POST",
  body: formData
});
```

**Response:**
```json
{
  "reply": "## Diagnosis: Early Blight\n\n**Symptoms:** Dark spots...",
  "details": {
    "symptom_scores": { "leaf_spots": 0.95, "yellowing": 0.8 },
    "web_evidence": ["..."],
    "classification": "early_blight",
    "confidence": 0.92
  }
}
```

**Key Rules:**
- ❌ `crop_type` is **MANDATORY** - Server will return 422 if missing
- ✅ `message` can provide context (e.g., "leaves turning yellow")
- ✅ Response includes detailed diagnosis in `details` object

---

## 🚨 Critical Integration Rules

### Rule #1: ALWAYS Use FormData (Never JSON)

**❌ WRONG - Will Fail:**
```jsx
fetch(`${API_URL}/api/chat`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message: "Hello", crop_type: "tomato" })
});
```

**✅ CORRECT:**
```jsx
const formData = new FormData();
formData.append("message", "Hello");
formData.append("crop_type", "tomato");

fetch(`${API_URL}/api/chat`, {
  method: "POST",
  body: formData  // No headers needed!
});
```

**Why?** The API expects `multipart/form-data` for file uploads and consistency.

---

### Rule #2: Crop Type Logic

| Endpoint       | Crop Required? | What Happens if Missing?                    |
|----------------|----------------|---------------------------------------------|
| `/api/chat`    | ❌ No          | Works fine - general plant advice           |
| `/api/analyze` | ✅ Yes         | Returns 422 Unprocessable Entity Error      |

**Implementation:**
```jsx
// For chat - can be empty
formData.append("crop_type", selectedCrop || "");

// For image upload - MUST validate first
if (!selectedCrop) {
  alert("Please select a crop type before uploading!");
  return;
}
formData.append("crop_type", selectedCrop);
```

---

### Rule #3: Chat History Format

**Send chat history as JSON string:**

```jsx
const chatHistory = messages.map(msg => ({
  role: msg.role === "user" ? "user" : "assistant",
  content: msg.text
}));

formData.append("chat_history", JSON.stringify(chatHistory));
```

**Why?** Enables context-aware responses. The AI remembers previous conversation.

---

### Rule #4: Markdown Rendering

All API responses are in **Markdown format**. You MUST use `react-markdown`:

```jsx
import ReactMarkdown from 'react-markdown';

// In your component
<ReactMarkdown>{botResponse}</ReactMarkdown>
```

---

## 💎 Complete React Component (Production Ready)

```jsx
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

function PlantDiseaseChat() {
  // Environment-based API URL
  const API_URL = import.meta.env.VITE_API_URL || process.env.REACT_APP_API_URL;

  // State management
  const [crops, setCrops] = useState([]);
  const [selectedCrop, setSelectedCrop] = useState("");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load available crops on mount
  useEffect(() => {
    if (!API_URL) {
      setError("API_URL not configured. Check your .env file!");
      return;
    }

    fetch(`${API_URL}/api/crops`)
      .then(res => {
        if (!res.ok) throw new Error(`Failed to load crops: ${res.status}`);
        return res.json();
      })
      .then(data => setCrops(data.crops))
      .catch(err => {
        console.error("Error loading crops:", err);
        setError("Failed to connect to backend. Is it running?");
      });
  }, [API_URL]);

  // Send text message with chat history
  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setInput("");
    setError(null);

    // Add user message to UI
    const newMessages = [...messages, { role: "user", text: userMessage }];
    setMessages(newMessages);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("message", userMessage);
      formData.append("crop_type", selectedCrop || "");
      formData.append("lang", "ar");

      // Build chat history for context
      const chatHistory = messages.map(msg => ({
        role: msg.role === "user" ? "user" : "assistant",
        content: msg.text
      }));
      formData.append("chat_history", JSON.stringify(chatHistory));

      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${res.status}`);
      }

      const data = await res.json();
      setMessages(prev => [...prev, { role: "bot", text: data.reply }]);
    } catch (error) {
      console.error("Error sending message:", error);
      setError(error.message || "Failed to send message");
      setMessages(prev => [...prev, {
        role: "bot",
        text: "⚠️ Sorry, something went wrong. Please try again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Handle image upload with optional text message
  const handleImage = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setError(null);

    // Validate crop selection (REQUIRED for images)
    if (!selectedCrop) {
      setError("⚠️ Please select a crop type before uploading an image!");
      e.target.value = ""; // Reset file input
      return;
    }

    // Show user action in chat
    const imageMessage = input.trim() 
      ? `[Image uploaded: ${input}]` 
      : "[Image uploaded]";
    setMessages(prev => [...prev, { role: "user", text: imageMessage }]);
    
    setLoading(true);
    const uploadText = input; // Capture before clearing
    setInput(""); // Clear input field

    try {
      const formData = new FormData();
      formData.append("image", file);
      formData.append("crop_type", selectedCrop);
      formData.append("lang", "ar");
      
      // Include text description if user typed something
      if (uploadText.trim()) {
        formData.append("message", uploadText);
      }

      const res = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${res.status}`);
      }

      const data = await res.json();
      setMessages(prev => [...prev, { role: "bot", text: data.reply }]);
    } catch (error) {
      console.error("Error analyzing image:", error);
      setError(error.message || "Failed to analyze image");
      setMessages(prev => [...prev, {
        role: "bot",
        text: "⚠️ Sorry, failed to analyze the image. Please try again."
      }]);
    } finally {
      setLoading(false);
      e.target.value = ""; // Reset file input
    }
  };

  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{
      maxWidth: 700,
      margin: "20px auto",
      padding: 20,
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    }}>
      <h1 style={{ textAlign: "center", color: "#2d5016" }}>
        🌿 Plant Disease Assistant
      </h1>

      {/* Error Banner */}
      {error && (
        <div style={{
          backgroundColor: "#fee",
          border: "1px solid #fcc",
          borderRadius: 5,
          padding: 12,
          marginBottom: 15,
          color: "#c33"
        }}>
          {error}
        </div>
      )}

      {/* Crop Selector */}
      <div style={{ marginBottom: 20 }}>
        <label style={{
          display: "block",
          marginBottom: 6,
          fontWeight: "600",
          color: "#333"
        }}>
          Select Crop Type:
        </label>
        <select
          value={selectedCrop}
          onChange={e => setSelectedCrop(e.target.value)}
          style={{
            width: "100%",
            padding: 12,
            borderRadius: 8,
            border: "2px solid #ddd",
            fontSize: 15,
            backgroundColor: "#fff",
            cursor: "pointer"
          }}
        >
          <option value="">-- Optional for Chat, Required for Images --</option>
          {crops.map(c => (
            <option key={c.slug} value={c.slug}>
              {c.name_en} ({c.name_ar})
            </option>
          ))}
        </select>
      </div>

      {/* Chat Messages */}
      <div style={{
        height: 450,
        overflowY: "auto",
        border: "2px solid #e0e0e0",
        borderRadius: 12,
        padding: 20,
        marginBottom: 15,
        backgroundColor: "#fafafa"
      }}>
        {messages.length === 0 && (
          <div style={{
            textAlign: "center",
            color: "#999",
            marginTop: 150,
            fontSize: 16
          }}>
            <p>👋 Welcome! Ask me about plant diseases.</p>
            <p>You can chat or upload an image for diagnosis.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              marginBottom: 20,
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start"
            }}
          >
            <div
              style={{
                display: "inline-block",
                maxWidth: "75%",
                padding: 12,
                borderRadius: 12,
                backgroundColor: msg.role === "user" ? "#4caf50" : "#fff",
                color: msg.role === "user" ? "#fff" : "#333",
                boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
                fontSize: 15,
                lineHeight: 1.5
              }}
            >
              <ReactMarkdown>{msg.text}</ReactMarkdown>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ textAlign: "center", color: "#666", marginTop: 10 }}>
            <em>⏳ Processing...</em>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your question or describe the problem..."
          disabled={loading}
          style={{
            flex: 1,
            padding: 12,
            borderRadius: 8,
            border: "2px solid #ddd",
            fontSize: 15,
            outline: "none"
          }}
        />

        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          style={{
            padding: "12px 24px",
            backgroundColor: loading || !input.trim() ? "#ccc" : "#4caf50",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            fontSize: 15,
            fontWeight: "600",
            cursor: loading || !input.trim() ? "not-allowed" : "pointer",
            transition: "background 0.2s"
          }}
        >
          💬 Send
        </button>

        <label
          style={{
            padding: "12px 24px",
            backgroundColor: loading ? "#ccc" : "#2196f3",
            color: "#fff",
            borderRadius: 8,
            fontSize: 15,
            fontWeight: "600",
            cursor: loading ? "not-allowed" : "pointer",
            display: "flex",
            alignItems: "center",
            gap: 5
          }}
        >
          📸 Image
          <input
            type="file"
            accept="image/*"
            onChange={handleImage}
            disabled={loading}
            style={{ display: "none" }}
          />
        </label>
      </div>

      {/* Hint */}
      <p style={{
        textAlign: "center",
        fontSize: 13,
        color: "#999",
        marginTop: 12
      }}>
        💡 Tip: Select a crop and type a description before uploading an image for better results
      </p>
    </div>
  );
}

export default PlantDiseaseChat;
```

---

## ⚠️ Common Pitfalls & Troubleshooting

### Issue #1: API Not Responding

**Symptoms:**
- Fetch fails with network error
- `Failed to connect to backend`

**Solution:**
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# If not running, start it:
cd /Users/apple/Desktop/final_plant
source venv/bin/activate
uvicorn api:app --reload --port 8000
```

---

### Issue #2: 503 Service Unavailable

**Symptoms:**
```json
{
  "detail": "ChromaDB is not ready. Please ensure the database is built."
}
```

**Solution:**
The vector database needs to be initialized:
```bash
cd /Users/apple/Desktop/final_plant
python infrastructure/create_db.py
```

---

### Issue #3: 422 Unprocessable Entity (Image Upload)

**Symptoms:**
```json
{
  "detail": "crop_type is required for image analysis"
}
```

**Solution:**
Always validate `crop_type` is selected before allowing image upload:
```jsx
if (!selectedCrop) {
  alert("Please select a crop type!");
  return;
}
```

---

### Issue #4: CORS Errors

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/api/chat' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Solution:**
CORS is already enabled in the backend. If you see this:
1. Check you're using `FormData` (not JSON with headers)
2. Verify backend is actually running
3. Try clearing browser cache

---

### Issue #5: Environment Variable Not Loaded

**Symptoms:**
- `API_URL` is `undefined`
- Console error: "API_URL not configured"

**Solution:**

**For Vite:**
```env
# .env file - MUST start with VITE_
VITE_API_URL=http://localhost:8000
```
```bash
# Restart dev server
npm run dev
```

**For Create React App:**
```env
# .env file - MUST start with REACT_APP_
REACT_APP_API_URL=http://localhost:8000
```
```bash
# Restart dev server  
npm start
```

---

### Issue #6: Markdown Not Rendering

**Symptoms:**
- Bot responses show raw Markdown (e.g., `## Heading`)

**Solution:**
```bash
# Install react-markdown
npm install react-markdown
```
```jsx
// Use in component
import ReactMarkdown from 'react-markdown';
<ReactMarkdown>{botResponse}</ReactMarkdown>
```

---

## ✅ Testing Checklist

Before deploying, verify:

### Backend Tests
- [ ] Backend starts without errors: `uvicorn api:app --reload`
- [ ] Health check works: `curl http://localhost:8000/api/health`
- [ ] Interactive docs accessible: `http://localhost:8000/docs`
- [ ] ChromaDB initialized (if not, run `python infrastructure/create_db.py`)

### Frontend Tests
- [ ] `.env` file created with correct API URL
- [ ] `react-markdown` installed
- [ ] Crops load on component mount
- [ ] Can send text message without crop selected
- [ ] Can send text message with crop selected
- [ ] Cannot upload image without crop (shows error)
- [ ] Can upload image with crop selected
- [ ] Chat history maintains context across messages
- [ ] Text description + image upload works together
- [ ] Loading states display correctly
- [ ] Error messages show for failed requests
- [ ] Markdown renders properly in bot responses

### Integration Tests
- [ ] Test with different image types (JPEG, PNG)
- [ ] Test with different crops (tomato, potato, rice, wheat, apple)
- [ ] Test long conversations (5+ messages)
- [ ] Test rapid-fire messages
- [ ] Test network errors (stop backend mid-conversation)
- [ ] Test large images (>5MB)

---

## 📚 Additional Resources

- **Detailed API Documentation:** [API_README.md](API_README.md)
- **Interactive API Docs:** `http://localhost:8000/docs` (when server running)
- **Backend Source:** Check `api.py` for endpoint implementations
- **React Markdown Docs:** [https://github.com/remarkjs/react-markdown](https://github.com/remarkjs/react-markdown)

---

## 🎯 Quick Start Summary

```bash
# 1. Start Backend
cd /Users/apple/Desktop/final_plant
source venv/bin/activate
uvicorn api:app --reload --port 8000

# 2. Setup Frontend
cd your-react-project
npm install react-markdown

# 3. Create .env
echo "VITE_API_URL=http://localhost:8000" > .env

# 4. Copy component code from this guide

# 5. Start development
npm run dev
```

---

## 📞 Support

If you encounter issues not covered in this guide:

1. Check FastAPI logs in terminal where `uvicorn` is running
2. Check browser console for error messages
3. Verify all dependencies are installed
4. Ensure Python environment is activated
5. Confirm `.env` file is in correct directory

**Backend Health Check:**
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{"status":"ok","db_ready":true}
```
