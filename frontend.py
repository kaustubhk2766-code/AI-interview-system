from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Get OpenRouter API Key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("❌ OPENROUTER_API_KEY not found in environment variables!")

REQUEST_TIMEOUT = 30

# Using a cost-effective model from OpenRouter
PRIMARY_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
FALLBACK_MODEL = "google/gemma-2-9b-it:free"

def call_openrouter(prompt, model=PRIMARY_MODEL):
    """Call OpenRouter API with OpenAI-compatible format"""
    
    # OpenRouter API endpoint
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
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
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        
        print(f"🔍 Status: {response.status_code}")
        print(f"🔍 Response: {response.text[:200]}")  # Log first 200 chars
        
        # Handle API errors
        if response.status_code == 401:
            return None, "❌ Invalid OpenRouter API Key. Check your OPENROUTER_API_KEY"
        elif response.status_code == 429:
            # Try fallback model before giving up
            if model == PRIMARY_MODEL:
                return call_openrouter(prompt, model=FALLBACK_MODEL)
            return None, "⏱️ Rate limit exceeded. Wait before trying again."
        elif response.status_code == 400:
            return None, f"❌ Bad request: {response.json().get('error', {}).get('message', 'Unknown error')}"
        elif response.status_code == 500:
            return None, "🔴 OpenRouter server error. Try again later."
        elif response.status_code != 200:
            return None, f"API Error: {response.status_code} - {response.text}"
        
        # Parse OpenRouter response (OpenAI-compatible format)
        result = response.json()
        
        # Check if response has choices
        if "choices" not in result or len(result["choices"]) == 0:
            return None, "❌ No response from OpenRouter API"
        
        # Extract text from OpenRouter response
        choice = result["choices"][0]
        if "message" not in choice or "content" not in choice["message"]:
            return None, "❌ Invalid OpenRouter response format"
        
        text = choice["message"]["content"]
        return text, None
        
    except requests.exceptions.Timeout:
        return None, "⏱️ Request timeout. OpenRouter took too long to respond."
    except requests.exceptions.ConnectionError:
        return None, "🌐 Connection error. Check your internet."
    except KeyError as e:
        return None, f"❌ Error parsing OpenRouter response: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"


# ========================
# 🔹 Routes
# ========================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "✅ Backend is running",
        "api": "OpenRouter API",
        "model": PRIMARY_MODEL,
        "endpoints": [
            "/generate-question (POST)",
            "/evaluate (POST)"
        ]
    })


@app.route("/generate-question", methods=["POST"])
def generate_question():
    """Generate a technical interview question based on role and experience."""
    try:
        data = request.json
        
        # Validate input
        role = data.get("role", "").strip()
        experience = data.get("experience", "").strip()
        
        if not role or not experience:
            return jsonify({"error": "Missing 'role' or 'experience' field"}), 400

        prompt = f"Generate ONE technical interview question for a {role} with {experience} years of experience. Keep it concise and practical."

        question, error = call_openrouter(prompt)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"question": question}), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@app.route("/evaluate", methods=["POST"])
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

        feedback, error = call_openrouter(prompt)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"feedback": feedback}), 200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# ---- Error handlers ----
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ========================
# For local development:
# python app.py

# For production (Gunicorn on Render):
# gunicorn app:app --bind 0.0.0.0:10000

if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")