from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# -------------------------------
# 🔹 Simple Rate Limiter
# -------------------------------
_last_call_time = {}
RATE_LIMIT_SECONDS = 5


def is_rate_limited(endpoint):
    now = time.time()
    last = _last_call_time.get(endpoint, 0)

    if now - last < RATE_LIMIT_SECONDS:
        wait = round(RATE_LIMIT_SECONDS - (now - last), 1)
        return True, wait

    _last_call_time[endpoint] = now
    return False, 0


# -------------------------------
# 🔹 DeepSeek API Config
# -------------------------------
API_KEY = os.getenv("DEEPSEEK_API_KEY")

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

MODEL = "deepseek-chat"


# -------------------------------
# 🔹 Common DeepSeek Call Function
# -------------------------------
def call_deepseek(prompt):

    if not API_KEY:
        return None, "❌ DEEPSEEK_API_KEY not found."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }

    try:
        response = requests.post(
            DEEPSEEK_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        print("🔍 Status:", response.status_code)
        print("🔍 Response:", response.text[:300])

        if response.status_code == 401:
            return None, "❌ Invalid DeepSeek API Key"

        if response.status_code != 200:
            return None, f"API Error {response.status_code}: {response.text}"

        data = response.json()

        if "choices" not in data:
            return None, "❌ Invalid response from DeepSeek"

        content = data["choices"][0]["message"]["content"]

        return content, None

    except requests.exceptions.Timeout:
        return None, "⏱️ Request timeout"

    except requests.exceptions.ConnectionError:
        return None, "🌐 Connection error"

    except Exception as e:
        return None, str(e)


# -------------------------------
# 🔹 Home Route
# -------------------------------
@app.route("/")
def home():
    return jsonify({
        "status": "✅ Backend running",
        "provider": "DeepSeek API",
        "model": MODEL
    })


# -------------------------------
# 🔹 Generate Question
# -------------------------------
@app.route("/generate-question", methods=["POST"])
def generate_question():

    limited, wait = is_rate_limited("generate-question")

    if limited:
        return jsonify({
            "error": f"⏱️ Wait {wait}s before another request."
        }), 429

    try:
        data = request.json

        role = data.get("role", "").strip()
        experience = data.get("experience", "").strip()

        if not role or not experience:
            return jsonify({
                "error": "Missing role or experience"
            }), 400

        prompt = f"""
Generate ONE technical interview question
for a {role} with {experience} years experience.

Keep it concise and practical.
"""

        question, error = call_deepseek(prompt)

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
        return jsonify({
            "error": f"⏱️ Wait {wait}s before another evaluation."
        }), 429

    try:
        data = request.json

        question = data.get("question", "").strip()
        answer = data.get("answer", "").strip()

        if not question or not answer:
            return jsonify({
                "error": "Missing question or answer"
            }), 400

        prompt = f"""
Question:
{question}

Answer:
{answer}

Provide:

1. Score out of 10
2. Strengths
3. Weaknesses
4. Improvements
5. Learning resources

Keep response concise but detailed.
"""

        feedback, error = call_deepseek(prompt)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"feedback": feedback})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# 🔹 Error Handlers
# -------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# -------------------------------
# 🔹 Run App
# -------------------------------
if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000))
    )