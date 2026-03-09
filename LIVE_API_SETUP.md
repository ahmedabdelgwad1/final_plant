# 🚀 Live API Setup & Connection Guide

This guide is specifically for the **Frontend/React Developer** to connect their local or live React application to the fully deployed Hugging Face Backend API.

---

## 🌍 The Live Environment

The backend for the Plant Disease Diagnosis system is 100% cloud-hosted and running live. **You do NOT need to run any Python backend code locally to make the React app work.**

### 📌 The API URL
```env
VITE_API_URL=https://Ahmed3182004-final-plant.hf.space
```
*(If you are using Create React App instead of Vite, use `REACT_APP_API_URL=...`)*

---

## ⚙️ Server Specifications & Capacity

We have deployed the backend on a robust Docker environment on **Hugging Face Spaces** to handle AI model responses efficiently:

- **RAM Space:** 16 GB (Handles vector search and ChromaDB queries exceptionally fast)
- **Compute:** 2 vCPU
- **Storage:** Persisted SQLite + ChromaDB Vector Store
- **Concurrent Capacity:** The server can smoothly handle **20 to 30 concurrent users** making requests simultaneously without bottlenecking. (More than enough for presentations and testing!)

---

## 🛠️ How to Connect (Step-by-Step)

### Step 1: Update Your Frontend `.env` File
In the root directory of your React project, open the `.env` file (or create one if it doesn't exist).
Override the `localhost` URL with the production URL:

```env
# Before:
# VITE_API_URL=http://localhost:8000

# Now:
VITE_API_URL=https://Ahmed3182004-final-plant.hf.space
```

### Step 2: Restart Your Frontend Server
Whenever you change a `.env` file in React/Vite, you must restart the development server.
```bash
# Stop the terminal process (CTRL + C) and run:
npm run dev
```

### Step 3: Test the Connection
Once your React app is running, our endpoints are immediately available over the internet.
You can ping the health check endpoint directly in your browser or Postman to confirm it is alive:
👉 **[Check Live API Health](https://Ahmed3182004-final-plant.hf.space/api/health)**
*(Should return `{"status":"ok","db_ready":true}`)*

---

## 📡 Essential Endpoint Reminders

Since you are now talking to the remote server, all endpoints work exactly as they did locally:

1. **Get Crops:** `GET {VITE_API_URL}/api/crops`
2. **Text Chat:** `POST {VITE_API_URL}/api/chat` (Requires `message`, optional `crop_type`)
3. **Image Analysis:** `POST {VITE_API_URL}/api/analyze` (Requires `crop_type` and `image` file)

*For exact JSON request/response formats and React FormData examples, please refer to the main `INTEGRATION_GUIDE.md` file.*
