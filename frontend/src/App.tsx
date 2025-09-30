import React, { useEffect, useRef, useState, type ReactNode } from "react";
import { Routes, Route, Navigate, Link as RouterLink, useNavigate } from "react-router-dom";
import {
  CssBaseline,
  ThemeProvider,
  createTheme,
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Container,
  Box,
  Paper,
  Button,
  TextField,
  Alert,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Chip,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Tooltip,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import LogoutIcon from "@mui/icons-material/Logout";

/** =====================================================
 *  Game_maker – App.tsx (MUI integrated, drop-in)
 *  - Keeps your existing logic, routes and API calls
 *  - Swaps inline styles to Material-UI components
 *  - Place this file as frontend/src/App.tsx
 *  - Ensure deps installed: @mui/material @emotion/react @emotion/styled @mui/icons-material
 * ===================================================== */

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
    <Container maxWidth="xs" sx={{ py: 6 }}>
      <Paper elevation={3} sx={{ p: 3, borderRadius: 3 }}>
        <Typography variant="h5" gutterBottom>
          {mode === "login" ? "Login" : "Signup"}
        </Typography>

        {err && <Alert severity="error" sx={{ mb: 2 }}>Error: {err}</Alert>}
        {msg && <Alert severity="success" sx={{ mb: 2 }}>{msg}</Alert>}

        <TextField
          fullWidth
          label="Username"
          value={username}
          onChange={(e) => setU(e.target.value)}
          sx={{ mb: 2 }}
        />
        <TextField
          fullWidth
          type="password"
          label="Password"
          value={password}
          onChange={(e) => setP(e.target.value)}
        />

        <Box sx={{ mt: 2, display: "flex", gap: 1 }}>
          {mode === "login" ? (
            <Button fullWidth variant="contained" onClick={doLogin}>Login</Button>
          ) : (
            <Button fullWidth variant="contained" onClick={doSignup}>Create account</Button>
          )}
        </Box>

        <Box sx={{ mt: 2 }}>
          {mode === "login" ? (
            <Typography variant="body2">
              אין לך חשבון? {" "}
              <Button onClick={() => { setMode("signup"); setErr(null); setMsg(null); }} size="small">Signup</Button>
            </Typography>
          ) : (
            <Typography variant="body2">
              כבר רשומה? {" "}
              <Button onClick={() => { setMode("login"); setErr(null); setMsg(null); }} size="small">Login</Button>
            </Typography>
          )}
        </Box>
      </Paper>
    </Container>
  );
}

/** ---------- navbar ---------- */
function Navbar({ onLogout, baseUrl, setBaseUrl }: { onLogout: () => void; baseUrl: string; setBaseUrl: (v: string) => void; }) {
  const auth = JSON.parse(localStorage.getItem("auth") || "null");
  return (
    <AppBar position="sticky" color="primary" enableColorOnDark>
      <Toolbar>
        <IconButton edge="start" color="inherit" sx={{ mr: 1 }}>
          <MenuIcon />
        </IconButton>
        <Typography variant="h6" sx={{ mr: 2 }}>
          Game_maker
        </Typography>
        <Button component={RouterLink} to="/play" color="inherit">Play</Button>
        <Button component={RouterLink} to="/createquiz" color="inherit">Create Quiz</Button>
        <Box sx={{ flex: 1 }} />
        {/* Base URL input */}
        <TextField
          size="small"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          label="Base URL"
          sx={{ mr: 2, minWidth: 280, display: { xs: "none", md: "inline-flex" } }}
        />
        {auth?.username ? (
          <Tooltip title={`Logged in as ${auth.username}`}>
            <Button color="inherit" onClick={onLogout} startIcon={<LogoutIcon />}>
              Logout
            </Button>
          </Tooltip>
        ) : (
          <Button component={RouterLink} to="/login" color="inherit">Login / Signup</Button>
        )}
      </Toolbar>
    </AppBar>
  );
}

