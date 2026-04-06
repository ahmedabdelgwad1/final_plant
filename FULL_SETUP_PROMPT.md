# Full Project Setup & Integration Prompt / التشغيل والربط الكامل للمشروع

*انسخ هذا النص وضعه للـ AI في مشروع الـ Frontend الذي قمت بعمله Clone ليقوم بتحديثه وتشغيله بالكامل:*

---

## 🚀 Mission: Full Setup, Run, and API Integration
You are an expert Frontend Developer. I have just cloned this repository. I need you to completely set up, run, and integrate my backend API into this project. Please execute the following phases step-by-step:

أنت مطور واجهات أمامية محترف. لقد قمت بعمل Clone لهذا المشروع للتو. أريدك أن تقوم بإعداد المشروع بالكامل، تشغيله، وربط واجهة الشات بوت بالـ API الخاص بي. يرجى تنفيذ الخطوات التالية بالترتيب:

### Phase 1: Environment Setup & Running
1. Identify the package manager used (npm, yarn, pnpm) from the lockfile or `package.json`.
2. Install all necessary dependencies.
3. Fix any legacy peer dependencies conflicts if they appear.
4. Run the development server (e.g., `npm run dev` or `npm start`).
5. If there are any initial compile errors or missing basic libraries, fix them immediately.

### Phase 2: Chatbot API Integration (No UI Changes!)
Once the project is running, locate the component(s) responsible for the **Chatbot UI** (chat history, input field, image upload, crop selection dropdown) and connect them to my backend API.

**⚠️ STRICT RULE:** DO NOT change ANY styles, tailwind classes, CSS, or the general layout. Keep the UI exactly as the original author designed it. Only change the fetch/axios logic and state management.

#### 🔗 Backend API Details (Base URL: `https://Ahmed3182004-final-plant.hf.space`)

**1. GET `/api/crops`**
- Call this on component mount to get the list of available crops.
- Populate the crop selection dropdown with this data.

**2. POST `/api/chat` (Text Only)**
- Triggered when the user sends a text message without an image.
- Must be sent as `FormData`.
- Fields: `message` (string), `crop_type` (string selected), `lang` (send `"en"` or `"ar"` as appropriate), `chat_history` (stringified JSON array of the chat context).
- Wait for the response and append the `reply` to the chat window.

**3. POST `/api/analyze` (Image + Optional Text)**
- Triggered when the user uploads an image (with or بدون message).
- Must be sent as `FormData`.
- Fields: `image` (File object), `crop_type` (string), `message` (string), `lang` (string), `chat_history` (stringified JSON).

### Phase 3: Testing & Debugging
- Ensure all POST requests correctly use `multipart/form-data`.
- Ensure `chat_history` is serialized properly before appending to `FormData`.
- Add a loading state (e.g., "Typing..." or a spinner) while waiting for the API response, using the existing UI components.
- Fix any browser console errors or CORS issues (if bypass proxies are needed, implement them locally in vite/webpack config).

**Now, please analyze the workspace, tell me what you found, and start executing these phases!**
