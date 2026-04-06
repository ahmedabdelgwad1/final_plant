# Frontend Integration Prompt / دمج الشات بوت مع الـ API

*Copy the text below and paste it to the AI in your frontend project's workspace:*

---

## 🎯 Goal / الهدف
I want you to analyze this frontend repository to find the Components and files responsible for the **Chatbot UI**. 
Once found, please integrate my backend API into the existing Chatbot **WITHOUT making any changes to the UI/CSS or the general design**. Only replace the mock data / existing API functions with my new endpoints.

أريدك أن تبحث في ملفات هذا المشروع عن المكونات (Components) المسؤولة عن الشات بوت. وبعد إيجادها، قم بربط واجهة الشات بوت بالـ API الخاص بي المذكور بالأسفل، **بدون تغيير أي شيء في التصميم أو الستايل (UI/CSS)**. قم فقط بتحديث دوال الاتصال بالخلفية (Network Calls).

## ⚠️ Strict Rules / قواعد هامة:
1. **DO NOT change the styling or UI structure.** Keep the design exactly as it is.
2. Only update the logic (State management, fetch/axios calls, form submission).
3. All POST requests must be sent as `FormData` (multipart/form-data), NOT JSON, because the API expects images.
4. Ensure `chat_history` is passed as a stringified JSON array in the POST requests.

## 🔗 Backend API Details / تفاصيل الروابط
**Base URL:** `https://Ahmed3182004-final-plant.hf.space`

### 1. Fetch Crops List (GET)
- **Endpoint:** `GET /api/crops`
- **Purpose:** Fetch the list of crops to populate the Crop Selection Dropdown.
- **Expected Response:** An array or object containing crop names.

### 2. Send Text Message (POST)
- **Endpoint:** `POST /api/chat`
- **Purpose:** Send a purely text-based question.
- **Required `FormData` Fields:**
  - `message`: (string) The user's text message.
  - `crop_type`: (string) The selected crop from the dropdown.
  - `lang`: (string) `"en"` or `"ar"`.
  - `chat_history`: (string) JSON stringified array of previous messages. Example: `"[{\"role\": \"user\", \"content\": \"hi\"}]"`
- **Expected Response:** Returns an object containing the AI's answer in a `reply` field.

### 3. Analyze Image (POST)
- **Endpoint:** `POST /api/analyze`
- **Purpose:** Upload a plant image for disease analysis, accompanied by an optional text message.
- **Required `FormData` Fields:**
  - `image`: (File) The image file from the input.
  - `crop_type`: (string) The selected crop.
  - `message`: (string) Optional text message to go with the image.
  - `lang`: (string) `"en"` or `"ar"`.
  - `chat_history`: (string) JSON stringified array of previous messages.

## 🛠️ Required Steps for the AI:
1. Locate the Chat Component (Messages list, Input field, File input, Crop dropdown).
2. Wire the crop dropdown to call `GET /api/crops` on component mount.
3. Wire the "Send" button to use `POST /api/analyze` if an image is attached, and `POST /api/chat` if only text is provided.
4. Append the returned `reply` from the backend to the UI chat history.
