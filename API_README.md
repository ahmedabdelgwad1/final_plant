# 🌿 Plant Disease API — React Integration Guide

> هذا الملف مخصص لمطوّر الـ React لربط الفرونت إند مع الباك إند.

---

## 📌 Backend Info

| Item             | Value                          |
| ---------------- | ------------------------------ |
| **Framework**    | FastAPI 0.115.6                |
| **Python**       | 3.11.10                       |
| **Base URL**     | `http://localhost:8000`        |
| **Content-Type** | `multipart/form-data` (POST)  |

---

## 🚀 Running the Backend

```bash
# 1. تأكّد إن Python 3.11 مثبّت عندك
python3.11 --version

# 2. ثبّت المكتبات
pip install -r requirements.txt

# 3. أنشئ قاعدة البيانات (مرة واحدة بس)
python infrastructure/create_db.py

# 4. شغّل السيرفر
uvicorn api:app --reload --port 8000
```

السيرفر هيشتغل على `http://localhost:8000`

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

> استخدم الـ `slug` في `crop_type` عند إرسال صورة.

---

### 3. Chat (Main Endpoint)

```
POST /api/chat
Content-Type: multipart/form-data
```

**Form Fields:**

| Field          | Type   | Required | Default | Description                              |
| -------------- | ------ | -------- | ------- | ---------------------------------------- |
| `message`      | string | ❌       | `""`    | رسالة المستخدم النصية                    |
| `image`        | file   | ❌       | `null`  | صورة النبات (jpg, png, webp)             |
| `crop_type`    | string | ❌       | `""`    | نوع المحصول (slug) — مطلوب مع الصورة     |
| `lang`         | string | ❌       | `"ar"`  | لغة الرد: `"ar"` أو `"en"`              |
| `chat_history` | string | ❌       | `"[]"`  | JSON string لمصفوفة الرسائل السابقة      |

**Response (always):**

```json
{ "reply": "..." }
```

---

## 🔀 Three Scenarios

### Scenario 1: Text Only (Chat)

```js
const formData = new FormData();
formData.append("message", "ما هو أخطر مرض في الطماطم؟");
formData.append("lang", "ar");
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
formData.append("lang", "ar");
formData.append("message", ""); // optional text with image

const res = await fetch("http://localhost:8000/api/chat", {
  method: "POST",
  body: formData,
});
const data = await res.json();
console.log(data.reply);
// → 🌱 **المرض:** ...
// → 🔬 **السبب:** ...
// → 💊 **العلاج:** ...
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
// → "من فضلك اختر نوع النبات الأول."
```

> الـ API هيرد يطلب نوع المحصول — اعرض dropdown للمستخدم من `/api/crops`.

---

## 💬 Chat History Format

أرسل الـ `chat_history` كـ JSON string لمصفوفة من الرسائل:

```js
const chatHistory = [
  { role: "user", content: "ما هو مرض اللفحة المتأخرة؟" },
  { role: "assistant", content: "اللفحة المتأخرة هي ..." },
  { role: "user", content: "وإيه العلاج؟" },
];

formData.append("chat_history", JSON.stringify(chatHistory));
```

- `role`: `"user"` أو `"assistant"`
- `content`: نص الرسالة
- الباك إند بيستخدم آخر 6 رسائل بس عشان الـ context

---

## 🌐 CORS

الـ CORS مفتوح لكل الـ origins (`*`) — يعني تقدر تشغّل React على أي بورت:

```
http://localhost:3000  ✅
http://localhost:5173  ✅
http://127.0.0.1:3000  ✅
```

---

## ⚠️ Error Handling

| Status | Meaning                                       |
| ------ | --------------------------------------------- |
| `200`  | Success — الرد في `reply`                     |
| `400`  | لم يتم إرسال رسالة أو صورة                    |
| `503`  | قاعدة البيانات لم تُبنى بعد (شغّل create_db) |

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
2. User types message → POST /api/chat (text only)
3. User uploads image → show crop dropdown
4. User selects crop + sends → POST /api/chat (image + crop)
5. Display reply (supports Markdown — use react-markdown)
6. Keep chat_history array, send it with each request
```

---

## 📝 Notes

- الرد بيكون **Markdown** — استخدم `react-markdown` لعرضه.
- الصور المدعومة: **JPG, PNG, WebP**.
- `lang` ممكن `"ar"` (عربي) أو `"en"` (إنجليزي) — بيتحكم في لغة الرد بالكامل.
- لو الصورة فيها مشكلة، الرد هيحتوي على `⚠️` warning.
- ملف `.env` لازم يكون موجود في الباك إند ويحتوي على الأقل على `GROQ_API_KEY`.

---

## 🔑 Environment Variables (Backend)

| Variable            | Required | Description                  |
| ------------------- | -------- | ---------------------------- |
| `GROQ_API_KEY`      | ✅       | مفتاح Groq API              |
| `PLANTNET_API_KEY`  | ❌       | للتحقق من التشخيص (اختياري) |
| `TAVILY_API_KEY`    | ❌       | بحث ويب إضافي (اختياري)     |

> الـ Backend هو مسئوليتي — إنت مش محتاج تعدّل فيه. بس شغّله واستخدم الـ API.
