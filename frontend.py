from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ========================
# 🔹 DeepSeek API Config
# ========================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

if not DEEPSEEK_API_KEY:
    raise ValueError("❌ DEEPSEEK_API_KEY not found in environment variables!")

REQUEST_TIMEOUT = 30

# DeepSeek model
MODEL = "deepseek-chat"


# ========================
# 🔹 DeepSeek API Function
# ========================

def call_deepseek(prompt):
    """Call DeepSeek API"""

    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
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
            url,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        print(f"🔍 Status: {response.status_code}")
        print(f"🔍 Response: {response.text[:200]}")

        # Handle API errors
        if response.status_code == 401:
            return None, "❌ Invalid DeepSeek API Key"

        elif response.status_code == 429:
            return None, "⏱️ Rate limit exceeded. Try again later."

        elif response.status_code == 500:
            return None, "🔴 DeepSeek server error."

        elif response.status_code != 200:
            return None, f"API Error: {response.status_code} - {response.text}"

        # Parse response
        result = response.json()

        if "choices" not in result or len(result["choices"]) == 0:
            return None, "❌ No response from DeepSeek API"

        text = result["choices"][0]["message"]["content"]

        return text, None

    except requests.exceptions.Timeout:
        return None, "⏱️ Request timeout."

    except requests.exceptions.ConnectionError:
        return None, "🌐 Connection error."

    except Exception as e:
        return None, f"Error: {str(e)}"


# ========================
# 🔹 Routes
# ========================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "✅ Backend is running",
        "api": "DeepSeek API",
        "model": MODEL,
        "endpoints": [
            "/generate-question (POST)",
            "/evaluate (POST)"
        ]
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
                "error": "Missing 'role' or 'experience' field"
            }), 400

        prompt = f"""
Generate ONE technical interview question
for a {role} with {experience} years of experience.

Keep it concise and practical.
"""

        question, error = call_deepseek(prompt)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"question": question}), 200

    except Exception as e:
        return jsonify({
            "error": f"Server error: {str(e)}"
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
                "error": "Missing 'question' or 'answer' field"
            }), 400

        prompt = f"""
Question: {question}

Answer: {answer}

Provide a structured evaluation:

1. Score out of 10
2. Strengths
3. Weaknesses
4. Improvements
5. Resources

Keep response concise but detailed.
"""

        feedback, error = call_deepseek(prompt)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"feedback": feedback}), 200

    except Exception as e:
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500


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
# 🔹 Run App
# ========================

if __name__ == "__main__":
    app.run(
        debug=False,
        port=5000,
        host="0.0.0.0"
    )