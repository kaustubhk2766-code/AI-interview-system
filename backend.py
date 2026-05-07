from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# 🔐 Gemini API Key loaded from environment for security
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
if API_KEY:
    genai.configure(api_key=API_KEY)

# -------------------------------
# 🔹 Common Gemini Call Function
# -------------------------------
def call_gemini(prompt):
    if not API_KEY:
        return None, "Gemini API key is not set. Please set GEMINI_API_KEY in your environment."

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        
        print("🔍 Response:", response.text)
        
        if response.text:
            return response.text, None
        else:
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