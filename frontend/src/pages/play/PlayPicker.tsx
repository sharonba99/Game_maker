import React, { useEffect, useState } from "react";
import { Container, Paper, FormControl, InputLabel, Select, MenuItem, Button, Alert, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import Crumbs from "../../components/Crumbs";
import { useApi } from "../../hooks/useApi";

export default function PlayPicker({ baseUrl }: { baseUrl: string }) {
  const api = useApi(baseUrl);
  const [topics, setTopics] = useState<string[]>([]);
  const [topic, setTopic] = useState("");
  const [quizzes, setQuizzes] = useState<{ id: number; title: string; count: number }[]>([]);
  const [quizId, setQuizId] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const nav = useNavigate();
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
    const res = await api.get<any>(`/library/quizzes?topic=${encodeURIComponent(t)}`);
    if (res.ok) setQuizzes(res.data);
  }

  async function start() {
    if (!quizId) return;
    setErr(null);
    const res = await api.post<{ session_id: number }>(`/library/session/create`, {
      quiz_id: quizId, player_name: playerName,
    });
    if (!res.ok) { setErr(res.error.message); return; }
    nav(`/play/game/${res.data.session_id}?quizId=${quizId}`);
  }

  return (
    <Container maxWidth="md" sx={{ py: 3 }}>
      <Crumbs items={[{ label: "Play" }]} />
      <Typography variant="h4" gutterBottom>Pick a Quiz</Typography>
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
    </Container>
  );
}
