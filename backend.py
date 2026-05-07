from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import hashlib
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ========================
# 🔹 SambaNova Config
# ========================

SAMBANOVA_API_KEY = os.getenv("SAMBANOVA_API_KEY")

if not SAMBANOVA_API_KEY:
    raise ValueError("❌ SAMBANOVA_API_KEY not found")

REQUEST_TIMEOUT = 30

# SambaNova OpenAI-compatible endpoint
API_URL = "https://api.sambanova.ai/v1/chat/completions"

# Working model
MODEL = "Meta-Llama-3.1-8B-Instruct"

# ========================
# 🔹 In-Memory Cache
# ========================

_cache = {}

def cache_key(*args):
    raw = json.dumps(args, sort_keys=True)
    return hashlib.md5(raw.encode()).hexdigest()

def get_cached(key):
    return _cache.get(key)

def set_cached(key, value):
    if len(_cache) >= 200:
        oldest = next(iter(_cache))
        del _cache[oldest]

    _cache[key] = value

# ========================
# 🔹 SambaNova Function
# ========================

def call_sambanova(prompt, max_tokens=600):

    headers = {
        "Authorization": f"Bearer {SAMBANOVA_API_KEY}",
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
        "max_tokens": max_tokens
    }

    try:

        response = requests.post(
            API_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        print("🔍 STATUS:", response.status_code)
        print("🔍 RESPONSE:", response.text[:300])

        if response.status_code == 401:
            return None, "❌ Invalid SambaNova API Key"

        elif response.status_code == 429:
            return None, "⏱️ Rate limit exceeded"

        elif response.status_code != 200:
            return None, f"API Error {response.status_code}: {response.text}"

        result = response.json()

        if "choices" not in result:
            return None, "❌ Invalid API response"

        text = result["choices"][0]["message"]["content"]

        return text, None

    except Exception as e:
        return None, str(e)

# ========================
# 🔹 Routes
# ========================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "✅ Backend running",
        "provider": "SambaNova",
        "model": MODEL,
        "cache_size": len(_cache)
    })

# ========================
# 🔹 Generate Question
# ========================

@app.route("/generate-question", methods=["POST"])
def generate_question():

    try:

        data = request.json

        role = data.get("role", "").strip()
        experience = data.get("experience", "").strip()

        if not role or not experience:
            return jsonify({
                "error": "Missing role or experience"
            }), 400

        key = cache_key("question", role, experience)

        cached = get_cached(key)

        if cached:
            print("✅ Cache hit: question")

            return jsonify({
                "question": cached,
                "cached": True
            })

        prompt = f"""
Generate ONE concise technical interview question
for a {role} with {experience} years of experience.

Return only the question.
"""

        question, error = call_sambanova(
            prompt,
            max_tokens=200
        )

        if error:
            return jsonify({
                "error": error
            }), 500

        set_cached(key, question)

        return jsonify({
            "question": question,
            "cached": False
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# ========================
# 🔹 Evaluate Answer
# ========================

@app.route("/evaluate", methods=["POST"])
def evaluate():

    try:

        data = request.json

        question = data.get("question", "").strip()
        answer = data.get("answer", "").strip()

        if not question or not answer:
            return jsonify({
                "error": "Missing question or answer"
            }), 400

        key = cache_key("eval", question, answer)

        cached = get_cached(key)

        if cached:
            print("✅ Cache hit: evaluation")

            return jsonify({
                "feedback": cached,
                "cached": True
            })

        prompt = f"""
Question:
{question}

Answer:
{answer}

Evaluate concisely:

1. Score out of 10
2. Strengths
3. Weaknesses
4. Improvements
5. Learning resource

Keep it brief and direct.
"""

        feedback, error = call_sambanova(
            prompt,
            max_tokens=600
        )

        if error:
            return jsonify({
                "error": error
            }), 500

        set_cached(key, feedback)

        return jsonify({
            "feedback": feedback,
            "cached": False
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# ========================
# 🔹 Cache Stats
# ========================

@app.route("/cache-stats", methods=["GET"])
def cache_stats():

    return jsonify({
        "cached_entries": len(_cache),
        "max_entries": 200
    })

# ========================
# 🔹 Error Handlers
# ========================

@app.errorhandler(404)
def not_found(e):

    return jsonify({
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def server_error(e):

    return jsonify({
        "error": "Internal server error"
    }), 500

# ========================
# 🔹 Run Server
# ========================

if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=5000
    )