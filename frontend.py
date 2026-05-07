import { useState, useRef, useCallback } from "react";

const API_BASE = "https://ai-interview-system-1-k20m.onrender.com";

// ========================
// 🔹 API Calls
// ========================

async function fetchQuestion(role, experience) {
  const res = await fetch(`${API_BASE}/generate-question`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, experience }),
  });

  const data = await res.json();

  if (!res.ok || data.error) {
    throw new Error(data.error || "Failed to generate question");
  }

  return data;
}

async function fetchEvaluation(question, answer) {
  const res = await fetch(`${API_BASE}/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, answer }),
  });

  const data = await res.json();

  if (!res.ok || data.error) {
    throw new Error(data.error || "Failed to evaluate answer");
  }

  return data;
}

// ========================
// 🔹 Reusable Components
// ========================

function Badge({ cached }) {
  if (!cached) return null;

  return (
    <span
      style={{
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.07em",
        textTransform: "uppercase",
        padding: "3px 10px",
        borderRadius: 999,
        background: "#ecfdf5",
        color: "#065f46",
        border: "1px solid #a7f3d0",
        marginLeft: 10,
      }}
    >
      ⚡ Cached
    </span>
  );
}

function Spinner() {
  return (
    <span
      style={{
        display: "inline-block",
        width: 16,
        height: 16,
        border: "2px solid #e2e8f0",
        borderTopColor: "#6366f1",
        borderRadius: "50%",
        animation: "spin 0.7s linear infinite",
        verticalAlign: "middle",
        marginRight: 8,
      }}
    />
  );
}

function ErrorBox({ message }) {
  if (!message) return null;

  return (
    <div
      style={{
        background: "#fef2f2",
        border: "1px solid #fecaca",
        borderRadius: 12,
        padding: "12px 16px",
        color: "#991b1b",
        fontSize: 13,
        marginTop: 12,
      }}
    >
      ⚠️ {message}
    </div>
  );
}

function SectionCard({ children }) {
  return (
    <div
      style={{
        background: "#fff",
        border: "1px solid #e2e8f0",
        borderRadius: 20,
        padding: 28,
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      {children}
    </div>
  );
}

function Label({ children }) {
  return (
    <div
      style={{
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.1em",
        textTransform: "uppercase",
        color: "#94a3b8",
        marginBottom: 8,
      }}
    >
      {children}
    </div>
  );
}

function Input({ value, onChange, placeholder }) {
  return (
    <input
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      style={{
        width: "100%",
        padding: "11px 14px",
        border: "1px solid #e2e8f0",
        borderRadius: 10,
        fontSize: 14,
        color: "#1e293b",
        outline: "none",
        fontFamily: "inherit",
        background: "#f8fafc",
        boxSizing: "border-box",
      }}
    />
  );
}

function Textarea({ value, onChange, placeholder, rows = 5 }) {
  return (
    <textarea
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      rows={rows}
      style={{
        width: "100%",
        padding: "12px 14px",
        border: "1px solid #e2e8f0",
        borderRadius: 10,
        fontSize: 14,
        color: "#1e293b",
        outline: "none",
        fontFamily: "inherit",
        background: "#f8fafc",
        resize: "vertical",
        lineHeight: 1.6,
        boxSizing: "border-box",
      }}
    />
  );
}

function PrimaryButton({ onClick, disabled, loading, children }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      style={{
        background:
          disabled || loading
            ? "#c7d2fe"
            : "linear-gradient(135deg, #6366f1, #8b5cf6)",
        color: "#fff",
        border: "none",
        borderRadius: 12,
        padding: "13px 26px",
        fontSize: 14,
        fontWeight: 700,
        cursor: disabled || loading ? "not-allowed" : "pointer",
        display: "inline-flex",
        alignItems: "center",
      }}
    >
      {loading && <Spinner />}
      {children}
    </button>
  );
}

// ========================
// 🔹 Generate Question
// ========================

function GenerateQuestion({ onQuestionGenerated }) {
  const [role, setRole] = useState("");
  const [experience, setExperience] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleGenerate = useCallback(async () => {
    if (!role.trim() || !experience.trim()) {
      setError("Please enter both role and experience.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await fetchQuestion(role.trim(), experience.trim());

      setResult(data);

      if (onQuestionGenerated) {
        onQuestionGenerated(data.question);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [role, experience, onQuestionGenerated]);

  return (
    <SectionCard>
      <h2 style={{ marginBottom: 20 }}>🎯 Generate Question</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 14,
          marginBottom: 16,
        }}
      >
        <div>
          <Label>Job Role</Label>

          <Input
            value={role}
            onChange={(e) => setRole(e.target.value)}
            placeholder="Frontend Developer"
          />
        </div>

        <div>
          <Label>Experience</Label>

          <Input
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
            placeholder="3"
          />
        </div>
      </div>

      <PrimaryButton onClick={handleGenerate} loading={loading}>
        {loading ? "Generating..." : "Generate Question"}
      </PrimaryButton>

      <ErrorBox message={error} />

      {result && (
        <div
          style={{
            marginTop: 20,
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: 12,
            padding: 18,
          }}
        >
          <div style={{ marginBottom: 10 }}>
            <strong>Question</strong>
            <Badge cached={result.cached} />
          </div>

          <p>{result.question}</p>
        </div>
      )}
    </SectionCard>
  );
}

// ========================
// 🔹 Evaluate Answer
// ========================

function EvaluateAnswer({ prefillQuestion }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const prevPrefill = useRef("");

  if (prefillQuestion && prefillQuestion !== prevPrefill.current) {
    prevPrefill.current = prefillQuestion;
    setQuestion(prefillQuestion);
  }

  const handleEvaluate = useCallback(async () => {
    if (!question.trim() || !answer.trim()) {
      setError("Please enter both question and answer.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await fetchEvaluation(question, answer);

      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [question, answer]);

  return (
    <SectionCard>
      <h2 style={{ marginBottom: 20 }}>📋 Evaluate Answer</h2>

      <div style={{ marginBottom: 14 }}>
        <Label>Question</Label>

        <Textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Enter interview question"
          rows={3}
        />
      </div>

      <div style={{ marginBottom: 16 }}>
        <Label>Answer</Label>

        <Textarea
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Enter your answer"
          rows={5}
        />
      </div>

      <PrimaryButton onClick={handleEvaluate} loading={loading}>
        {loading ? "Evaluating..." : "Evaluate Answer"}
      </PrimaryButton>

      <ErrorBox message={error} />

      {result && (
        <div
          style={{
            marginTop: 20,
            background: "#f8fafc",
            border: "1px solid #e2e8f0",
            borderRadius: 12,
            padding: 18,
          }}
        >
          <div style={{ marginBottom: 10 }}>
            <strong>Feedback</strong>
            <Badge cached={result.cached} />
          </div>

          <pre
            style={{
              whiteSpace: "pre-wrap",
              fontFamily: "inherit",
              lineHeight: 1.7,
            }}
          >
            {result.feedback}
          </pre>
        </div>
      )}
    </SectionCard>
  );
}

// ========================
// 🔹 Main App
// ========================

export default function InterviewApp() {
  const [generatedQuestion, setGeneratedQuestion] = useState("");

  return (
    <>
      <style>{`
        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          font-family: Arial, sans-serif;
          background: #f1f5f9;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>

      <div
        style={{
          maxWidth: 760,
          margin: "0 auto",
          padding: 40,
        }}
      >
        <div style={{ textAlign: "center", marginBottom: 36 }}>
          <h1
            style={{
              fontSize: 36,
              marginBottom: 10,
              color: "#0f172a",
            }}
          >
            AI Interview Assistant
          </h1>

          <p style={{ color: "#64748b" }}>
            Generate interview questions and evaluate answers
          </p>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 20,
          }}
        >
          <GenerateQuestion
            onQuestionGenerated={setGeneratedQuestion}
          />

          <EvaluateAnswer
            prefillQuestion={generatedQuestion}
          />
        </div>

        <div
          style={{
            textAlign: "center",
            marginTop: 30,
            color: "#94a3b8",
            fontSize: 13,
          }}
        >
          Backend Connected:
          {" "}
          {API_BASE}
        </div>
      </div>
    </>
  );
}