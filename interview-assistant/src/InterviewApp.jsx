import { useState } from 'react';
import './App.css';

const API_URL = 'https://ai-interview-system-dno5.onrender.com/';

async function postJson(path, payload) {
  const response = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

function InterviewApp() {
  const [role, setRole] = useState('Software Engineer');
  const [experience, setExperience] = useState('2');
  const [question, setQuestion] = useState('');
  const [generatedQuestion, setGeneratedQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState('');
  const [loadingQuestion, setLoadingQuestion] = useState(false);
  const [loadingFeedback, setLoadingFeedback] = useState(false);
  const [error, setError] = useState('');

  const handleGenerateQuestion = async (event) => {
    event.preventDefault();
    setError('');
    setGeneratedQuestion('');
    setFeedback('');
    setLoadingQuestion(true);

    try {
      const data = await postJson('/generate-question', { role, experience });
      const nextQuestion = data.question?.trim() || '';
      setGeneratedQuestion(nextQuestion);
      setQuestion(nextQuestion);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingQuestion(false);
    }
  };

  const handleEvaluate = async (event) => {
    event.preventDefault();
    setError('');
    setFeedback('');
    setLoadingFeedback(true);

    try {
      const data = await postJson('/evaluate', {
        question: question.trim(),
        answer: answer.trim(),
      });
      setFeedback(data.feedback);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingFeedback(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Interview Assistant</h1>
        <p>Generate interview questions and evaluate candidate answers.</p>
      </header>

      <main className="app-content">
        <section className="card">
          <h2>1. Generate a question</h2>
          <form onSubmit={handleGenerateQuestion}>
            <label>
              Role
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="e.g. Backend Developer"
              />
            </label>
            <label>
              Experience (years)
              <input
                type="text"
                value={experience}
                onChange={(e) => setExperience(e.target.value)}
                placeholder="e.g. 3"
              />
            </label>
            <button type="submit" disabled={loadingQuestion}>
              {loadingQuestion ? 'Generating...' : 'Generate Question'}
            </button>
          </form>

          {generatedQuestion && (
            <div className="result-box">
              <h3>Generated question</h3>
              <p>{generatedQuestion}</p>
            </div>
          )}
        </section>

        <section className="card">
          <h2>2. Evaluate an answer</h2>
          <form onSubmit={handleEvaluate}>
            <label>
              Question
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={3}
                placeholder="Paste or edit the interview question"
              />
            </label>
            <label>
              Candidate answer
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                rows={5}
                placeholder="Enter the candidate's answer"
              />
            </label>
            <button type="submit" disabled={loadingFeedback}>
              {loadingFeedback ? 'Evaluating...' : 'Evaluate Answer'}
            </button>
          </form>

          {feedback && (
            <div className="result-box">
              <h3>Feedback</h3>
              <pre>{feedback}</pre>
            </div>
          )}
        </section>

        {error && (
          <div className="error-box">
            <strong>Error:</strong> {error}
          </div>
        )}
      </main>
    </div>
  );
}

export default InterviewApp;
