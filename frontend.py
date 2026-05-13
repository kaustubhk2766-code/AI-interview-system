# frontend.py (Python + Flask Frontend)

from flask import Flask, render_template_string

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Interview Assistant</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 40px;
            font-family: Arial, sans-serif;
            background: #f1f5f9;
        }

        .container {
            max-width: 800px;
            margin: auto;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
        }

        input,
        textarea {
            width: 100%;
            padding: 12px;
            border-radius: 10px;
            border: 1px solid #cbd5e1;
            margin-top: 8px;
            margin-bottom: 15px;
        }

        button {
            background: #6366f1;
            color: white;
            border: none;
            padding: 12px 22px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 15px;
        }

        button:hover {
            opacity: 0.9;
        }

        .result {
            margin-top: 20px;
            background: #f8fafc;
            padding: 15px;
            border-radius: 10px;
            white-space: pre-wrap;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 12px;
            border-radius: 10px;
            margin-top: 15px;
        }
    </style>
</head>
<body>

<div class="container">

    <h1>AI Interview Assistant</h1>

    <div class="card">
        <h2>Generate Question</h2>

        <input
            type="text"
            id="role"
            placeholder="Job Role"
        />

        <input
            type="text"
            id="experience"
            placeholder="Years of Experience"
        />

        <button onclick="generateQuestion()">
            Generate Question
        </button>

        <div id="questionError"></div>

        <div id="questionResult" class="result" style="display:none"></div>
    </div>

    <div class="card">
        <h2>Evaluate Answer</h2>

        <textarea
            id="question"
            rows="3"
            placeholder="Interview Question"
        ></textarea>

        <textarea
            id="answer"
            rows="5"
            placeholder="Your Answer"
        ></textarea>

        <button onclick="evaluateAnswer()">
            Evaluate Answer
        </button>

        <div id="evalError"></div>

        <div id="feedbackResult" class="result" style="display:none"></div>
    </div>

</div>

<script>

const API_BASE = "https://ai-interview-system-1-k20m.onrender.com";

async function generateQuestion() {

    const role = document.getElementById("role").value;
    const experience = document.getElementById("experience").value;

    const errorBox = document.getElementById("questionError");
    const resultBox = document.getElementById("questionResult");

    errorBox.innerHTML = "";
    resultBox.style.display = "none";

    try {

        const response = await fetch(`${API_BASE}/generate-question`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                role,
                experience
            })
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        resultBox.style.display = "block";
        resultBox.innerHTML = `<strong>Question:</strong><br><br>${data.question}`;

        document.getElementById("question").value = data.question;

    } catch (err) {

        errorBox.innerHTML = `<div class="error">${err.message}</div>`;
    }
}

async function evaluateAnswer() {

    const question = document.getElementById("question").value;
    const answer = document.getElementById("answer").value;

    const errorBox = document.getElementById("evalError");
    const resultBox = document.getElementById("feedbackResult");

    errorBox.innerHTML = "";
    resultBox.style.display = "none";

    try {

        const response = await fetch(`${API_BASE}/evaluate`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                question,
                answer
            })
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        resultBox.style.display = "block";
        resultBox.innerHTML = `<strong>Feedback:</strong><br><br>${data.feedback}`;

    } catch (err) {

        errorBox.innerHTML = `<div class="error">${err.message}</div>`;
    }
}

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

if __name__ == "__main__":
    app.run(debug=True, port=3000)



