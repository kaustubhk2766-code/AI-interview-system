from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time

app = Flask(__name__)
CORS(app)

# ---- Simple rate limiter (per endpoint, global) ----
_last_call_time = {}
RATE_LIMIT_SECONDS = 5  # min seconds between calls per endpoint

def is_rate_limited(endpoint):
    now = time.time()
    last = _last_call_time.get(endpoint, 0)
    if now - last < RATE_LIMIT_SECONDS:
        wait = round(RATE_LIMIT_SECONDS - (now - last), 1)
        return True, wait
    _last_call_time[endpoint] = now
    return False, 0

# 🔐 Gemini API Key loaded from environment for security
API_KEY = os.getenv("GEMINI_API_KEY")

# -------------------------------
# 🔹 Common Gemini Call Function
# -------------------------------
# Models available with this API key (verified via ListModels)
PRIMARY_MODEL = "gemini-2.0-flash"
FALLBACK_MODEL = "gemini-2.0-flash-lite"  # lighter quota limits

def call_gemini(prompt, model=PRIMARY_MODEL):
    if not API_KEY:
        return None, "Gemini API key is not set. Please set GEMINI_API_KEY in your environment."

    # ✅ Correct endpoint: v1beta + generateContent + API key as query param
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={API_KEY}"
    headers = {
        "Content-Type": "application/json"
    }
    # ✅ Correct payload format for Gemini generateContent
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 512
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 429:
            # Try fallback model before giving up
            if model == PRIMARY_MODEL:
                return call_gemini(prompt, model=FALLBACK_MODEL)
            return None, "⏱️ API quota exceeded. Please wait a moment and try again."
        elif response.status_code != 200:
            return None, f"API Error {response.status_code}: {response.text}"

        data = response.json()
        # ✅ Correct response parsing for generateContent
        candidates = data.get("candidates") or []
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if parts:
                return parts[0].get("text", ""), None

        return None, "No response from Gemini"

    except Exception as e:
        return None, str(e)


# -------------------------------
# 🔹 Home Route
# -------------------------------
@app.route("/")
def home():
    return "Backend is running with Gemini ✅"


# -------------------------------
# 🔹 Generate Question
# -------------------------------
@app.route("/generate-question", methods=["POST"])
def generate_question():
    limited, wait = is_rate_limited("generate-question")
    if limited:
        return jsonify({"error": f"⏱️ Please wait {wait}s before generating another question."}), 429
    try:
        data = request.json
        role = data.get("role", "")
        experience = data.get("experience", "")

        prompt = f"Generate ONE technical interview question for a {role} with {experience} years of experience."

        question, error = call_gemini(prompt)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"question": question})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# 🔹 Evaluate Answer
# -------------------------------
@app.route("/evaluate", methods=["POST"])
def evaluate():
    limited, wait = is_rate_limited("evaluate")
    if limited:
        return jsonify({"error": f"⏱️ Please wait {wait}s before evaluating again."}), 429
    try:
        data = request.json
        question = data.get("question", "")
        answer = data.get("answer", "")

        prompt = f"""
Question: {question}
Answer: {answer}

Provide:
1. Score out of 10
2. Strengths
3. Weaknesses
4. Improvements
5. Learning resources
"""

        feedback, error = call_gemini(prompt)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"feedback": feedback})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
if __name__ == "__main__":
    app.run(
        debug=bool(os.getenv("FLASK_DEBUG", "1") == "1"),
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000))
    )