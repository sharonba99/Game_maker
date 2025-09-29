import React, { useEffect, useRef, useState, type ReactNode } from "react";
import { Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";

/** ---------- small fetch helper ---------- */
type Ok<T> = { ok: true; data: T };
type Err = { ok: false; error: { code: string; message: string } };
type J<T> = Ok<T> | Err;

function useApi(baseUrl: string) {
  async function get<T>(p: string): Promise<J<T>> {
    const r = await fetch(`${baseUrl}${p}`);
    return r.json();
  }
  async function post<T>(p: string, body: any): Promise<J<T>> {
    const r = await fetch(`${baseUrl}${p}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return r.json();
  }
  return { get, post };
}

/** ---------- auth guard ---------- */
function RequireAuth({ children }: { children: ReactNode }) {
  const hasUser = !!JSON.parse(localStorage.getItem("auth") || "null")?.username;
  if (!hasUser) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

/** ---------- Auth page (Login + Signup toggle) ---------- */
function AuthPage({ baseUrl }: { baseUrl: string }) {
  const api = useApi(baseUrl);
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [username, setU] = useState("");
  const [password, setP] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const nav = useNavigate();

  async function doLogin() {
    setErr(null); setMsg(null);
    const res = await api.post<{ user_id: number; username: string }>("/users/login", { username, password });
    if (!res.ok) { setErr(res.error.message); return; }
    localStorage.setItem("auth", JSON.stringify(res.data)); // {user_id, username}
    nav("/play");
  }

  async function doSignup() {
    setErr(null); setMsg(null);
    const res = await api.post<{ id: number; username: string }>("/users/signup", { username, password });
    if (!res.ok) { setErr(res.error.message); return; }
    setMsg("Account created. Logging you in...");
    await doLogin();
  }

  return (
    <div style={{ padding: 16, maxWidth: 420, margin: "0 auto" }}>
      <h2>{mode === "login" ? "Login" : "Signup"}</h2>

      {err && <div style={{ color: "crimson", marginBottom: 8 }}>Error: {err}</div>}
      {msg && <div style={{ color: "green", marginBottom: 8 }}>{msg}</div>}

      <div>Username</div>
      <input value={username} onChange={(e) => setU(e.target.value)} />
      <div style={{ marginTop: 8 }}>Password</div>
      <input type="password" value={password} onChange={(e) => setP(e.target.value)} />

      <div style={{ marginTop: 12 }}>
        {mode === "login" ? (
          <button onClick={doLogin}>Login</button>
        ) : (
          <button onClick={doSignup}>Create account</button>
        )}
      </div>

      <div style={{ marginTop: 12, fontSize: 13 }}>
        {mode === "login" ? (
          <>
            אין לך חשבון?{" "}
            <button onClick={() => { setMode("signup"); setErr(null); setMsg(null); }} style={{ textDecoration: "underline" }}>
              Signup
            </button>
          </>
        ) : (
          <>
            כבר רשומה?{" "}
            <button onClick={() => { setMode("login"); setErr(null); setMsg(null); }} style={{ textDecoration: "underline" }}>
              Login
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/** ---------- navbar ---------- */
function Navbar({ onLogout }: { onLogout: () => void }) {
  const auth = JSON.parse(localStorage.getItem("auth") || "null");
  return (
    <nav style={{ display: "flex", gap: 12, padding: 8, borderBottom: "1px solid #ddd" }}>
      <Link to="/play">Play</Link>
      <Link to="/createquiz">CreateQuiz</Link>
      <div style={{ marginLeft: "auto" }}>
        {auth?.username ? (
          <>
            <span style={{ marginRight: 8 }}>Hello, {auth.username}</span>
            <button onClick={onLogout}>Logout</button>
          </>
        ) : (
          <Link to="/login">Login / Signup</Link>
        )}
      </div>
    </nav>
  );
}

/** ---------- types for leaderboard ---------- */
type LeaderRow = { player_name: string; score: number; /* duration_ms?: number */ };

/** ---------- play page ---------- */
function Play({ baseUrl }: { baseUrl: string }) {
  const api = useApi(baseUrl);
  const [topics, setTopics] = useState<string[]>([]);
  const [topic, setTopic] = useState("");
  const [quizzes, setQuizzes] = useState<{ id: number; title: string; count: number }[]>([]);
  const [quizId, setQuizId] = useState<number | null>(null);

  const [sid, setSid] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [current, setCurrent] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [board, setBoard] = useState<{ player_name: string; score: number }[]>([]);
  const [answering, setAnswering] = useState(false);
  const startMsRef = useRef(0);

  const playerName = JSON.parse(localStorage.getItem("auth") || "null")?.username || "guest";

  useEffect(() => {
    (async () => {
      const t = await api.get<string[]>("/library/topics");
      if (t.ok) setTopics(t.data);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadQuizzes(t: string) {
    setTopic(t);
    setQuizId(null);
    setBoard([]);
    const res = await api.get<any>(`/library/quizzes?topic=${encodeURIComponent(t)}`);
    if (res.ok) setQuizzes(res.data);
  }

  async function start() {
    if (!quizId) return;
    setErr(null);
    setBoard([]);
    try {
      const res = await api.post<{ session_id: number }>(`/library/session/create`, {
        quiz_id: quizId,
        player_name: playerName,
      });
      console.log("start/session_create:", res);
      if (!res.ok) { setErr(res.error.message); return; }
      setSid(res.data.session_id);
      await loadCurrent(res.data.session_id);
      setScore(0);
    } catch (e: any) {
      setErr("Network error starting session");
      console.error(e);
    }
  }

  async function loadCurrent(sidX: number) {
    try {
      const res = await api.get<any>(`/library/session/${sidX}/current`);
      console.log("current:", res);
      if (!res.ok) { setErr(res.error.message); return; }
      setCurrent(res.data);
      if (!res.data.finished) startMsRef.current = performance.now();
      if (res.data.finished && quizId) {
        await loadBoard(quizId);
      }
    } catch (e: any) {
      setErr("Network error loading question");
      console.error(e);
    }
  }

  async function answer(opt: string) {
    if (!sid || answering) return;
    setAnswering(true);
    setErr(null);
    try {
      const ms = Math.floor(performance.now() - startMsRef.current);
      const res = await api.post<any>(`/library/session/${sid}/answer`, { answer: opt, client_ms: ms });
      console.log("answer:", res);
      if (!res.ok) { setErr(res.error.message); setAnswering(false); return; }
      if (typeof res.data.score === "number") setScore(res.data.score);

      if (res.data.finished) {
        setCurrent({ finished: true });
        if (quizId) await loadBoard(quizId);
      } else if (res.data.next) {
        setCurrent(res.data.next);
        startMsRef.current = performance.now();
      } else {
        await loadCurrent(sid);
      }
    } catch (e: any) {
      setErr("Network error submitting answer");
      console.error(e);
    } finally {
      setAnswering(false);
    }
  }

  async function loadBoard(qid: number) {
    try {
      const r = await api.get<{ top: { player_name: string; score: number }[] }>(`/library/leaderboard?quiz_id=${qid}`);
      console.log("board:", r);
      if (r.ok) setBoard(r.data.top);
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div style={{ padding: 16 }}>
      <h2>Play</h2>
      <div style={{ marginBottom: 6 }}>Playing as: <b>{playerName}</b></div>
      {err && <div style={{ color: "crimson" }}>Error: {err}</div>}

      <div>Topic</div>
      <select value={topic} onChange={(e) => loadQuizzes(e.target.value)}>
        <option value="">-- choose topic --</option>
        {topics.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>

      {topic && (
        <>
          <div style={{ marginTop: 8 }}>Quiz</div>
          <select value={quizId ?? ""} onChange={(e) => setQuizId(+e.target.value || null)}>
            <option value="">-- choose quiz --</option>
            {quizzes.map((q) => (
              <option key={q.id} value={q.id}>{q.title} ({q.count} Qs)</option>
            ))}
          </select>
          <div><button type="button" style={{ marginTop: 8 }} onClick={start}>Start</button></div>
        </>
      )}

      {current && !current.finished && (
        <div style={{ marginTop: 16 }}>
          <div>Score: {score}</div>
          <div style={{ fontSize: 18, margin: "8px 0" }}>{current.question}</div>
          <div style={{ display: "grid", gap: 8 }}>
            {current.options?.map((o: string, i: number) => (
              <button
                key={i}
                type="button"
                onClick={() => answer(o)}
                disabled={answering}
              >
                {answering ? "…" : o}
              </button>
            ))}
          </div>
          <div style={{ marginTop: 8 }}>Q {(current.index ?? 0) + 1} / {current.total}</div>
        </div>
      )}

      {current?.finished && (
        <div style={{ marginTop: 16 }}>
          <h3>Finished!</h3>
          <div>Final score: {score}</div>

          {/* Leaderboard */}
          <div style={{ marginTop: 16 }}>
            <h3>Top 10</h3>
            {board.length === 0 ? (
              <div>No scores yet</div>
            ) : (
              <div style={{ display: "grid", gap: 6, maxWidth: 520 }}>
                {board.map((r, i) => (
                  <div key={i} style={{ display: "flex", justifyContent: "space-between", border: "1px solid #ddd", padding: "6px 10px", borderRadius: 8 }}>
                    <div>{i + 1}. {r.player_name}</div>
                    <div>{r.score}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/** ---------- create quiz page ---------- */
function CreateQuiz({ baseUrl }: { baseUrl: string }) {
  const api = useApi(baseUrl);
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [diff, setDiff] = useState("");
  const [quizId, setQuizId] = useState<number | null>(null);

  // question form
  const [q, setQ] = useState("");
  const [a1, setA1] = useState("");
  const [a2, setA2] = useState("");
  const [a3, setA3] = useState("");
  const [a4, setA4] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function create() {
    setErr(null); setMsg(null);
    const res = await api.post<{ id: number }>(`/library/quizzes`, { title, topic, difficulty: diff });
    if (!res.ok) { setErr(res.error.message); return; }
    setQuizId(res.data.id);
    setMsg("Quiz created: id " + res.data.id);
  }

  async function addQuestion() {
    if (!quizId) { setErr("Create quiz first"); return; }
    setErr(null); setMsg(null);
    const res = await api.post<{ id: number }>(`/library/questions`, {
      quiz_id: quizId, question: q, difficulty: diff, answers: [a1, a2, a3, a4]
    });
    if (!res.ok) { setErr(res.error.message); return; }
    setMsg("Question added: id " + res.data.id);
    setQ(""); setA1(""); setA2(""); setA3(""); setA4("");
  }

  return (
    <div style={{ padding: 16 }}>
      <h2>Create Quiz & Questions</h2>
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      {msg && <div style={{ color: "green" }}>{msg}</div>}

      <h3>New Quiz</h3>
      <div>Title</div><input value={title} onChange={(e) => setTitle(e.target.value)} />
      <div>Topic</div><input value={topic} onChange={(e) => setTopic(e.target.value)} />
      <div>Difficulty</div><input value={diff} onChange={(e) => setDiff(e.target.value)} placeholder="easy/medium/hard" />
      <div><button style={{ marginTop: 8 }} onClick={create}>Create quiz</button></div>

      <h3 style={{ marginTop: 16 }}>Add Question (answers[0] is correct)</h3>
      <div>Question</div><input value={q} onChange={(e) => setQ(e.target.value)} />
      <div>Answers</div>
      <input placeholder="correct" value={a1} onChange={(e) => setA1(e.target.value)} />
      <input placeholder="wrong 1" value={a2} onChange={(e) => setA2(e.target.value)} />
      <input placeholder="wrong 2" value={a3} onChange={(e) => setA3(e.target.value)} />
      <input placeholder="wrong 3" value={a4} onChange={(e) => setA4(e.target.value)} />
      <div><button style={{ marginTop: 8 }} onClick={addQuestion}>Add question</button></div>
    </div>
  );
}

/** ---------- app root ---------- */
export default function App() {
  const [baseUrl, setBaseUrl] = useState("http://localhost:5001");
  const nav = useNavigate();
  function logout() {
    localStorage.removeItem("auth");
    nav("/login");
  }
  return (
    <div>
      <Navbar onLogout={logout} />
      <div style={{ padding: 8 }}>
        Base URL: <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} style={{ width: 260 }} />
      </div>
      <Routes>
        <Route path="/login" element={<AuthPage baseUrl={baseUrl} />} />
        <Route path="/play" element={<RequireAuth><Play baseUrl={baseUrl} /></RequireAuth>} />
        <Route path="/createquiz" element={<RequireAuth><CreateQuiz baseUrl={baseUrl} /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/play" replace />} />
      </Routes>
    </div>
  );
}
