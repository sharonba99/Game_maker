import React, { useEffect, useMemo, useRef, useState } from "react";

type TOk<T> = { ok: true; data: T };
type TErr = { ok: false; error: { code: string; message: string } };
type J<T> = TOk<T> | TErr;

function useApi(baseUrl: string) {
  async function get<T>(path: string): Promise<J<T>> {
    const r = await fetch(`${baseUrl}${path}`);
    return r.json();
  }
  async function post<T>(path: string, body: any): Promise<J<T>> {
    const r = await fetch(`${baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return r.json();
  }
  async function put<T>(path: string, body: any): Promise<J<T>> {
    const r = await fetch(`${baseUrl}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return r.json();
  }
  return { get, post, put };
}

type QuizRow = { id: number; title: string; topic: string; difficulty?: string; count: number };
type CurrentQ = { finished: boolean; question_id?: number; question?: string; options?: string[]; index?: number; total?: number };
type LeaderTop = { player_name: string; score: number }[];

export default function App() {
  const [baseUrl, setBaseUrl] = useState("http://localhost:5001");
  const api = useApi(baseUrl);

  // auth-less for now
  const [player, setPlayer] = useState("neomi");

  // views
  type View = "lobby" | "play" | "result" | "leaderboard" | "manage";
  const [view, setView] = useState<View>("lobby");

  // lobby state
  const [topics, setTopics] = useState<string[]>([]);
  const [topic, setTopic] = useState<string>("");
  const [quizzes, setQuizzes] = useState<QuizRow[]>([]);
  const [quizId, setQuizId] = useState<number | null>(null);

  // game
  const [sid, setSid] = useState<number | null>(null);
  const [current, setCurrent] = useState<CurrentQ | null>(null);
  const [score, setScore] = useState(0);
  const startMsRef = useRef<number>(0);

  // leaderboard
  const [board, setBoard] = useState<LeaderTop>([]);

  // manage (add question / create quiz)
  const [qTopic, setQTopic] = useState("");
  const [qDiff, setQDiff] = useState("");
  const [qText, setQText] = useState("");
  const [a1, setA1] = useState("");
  const [a2, setA2] = useState("");
  const [a3, setA3] = useState("");
  const [a4, setA4] = useState("");
  const [id, setId] = useState("");

  const [mTitle, setMTitle] = useState("");
  const [mTopic, setMTopic] = useState("");
  const [mDiff, setMDiff] = useState("");
  const [mCount, setMCount] = useState(5);

  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  // load topics initially
  useEffect(() => {
    (async () => {
      const res = await api.get<string[]>("/library/topics");
      if (res.ok) setTopics(res.data);
    })();
  }, [baseUrl]);

  async function loadQuizzes(t: string) {
    setTopic(t);
    setQuizId(null);
    const res = await api.get<QuizRow[]>(`/library/quizzes?topic=${encodeURIComponent(t)}`);
    if (res.ok) setQuizzes(res.data);
  }

  async function startQuiz() {
    if (!quizId) { setError("Choose quiz"); return; }
    setError(null);
    setInfo(null);
    const res = await api.post<{ session_id: number }>(`/library/session/create`, { player_name: player, quiz_id: quizId });
    if (!res.ok) { setError(res.error.message); return; }
    setSid(res.data.session_id);
    await loadCurrent(res.data.session_id);
    setScore(0);
    setView("play");
  }

  async function loadCurrent(sidX: number) {
    const res = await api.get<CurrentQ>(`/library/session/${sidX}/current`);
    if (!res.ok) { setError(res.error.message); return; }
    setCurrent(res.data);
    if (!res.data.finished) {
      startMsRef.current = performance.now(); // start timer
    } else {
      setView("result");
    }
  }

  async function submitAnswer(ans: string) {
    if (!sid) return;
    const elapsed = Math.floor(performance.now() - startMsRef.current);
    const res = await api.post<any>(`/library/session/${sid}/answer`, { answer: ans, client_ms: elapsed });
    if (!res.ok) { setError(res.error.message); return; }
    if (typeof res.data.score === "number") setScore(res.data.score);
    if (res.data.finished) {
      setView("result");
    } else if (res.data.next) {
      setCurrent(res.data.next);
      startMsRef.current = performance.now();
    } else {
      await loadCurrent(sid);
    }
  }

  async function loadLeaderboardForQuiz(qid: number) {
    const res = await api.get<{ top: LeaderTop }>(`/library/leaderboard?quiz_id=${qid}`);
    if (res.ok) setBoard(res.data.top);
  }

  // manage actions
  async function addQuestion() {
    setError(null);
    setInfo(null);
    const answers = [a1, a2, a3, a4];
    const res = await api.post<{ id: number }>(`/library/questions`, {
      question: qText, topic: qTopic, difficulty: qDiff, answers, quiz_id: id
    });
    if (!res.ok) { setError(res.error.message); return; }
    // refresh topics list
    const t = await api.get<string[]>("/library/topics");
    if (t.ok) setTopics(t.data);
    setQText(""); setA1(""); setA2(""); setA3(""); setA4("");
    setInfo("New question was created successfully");
  }

  async function createQuiz() {
    setError(null);
    setInfo(null);
    const res = await api.post<{ id: number }>(`/library/quizzes`, {
      title: mTitle, topic: mTopic, difficulty: mDiff, count: mCount
    });
    if (!res.ok) { setError(res.error.message); return; }
    if (topic === mTopic) await loadQuizzes(topic);
    setMTitle(""); setMTopic(""); setMDiff(""); setMCount(5);
    setInfo("New quiz was created successfully. Quiz ID is " + res.data.id.toString());
  }

  // UI bits
  const header = (
    <header style={{ textAlign: "center", padding: "16px 0" }}>
      <h1>Trivia Creator – Mini Quiz</h1>
      <p>Kahoot-style flow: Login → Start → Answer → Result → Leaderboard</p>
    </header>
  );

  return (
    <div style={{ padding: 12, fontFamily: "system-ui, Arial" }}>
      {/* base config */}
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <label>Base URL</label>
        <input value={baseUrl} onChange={e => setBaseUrl(e.target.value)} style={{ width: 260 }} />
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <button onClick={() => setView("lobby")}>Lobby</button>
          <button onClick={() => setView("manage")}>Manage</button>
          {view !== "lobby" && <button onClick={() => { setSid(null); setView("lobby"); }}>Logout</button>}
        </div>
      </div>

      {header}

      {error && (
        <div style={{ color: "#b00", marginBottom: 8 }}>Error: {error}</div>
      )}

      {info && (
        <div style={{ color: "rgba(0, 187, 34, 1)", marginBottom: 8 }}>Info: {info}</div>
      )}

      {/* Lobby */}
      {view === "lobby" && (
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          <h2>Start a Session</h2>
          <div>Player name</div>
          <input value={player} onChange={e=>setPlayer(e.target.value)} />
          <div style={{ marginTop: 8 }}>Topic</div>
          <select value={topic} onChange={e => loadQuizzes(e.target.value)}>
            <option value="">-- choose topic --</option>
            {topics.map(t => <option key={t} value={t}>{t}</option>)}
          </select>

          {topic && (
            <>
              <div style={{ marginTop: 8 }}>Quizzes in {topic}</div>
              <select value={quizId ?? ""} onChange={e => setQuizId(+e.target.value || null)}>
                <option value="">-- choose quiz --</option>
                {quizzes.map(q => (
                  <option key={q.id} value={q.id}>{q.title} ({q.count} Qs)</option>
                ))}
              </select>
            </>
          )}

          <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
            <button onClick={startQuiz}>Start</button>
            {quizId && (
              <button onClick={async () => { await loadLeaderboardForQuiz(quizId); setView("leaderboard"); }}>View Leaderboard</button>
            )}
          </div>
        </div>
      )}

      {/* Play */}
      {view === "play" && current && !current.finished && (
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          <h2>Question { (current.index ?? 0) + 1 } / {current.total}</h2>
          <div style={{ marginBottom: 8 }}>Score: {score}</div>
          <div style={{ margin: "12px 0", fontSize: 18 }}>{current.question}</div>
          <div style={{ display: "grid", gap: 8 }}>
            {current.options?.map((opt, i) => (
              <button key={i} onClick={() => submitAnswer(opt)}>{opt}</button>
            ))}
          </div>
        </div>
      )}

      {/* Result */}
      {view === "result" && (
        <div style={{ maxWidth: 800, margin: "0 auto" }}>
          <h2>Result</h2>
          <p>Final score: <b>{score}</b></p>
          {quizId && (
            <button onClick={async () => { await loadLeaderboardForQuiz(quizId); setView("leaderboard"); }}>
              Leaderboard
            </button>
          )}
          <button style={{ marginLeft: 8 }} onClick={() => setView("lobby")}>Back to Lobby</button>
        </div>
      )}

      {/* Leaderboard */}
      {view === "leaderboard" && (
        <div style={{ maxWidth: 600, margin: "0 auto" }}>
          <h2>Leaderboard (Top 10)</h2>
          {board.length === 0 ? (
            <div>No scores yet</div>
          ) : (
            <div style={{ display: "grid", gap: 6 }}>
              {board.map((r, i) => (
                <div key={i} style={{ display: "flex", justifyContent: "space-between", border: "1px solid #ddd", padding: "6px 10px" }}>
                  <div>{i + 1}. {r.player_name}</div>
                  <div>{r.score}</div>
                </div>
              ))}
            </div>
          )}
          <div style={{ marginTop: 12 }}>
            <button onClick={() => setView("lobby")}>Back</button>
          </div>
        </div>
      )}

      {/* Manage */}
      {view === "manage" && (
        <div style={{ maxWidth: 900, margin: "0 auto", display: "grid", gap: 24 }}>
          <section style={{ border: "1px solid #ddd", padding: 12 }}>
            <h3>Add Question (answers[0] is correct)</h3>
            <div>Topic</div>
            <input value={qTopic} onChange={e=>setQTopic(e.target.value)} />
            <div>Difficulty</div>
            <input value={qDiff} onChange={e=>setQDiff(e.target.value)} placeholder="easy / medium / hard" />
            <div>Question</div>
            <input value={qText} onChange={e=>setQText(e.target.value)} />
            <div>Answers (first is correct)</div>
            <input placeholder="correct" value={a1} onChange={e=>setA1(e.target.value)} />
            <input placeholder="wrong 1" value={a2} onChange={e=>setA2(e.target.value)} />
            <input placeholder="wrong 2" value={a3} onChange={e=>setA3(e.target.value)} />
            <input placeholder="wrong 3" value={a4} onChange={e=>setA4(e.target.value)} />
            <div>Quiz ID</div>
            <input value={id} onChange={e=>setId(e.target.value)} />
            <div style={{ marginTop: 8 }}>
              <button onClick={addQuestion}>Add Question</button>
            </div>
          </section>

          <section style={{ border: "1px solid #ddd", padding: 12 }}>
            <h3>Create Quiz (by topic)</h3>
            <div>Title</div>
            <input value={mTitle} onChange={e=>setMTitle(e.target.value)} />
            <div>Topic</div>
            <input value={mTopic} onChange={e=>setMTopic(e.target.value)} />
            <div>Difficulty (optional)</div>
            <input value={mDiff} onChange={e=>setMDiff(e.target.value)} placeholder="easy / medium / hard" />
            <div>Count (random questions from topic)</div>
            <input type="number" value={mCount} onChange={e=>setMCount(parseInt(e.target.value || "5", 10))} />
            <div style={{ marginTop: 8 }}>
              <button onClick={createQuiz}>Create</button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

