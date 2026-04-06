// Comprehensive React code file to connect to the API without needing a .env file
// You can send this file to the React developer to understand the integration immediately

import React, { useState, useEffect } from "react";

// 1. Define the base server URL (Hardcoded)
const API_BASE = "https://Ahmed3182004-final-plant.hf.space";

// ==========================================
// 2. API Functions
// ==========================================

export async function checkServerHealth() {
    const response = await fetch(`${API_BASE}/api/health`);
    if (!response.ok) throw new Error("Server is not responding");
    return response.json();
}

export async function fetchCrops() {
    const response = await fetch(`${API_BASE}/api/crops`);
    if (!response.ok) throw new Error("Failed to fetch crops");
    return response.json();
}

export async function sendTextMessage(message, cropType, chatHistory) {
    const formData = new FormData();
    formData.append("message", message);
    formData.append("crop_type", cropType);
    formData.append("lang", "en"); // or "ar"
    formData.append("chat_history", JSON.stringify(chatHistory));

    const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) throw new Error("Chat request failed");
    return response.json();
}

export async function uploadAndAnalyzeImage(imageFile, cropType, message, chatHistory) {
    const formData = new FormData();
    formData.append("image", imageFile);
    formData.append("crop_type", cropType);
    formData.append("message", message || "");
    formData.append("lang", "en"); // or "ar"
    formData.append("chat_history", JSON.stringify(chatHistory));

    const response = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        body: formData,
    });

    if (!response.ok) throw new Error("Image analysis failed");
    return response.json();
}


// ==========================================
// 3. Example React Component using these functions
// ==========================================

export default function PlantChatApp() {
    const [crops, setCrops] = useState([]);
    const [selectedCrop, setSelectedCrop] = useState("");
    const [message, setMessage] = useState("");
    const [imageFile, setImageFile] = useState(null);
    const [chatHistory, setChatHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    // Fetch crops when the component mounts
    useEffect(() => {
        fetchCrops()
            .then(data => setCrops(data.crops || data))
            .catch(err => console.error(err));
    }, []);

    const handleSend = async () => {
        if (!message && !imageFile) return;

        // Add user message to chat history
        const newHistory = [...chatHistory, { role: "user", content: message || "[Image]" }];
        setChatHistory(newHistory);
        setIsLoading(true);

        try {
            let data;
            // If there's an image, call the analyze endpoint
            if (imageFile) {
                if (!selectedCrop) {
                    alert("Please select the crop type before uploading the image!");
                    setIsLoading(false);
                    return;
                }
                data = await uploadAndAnalyzeImage(imageFile, selectedCrop, message, newHistory);
            }
            // If there's no image, call the regular chat endpoint
            else {
                data = await sendTextMessage(message, selectedCrop, newHistory);
            }

            // Add model's reply to chat history
            setChatHistory(prev => [...prev, { role: "assistant", content: data.reply }]);
        } catch (error) {
            alert("An error occurred while sending data");
            console.error(error);
        } finally {
            setIsLoading(false);
            setMessage("");
            setImageFile(null);
        }
    };

    return (
        <div style={{ padding: "20px", maxWidth: "600px", margin: "auto", fontFamily: "sans-serif" }}>
            <h2>Plant Disease Diagnosis App 🌿</h2>

            {/* 1. Crop Selection */}
            <select
                value={selectedCrop}
                onChange={e => setSelectedCrop(e.target.value)}
                style={{ width: "100%", padding: "10px", marginBottom: "15px" }}
            >
                <option value="">-- Select Crop Type --</option>
                {crops.map(c => <option key={c} value={c}>{c}</option>)}
            </select>

            {/* 2. Chat History */}
            <div style={{ border: "1px solid #ccc", padding: "10px", height: "300px", overflowY: "auto", marginBottom: "15px" }}>
                {chatHistory.map((msg, idx) => (
                    <div key={idx} style={{
                        textAlign: msg.role === "user" ? "right" : "left",
                        backgroundColor: msg.role === "user" ? "#dcf8c6" : "#f1f0f0",
                        padding: "8px",
                        margin: "5px 0",
                        borderRadius: "5px"
                    }}>
                        <strong>{msg.role === "user" ? "You: " : "AI: "}</strong>
                        {msg.content}
                    </div>
                ))}
            </div>

            {/* 3. Input */}
            <input
                type="text"
                value={message}
                onChange={e => setMessage(e.target.value)}
                placeholder="Type your question here..."
                style={{ width: "100%", padding: "10px", marginBottom: "10px" }}
            />

            <input
                type="file"
                accept="image/*"
                onChange={e => setImageFile(e.target.files[0])}
                style={{ marginBottom: "10px" }}
            />

            <button
                onClick={handleSend}
                disabled={isLoading}
                style={{ display: "block", width: "100%", padding: "10px", background: "#4CAF50", color: "white", border: "none" }}
            >
                {isLoading ? "Sending..." : "Send"}
            </button>
        </div>
    );
}
