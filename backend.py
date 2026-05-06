from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# 🔐 OpenAI API Key loaded from environment for security
API_KEY = os.getenv("OPENAI_API_KEY")

# -------------------------------
# 🔹 Common OpenAI Call Function
# -------------------------------
def call_openai(prompt):
    if not API_KEY:
        return None, "OpenAI API key is not set. Please set OPENAI_API_KEY in your environment."

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4o-mini",   # fast + cheap + good
        "messages": [
            {"role": "system", "content": "You are an expert interviewer."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)

        print("🔍 Status:", response.status_code)
        print("🔍 Response:", response.text)

        if response.status_code != 200:
            return None, response.text

        result = response.json()
        text = result["choices"][0]["message"]["content"]

        return text, None

    except Exception as e:
        return None, str(e)


# -------------------------------
# 🔹 Home Route
# -------------------------------
@app.route("/")
def home():
    return "Backend is running with OpenAI ✅"


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

        question, error = call_openai(prompt)

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

        feedback, error = call_openai(prompt)

        if error:
            return jsonify({"error": error}), 500

        return jsonify({"feedback": feedback})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)