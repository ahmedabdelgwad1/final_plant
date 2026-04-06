# Run & Test Prompt / أمر التشغيل والاختبار

*انسخ هذا النص وضعه للـ AI **بعد** أن ينتهي من تعديل الأكواد والربط مع الـ API بنجاح:*

---

## 🚀 Mission: Run, Test, and Debug the Project
Great job on integrating the API. Now, I want you to run the project and ensure everything works perfectly. Please follow these steps:

عمل رائع في ربط الـ API. الآن، أريدك أن تقوم بتشغيل المشروع والتأكد من أن كل شيء يعمل بكفاءة. يرجى اتباع الخطوات التالية:

### 1. 📦 Environment Setup & Dependencies
- Check the `package.json` and lock files (package-lock.json / yarn.lock / pnpm-lock.yaml) to determine the correct package manager.
- Run the install command to download all dependencies. 
- If there are conflicts (like legacy peer dependencies), resolve them automatically.

### 2. 🏃‍♂️ Run the Development Server
- Start the local development server (e.g., `npm run dev`, `npm start`, or the equivalent).
- Tell me what local URL the server is running on (e.g., http://localhost:3000).

### 3. 🐛 Fix Compile Errors (If Any)
- If the terminal shows any build or compile errors after starting the server, fix them immediately without waiting for my prompt.
- Do NOT change any CSS/UI while fixing errors.

### 4. 🌐 Handle API / CORS Issues
- I will test the Chatbot now.
- If we face any CORS (Cross-Origin Resource Sharing) policy errors in the browser console when calling `https://Ahmed3182004-final-plant.hf.space`, please configure a local proxy in the frontend config file (like `vite.config.js`, `next.config.js`, or `webpack.config.js`) to bypass it.

**Please start by installing dependencies and running the server now!**
