import React, { useEffect, useState } from "react";

/**
 * Kahoot-style Mini Frontend
 * -----------------------------------------------------------
 * One-file React app to talk to your Flask API.
 * Screens:
 * 1) Login (get JWT)
 * 2) Lobby (start session: choose topic + number of questions)
 * 3) Question (show current question, submit answer, timer optional)
 * 4) Result (final score)
 * 5) Leaderboard (top scores)
 */

const Card = ({ children }: { children: React.ReactNode }) => (
  <div className="mx-auto w-full max-w-xl rounded-2xl shadow p-6 bg-white border">
    {children}
  </div>
);

const Button = ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
  <button
    {...props}
    className={`px-4 py-2 rounded-xl shadow hover:shadow-md active:scale-[.99] transition ${
      (props as any).className || ""
    }`}
  >
    {children}
  </button>
);

const Input = (
  props: React.InputHTMLAttributes<HTMLInputElement> & { label?: string }
) => (
  <label className="block mb-3">
    {props.label && <div className="mb-1 text-sm text-gray-600">{props.label}</div>}
    <input
      {...props}
      className={`w-full rounded-xl border px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 ${
        (props as any).className || ""
      }`}
    />
  </label>
);

const Select = (
  props: React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string }
) => (
  <label className="block mb-3">
    {props.label && <div className="mb-1 text-sm text-gray-600">{props.label}</div>}
    <select
      {...props}
      className={`w-full rounded-xl border px-3 py-2 outline-none focus:ring-2 focus:ring-indigo-500 ${
        (props as any).className || ""
      }`}
    />
  </label>
);

// Helper to wrap fetch with base URL + auth
function useApi(baseUrl: string, token: string | null) {
  async function get(path: string) {
    const r = await fetch(`${baseUrl}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    return r.json();
  }
  async function post(path: string, body: any) {
    const r = await fetch(`${baseUrl}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    });
    return r.json();
  }
  return { get, post };
}

