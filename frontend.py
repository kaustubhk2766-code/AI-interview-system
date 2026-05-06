from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# 🔐 API Key from environment (NEVER hardcode!)
API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("❌ OPENAI_API_KEY not found in environment variables!")

# ⏱️ Rate limiting to prevent abuse
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Request timeout to avoid hanging
REQUEST_TIMEOUT = 30  # seconds


# -------------------------------
# 🔹 Common OpenAI Call Function
# -------------------------------
def call_openai(prompt):
    """Call OpenAI API with error handling and timeout."""
    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an expert technical interviewer. Provide constructive, detailed feedback."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000  # ← IMPORTANT: Limit response length to save costs
    }

    try:
        response = requests.post(
            url, 
            headers=headers, 
            json=data,
            timeout=REQUEST_TIMEOUT
        )

        print(f"🔍 Status: {response.status_code}")

        # Handle common API errors
        if response.status_code == 401:
            return None, "❌ API Key is invalid or expired. Update it in .env"
        elif response.status_code == 429:
            return None, "⏱️ Rate limit exceeded. Wait before trying again."
        elif response.status_code == 500:
            return None, "🔴 OpenAI server error. Try again later."
        elif response.status_code != 200:
            return None, f"API Error: {response.status_code} - {response.text}"

        result = response.json()
        text = result["choices"][0]["message"]["content"]
        return text, None

    except requests.exceptions.Timeout:
        return None, "⏱️ Request timeout. OpenAI took too long to respond."
    except requests.exceptions.ConnectionError:
        return None, "🌐 Connection error. Check your internet."
    except Exception as e:
        return None, f"Error: {str(e)}"


# -------------------------------
# 🔹 Home Route
# -------------------------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "✅ Backend is running",
        "api": "OpenAI GPT-4o-mini",
        "endpoints": [
            "/generate-question (POST)",
            "/evaluate (POST)"
        ]
    })


# -------------------------------
# 🔹 Generate Question
# -------------------------------
@app.route("/generate-question", methods=["POST"])
@limiter.limit("10 per minute")  # Prevent spam
def generate_question():
    """Generate a technical interview question based on role and experience."""
    try:
        data = request.json
        
        # Validate input
        role = data.get("role", "").strip()
        experience = data.get("experience", "").strip()
        
        if not role or not experience:
            return jsonify({"error": "Missing 'role' or 'experience' field"}), 400

        prompt = f"Generate ONE technical interview question for a {role} with {experience} years of experience. Keep it concise."

        question, error = call_openai(prompt)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"question": question}), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# -------------------------------
# 🔹 Evaluate Answer
# -------------------------------
@app.route("/evaluate", methods=["POST"])
@limiter.limit("10 per minute")
def evaluate():
    """Evaluate a candidate's answer to an interview question."""
    try:
        data = request.json
        
        # Validate input
        question = data.get("question", "").strip()
        answer = data.get("answer", "").strip()
        
        if not question or not answer:
            return jsonify({"error": "Missing 'question' or 'answer' field"}), 400

        prompt = f"""
Question: {question}

Answer: {answer}

Provide a structured evaluation:
1. **Score**: (out of 10)
2. **Strengths**: (2-3 key points)
3. **Weaknesses**: (2-3 areas to improve)
4. **Improvements**: (specific suggestions)
5. **Resources**: (1-2 learning links or topics)

Keep response concise but detailed.
"""

        feedback, error = call_openai(prompt)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"feedback": feedback}), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ---- Error handlers ----
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded. Please wait before making more requests."}), 429


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


# ========================
if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")