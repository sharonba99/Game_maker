import React, { useEffect, useState } from "react";
import { Container, Paper, FormControl, InputLabel, Select, MenuItem, TextField, Stack, Button, Alert, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import Crumbs from "../../components/Crumbs";
import { useApi } from "../../hooks/useApi";

export default function AddQuestionForm({ baseUrl }: { baseUrl: string }) {
  const api = useApi(baseUrl);
  const [quizzes, setQuizzes] = useState<{ id: number; title: string }[]>([]);
  const [quizId, setQuizId] = useState<number | "">("");
  const [diff, setDiff] = useState("");
  const [q, setQ] = useState("");
  const [a1, setA1] = useState("");
  const [a2, setA2] = useState("");
  const [a3, setA3] = useState("");
  const [a4, setA4] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const nav = useNavigate();

  useEffect(() => {
    (async () => {
      const res = await api.get<any>("/library/quizzes");
      if (res.ok) setQuizzes(res.data);
    })();
  }, []);

  async function addQuestion() {
    if (!quizId) { setErr("Select quiz first"); return; }
    setErr(null); setMsg(null);
    const res = await api.post<{ id: number }>("/library/questions", {
      quiz_id: quizId,
      question: q,
      difficulty: diff,
      answers: [a1, a2, a3, a4], // answers[0] is correct
    });
    if (!res.ok) { setErr(res.error.message); return; }
    setMsg("Question added: id " + res.data.id);
    setQ(""); setA1(""); setA2(""); setA3(""); setA4("");
  }

  return (
    <Container maxWidth="sm" sx={{ py: 3 }}>
      <Crumbs items={[{ label: "Create", to: "/createquiz" }, { label: "Add Questions" }]} />
      <Typography variant="h4" gutterBottom>Add Question</Typography>
      {err && <Alert severity="error" sx={{ mb: 2 }}>{err}</Alert>}
      {msg && <Alert severity="success" sx={{ mb: 2 }}>{msg}</Alert>}

      <Paper sx={{ p: 2, borderRadius: 3 }}>
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Quiz</InputLabel>
          <Select value={quizId} label="Quiz" onChange={(e) => setQuizId(Number(e.target.value))}>
            <MenuItem value=""><em>Choose quiz</em></MenuItem>
            {quizzes.map((q) => (
              <MenuItem key={q.id} value={q.id}>{q.title} (id {q.id})</MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField fullWidth label="Difficulty (easy/medium/hard)" value={diff} onChange={(e) => setDiff(e.target.value)} sx={{ mb: 2 }} />
        <TextField fullWidth label="Question" value={q} onChange={(e) => setQ(e.target.value)} sx={{ mb: 2 }} />
        <TextField fullWidth label="Correct answer" value={a1} onChange={(e) => setA1(e.target.value)} sx={{ mb: 1 }} />
        <TextField fullWidth label="Wrong 1" value={a2} onChange={(e) => setA2(e.target.value)} sx={{ mb: 1 }} />
        <TextField fullWidth label="Wrong 2" value={a3} onChange={(e) => setA3(e.target.value)} sx={{ mb: 1 }} />
        <TextField fullWidth label="Wrong 3" value={a4} onChange={(e) => setA4(e.target.value)} sx={{ mb: 2 }} />

        <Stack direction="row" spacing={1}>
          <Button variant="outlined" onClick={addQuestion}>Add question</Button>
          <Button variant="text" onClick={() => nav(-1)}>Back</Button>
          <Button variant="text" onClick={() => nav("/createquiz/new")}>Go to Create Quiz</Button>
        </Stack>
      </Paper>
    </Container>
  );
}
