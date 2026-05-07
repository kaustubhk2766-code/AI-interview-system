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

# 🔐 OpenRouter API Key loaded from environment for security
API_KEY = os.getenv("OPENROUTER_API_KEY")

# -------------------------------
# 🔹 Common OpenRouter Call Function
# -------------------------------
# Using a cost-effective model from OpenRouter
PRIMARY_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
FALLBACK_MODEL = "google/gemma-2-9b-it:free"

def call_openrouter(prompt, model=PRIMARY_MODEL):
    if not API_KEY:
        return None, "OpenRouter API key is not set. Please set OPENROUTER_API_KEY in your environment."

    # OpenRouter API endpoint
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/kaustubhk2766-code/AI-interview-system",
        "X-Title": "AI Interview System"
    }
    # OpenRouter uses OpenAI-compatible chat completions format
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 429:
            # Try fallback model before giving up
            if model == PRIMARY_MODEL:
                return call_openrouter(prompt, model=FALLBACK_MODEL)
            return None, "⏱️ API quota exceeded. Please wait a moment and try again."
        elif response.status_code == 401:
            return None, "❌ Invalid OpenRouter API Key. Check your OPENROUTER_API_KEY"
        elif response.status_code != 200:
            return None, f"API Error {response.status_code}: {response.text}"

        data = response.json()
        # Parse OpenRouter response (OpenAI-compatible format)
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content", "")
            if content:
                return content, None

        return None, "No response from OpenRouter"

    except Exception as e:
        return None, str(e)


# -------------------------------
# 🔹 Home Route
# -------------------------------
@app.route("/")
def home():
    return "Backend is running with OpenRouter ✅"


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

        question, error = call_openrouter(prompt)

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

        feedback, error = call_openrouter(prompt)

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