/** ---------- types for leaderboard ---------- */
type LeaderRow = { player_name: string; score: number };

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
  const [board, setBoard] = useState<LeaderRow[]>([]);
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
      const r = await api.get<{ top: LeaderRow[] }>(`/library/leaderboard?quiz_id=${qid}`);
      if (r.ok) setBoard(r.data.top);
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <Container maxWidth="md" sx={{ py: 3 }}>
      <Typography variant="h4" gutterBottom>Play</Typography>
      <Typography variant="body2" sx={{ mb: 2 }}>Playing as: <b>{playerName}</b></Typography>
      {err && <Alert severity="error" sx={{ mb: 2 }}>{err}</Alert>}

      <Paper sx={{ p: 2, borderRadius: 3 }}>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Topic</InputLabel>
          <Select label="Topic" value={topic} onChange={(e) => loadQuizzes(String(e.target.value))}>
            <MenuItem value=""><em>choose topic</em></MenuItem>
            {topics.map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
          </Select>
        </FormControl>

        {topic && (
          <>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Quiz</InputLabel>
              <Select label="Quiz" value={quizId ?? ""} onChange={(e) => setQuizId(Number(e.target.value) || null)}>
                <MenuItem value=""><em>choose quiz</em></MenuItem>
                {quizzes.map((q) => (
                  <MenuItem key={q.id} value={q.id}>{q.title} ({q.count} Qs)</MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button variant="contained" onClick={start}>Start</Button>
          </>
        )}
      </Paper>

      {current && !current.finished && (
        <Paper sx={{ p: 2, borderRadius: 3, mt: 2 }}>
          <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <Chip label={`Score: ${score}`} color="primary" />
            <Chip label={`Q ${(current.index ?? 0) + 1} / ${current.total}`} />
          </Box>
          <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>{current.question}</Typography>
          <Box sx={{ display: "grid", gap: 1 }}>
            {current.options?.map((o: string, i: number) => (
              <Button key={i} variant="outlined" onClick={() => answer(o)} disabled={answering}>
                {answering ? "…" : o}
              </Button>
            ))}
          </Box>
        </Paper>
      )}

      {current?.finished && (
        <Paper sx={{ p: 2, borderRadius: 3, mt: 2 }}>
          <Typography variant="h5" gutterBottom>Finished!</Typography>
          <Chip label={`Final score: ${score}`} color="success" sx={{ mb: 2 }} />

          <Typography variant="h6" sx={{ mb: 1 }}>Top 10</Typography>
          {board.length === 0 ? (
            <Typography variant="body2">No scores yet</Typography>
          ) : (
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>Player</TableCell>
                  <TableCell align="right">Score</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {board.map((r, i) => (
                  <TableRow key={i} hover>
                    <TableCell>{i + 1}</TableCell>
                    <TableCell>{r.player_name}</TableCell>
                    <TableCell align="right">{r.score}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Paper>
      )}
    </Container>
  );
}

/** ---------- create quiz page ---------- */
function CreateQuiz({ baseUrl }: { baseUrl: string }) {
  const api = useApi(baseUrl);
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [diff, setDiff] = useState("");
  const [quizId, setQuizId] = useState<number | null>(null);

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
    <Container maxWidth="sm" sx={{ py: 3 }}>
      <Typography variant="h4" gutterBottom>Create Quiz & Questions</Typography>
      {err && <Alert severity="error" sx={{ mb: 2 }}>{err}</Alert>}
      {msg && <Alert severity="success" sx={{ mb: 2 }}>{msg}</Alert>}

      <Paper sx={{ p: 2, borderRadius: 3 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>New Quiz</Typography>
        <TextField fullWidth label="Title" value={title} onChange={(e) => setTitle(e.target.value)} sx={{ mb: 2 }} />
        <TextField fullWidth label="Topic" value={topic} onChange={(e) => setTopic(e.target.value)} sx={{ mb: 2 }} />
        <TextField fullWidth label="Difficulty (easy/medium/hard)" value={diff} onChange={(e) => setDiff(e.target.value)} sx={{ mb: 2 }} />
        <Button variant="contained" onClick={create}>Create quiz</Button>

        <Divider sx={{ my: 3 }} />

        <Typography variant="h6" sx={{ mb: 1 }}>Add Question (answers[0] is correct)</Typography>
        <TextField fullWidth label="Question" value={q} onChange={(e) => setQ(e.target.value)} sx={{ mb: 2 }} />
        <TextField fullWidth label="Correct answer" value={a1} onChange={(e) => setA1(e.target.value)} sx={{ mb: 1 }} />
        <TextField fullWidth label="Wrong 1" value={a2} onChange={(e) => setA2(e.target.value)} sx={{ mb: 1 }} />
        <TextField fullWidth label="Wrong 2" value={a3} onChange={(e) => setA3(e.target.value)} sx={{ mb: 1 }} />
        <TextField fullWidth label="Wrong 3" value={a4} onChange={(e) => setA4(e.target.value)} sx={{ mb: 2 }} />
        <Button variant="outlined" onClick={addQuestion}>Add question</Button>
      </Paper>
    </Container>
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

  // theme (light only for now; you can add toggle if you want)
  const theme = createTheme({
    shape: { borderRadius: 12 },
    palette: { mode: "light" },
  });

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Navbar onLogout={logout} baseUrl={baseUrl} setBaseUrl={setBaseUrl} />
      <Box component="main" sx={{ minHeight: "calc(100dvh - 64px)" }}>
        <Routes>
          <Route path="/login" element={<AuthPage baseUrl={baseUrl} />} />
          <Route path="/play" element={<RequireAuth><Play baseUrl={baseUrl} /></RequireAuth>} />
          <Route path="/createquiz" element={<RequireAuth><CreateQuiz baseUrl={baseUrl} /></RequireAuth>} />
          <Route path="*" element={<Navigate to="/play" replace />} />
        </Routes>
      </Box>
    </ThemeProvider>
  );
}