export default function App() {
  const [baseUrl, setBaseUrl] = useState("http://localhost:5001");

  // Auth
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));

  // Quiz state
  const [player, setPlayer] = useState("");
  const [topic, setTopic] = useState("");
  const [count, setCount] = useState(5);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [currentQ, setCurrentQ] = useState<{ id: number; question: string } | null>(null);
  const [answer, setAnswer] = useState("");
  const [score, setScore] = useState(0);
  const [finished, setFinished] = useState(false);
  const [leaderboard, setLeaderboard] = useState<{ player_name: string; score: number }[]>([]);
  const [view, setView] = useState<"login" | "lobby" | "question" | "result" | "leaderboard">(
    token ? "lobby" : "login"
  );
  const [error, setError] = useState<string | null>(null);

  const api = useApi(baseUrl, token);

  useEffect(() => {
    if (!token) localStorage.removeItem("token");
    else localStorage.setItem("token", token);
  }, [token]);

  async function handleLogin() {
    setError(null);
    try {
      const res = await api.post("/users/login", { username, password });
      if (!res.ok && !res.message?.toLowerCase().includes("success")) {
        throw new Error(res?.error?.message || "Login failed");
      }
      setToken(res.data?.access_token || "dev-token");
      setView("lobby");
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function startSession() {
    setError(null);
    try {
      const body: any = { player_name: player || username, n: count };
      if (topic) body.topic = topic;
      const res = await api.post("/library/session/create", body);
      if (!res.ok) throw new Error(res?.error?.message || "Create session failed");
      setSessionId(res.data.session_id);
      await fetchCurrent(res.data.session_id);
      setScore(0);
      setFinished(false);
      setView("question");
    } catch (e: any) {
      setError(e.message);
    }
  }

  async function fetchCurrent(sid = sessionId) {
    if (!sid) return;
    const res = await api.get(`/library/session/${sid}/current`);
    if (!res.ok) {
      setError(res?.error?.message || "Failed to load question");
      return;
    }
    if (res.data.finished) {
      setFinished(true);
      setCurrentQ(null);
      setView("result");
    } else {
      setCurrentQ(res.data);
      setAnswer("");
    }
  }

  async function submitAnswer() {
    if (!sessionId) return;
    const res = await api.post(`/library/session/${sessionId}/answer`, { answer });
    if (!res.ok) {
      setError(res?.error?.message || "Failed to submit");
      return;
    }
    setScore(res.data.score);
    if (res.data.finished) {
      setFinished(true);
      setView("result");
      await loadLeaderboard();
    } else {
      await fetchCurrent();
    }
  }

  async function loadLeaderboard() {
    const res = await api.get("/library/leaderboard");
    if (res.ok) setLeaderboard(res.data);
  }

  const header = (
    <header className="py-6 text-center">
      <h1 className="text-3xl font-bold">Trivia Creator – Mini Quiz</h1>
      <p className="text-gray-600">Kahoot-style flow: Login → Start → Answer → Result → Leaderboard</p>
    </header>
  );

  const baseConfig = (
    <div className="fixed top-3 right-3 flex gap-2 items-center text-sm">
      <Input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} label="Base URL" />
      {token ? (
        <Button onClick={() => { setToken(null); setView("login"); }}>Logout</Button>
      ) : null}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 to-white text-gray-900 p-6">
      {baseConfig}
      {header}
      {error && (
        <div className="mx-auto mb-4 w-full max-w-xl text-red-700 bg-red-50 border border-red-200 p-3 rounded-xl">
          {error}
        </div>
      )}

      {view === "login" && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">Login</h2>
          <div className="grid grid-cols-1 gap-2">
            <Input label="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
            <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            <Button className="bg-indigo-600 text-white" onClick={handleLogin}>Login</Button>
            <p className="text-xs text-gray-500 mt-2">No signup UI here – create users via Postman or add a quick signup route later.</p>
          </div>
        </Card>
      )}

      {view === "lobby" && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">Start a Session</h2>
          <div className="grid grid-cols-1 gap-2">
            <Input label="Player name" value={player} onChange={(e) => setPlayer(e.target.value)} placeholder={username || "guest"} />
            <Input label="Topic (optional)" value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Math / Geography ..." />
            <Input label="Number of questions" type="number" min={1} max={20} value={count} onChange={(e) => setCount(parseInt(e.target.value || "5", 10))} />
            <div className="flex gap-2">
              <Button className="bg-indigo-600 text-white" onClick={startSession}>Start</Button>
              <Button className="border" onClick={async () => { await loadLeaderboard(); setView("leaderboard"); }}>View Leaderboard</Button>
            </div>
          </div>
        </Card>
      )}

      {view === "question" && (
        <Card>
          <h2 className="text-xl font-semibold mb-2">Question</h2>
          {currentQ ? (
            <>
              <div className="mb-4 text-lg">{currentQ.question}</div>
              <Input label="Your answer" value={answer} onChange={(e) => setAnswer(e.target.value)} />
              <div className="flex gap-2">
                <Button className="bg-indigo-600 text-white" onClick={submitAnswer}>Submit</Button>
                <Button className="border" onClick={() => fetchCurrent()}>Skip</Button>
              </div>
              <div className="mt-4 text-sm text-gray-600">Score: {score}</div>
            </>
          ) : (
            <div>Loading...</div>
          )}
        </Card>
      )}

      {view === "result" && (
        <Card>
          <h2 className="text-xl font-semibold mb-2">Result</h2>
          <p className="mb-4">Final score: <b>{score}</b></p>
          <div className="flex gap-2">
            <Button className="bg-indigo-600 text-white" onClick={async () => { await loadLeaderboard(); setView("leaderboard"); }}>Leaderboard</Button>
            <Button className="border" onClick={() => setView("lobby")}>Back to Lobby</Button>
          </div>
        </Card>
      )}

      {view === "leaderboard" && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">Leaderboard (Top 10)</h2>
          <div className="space-y-2">
            {leaderboard.length === 0 ? (
              <div className="text-gray-500">No scores yet</div>
            ) : leaderboard.map((row, i) => (
              <div key={i} className="flex items-center justify-between border rounded-xl px-3 py-2">
                <div className="font-medium">{row.player_name}</div>
                <div className="text-gray-600">{row.score}</div>
              </div>
            ))}
          </div>
          <div className="mt-4">
            <Button className="border" onClick={() => setView("lobby")}>Back</Button>
          </div>
        </Card>
      )}
    </div>
  );
}
