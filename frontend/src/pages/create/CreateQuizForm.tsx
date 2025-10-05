import React, { useState } from "react";
import { Container, Paper, TextField, Stack, Button, Alert, Typography } from "@mui/material";
import { useNavigate } from "react-router-dom";
import Crumbs from "../../components/Crumbs";
import { useApi } from "../../hooks/useApi";

export default function CreateQuizForm({ baseUrl }: { baseUrl: string }) {
  const api = useApi(baseUrl);
  const [title, setTitle] = useState("");
  const [topic, setTopic] = useState("");
  const [diff, setDiff] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const nav = useNavigate();

  async function create() {
    setErr(null); setMsg(null);
    const res = await api.post<{ id: number }>("/library/quizzes", { title, topic, difficulty: diff });
    if (!res.ok) { setErr(res.error.message); return; }
    setMsg("Quiz created: id " + res.data.id);
  }

  return (
    <Container maxWidth="sm" sx={{ py: 3 }}>
      <Crumbs items={[{ label: "Create", to: "/createquiz" }, { label: "Create Quiz" }]} />
      <Typography variant="h4" gutterBottom>New Quiz</Typography>
      {err && <Alert severity="error" sx={{ mb: 2 }}>{err}</Alert>}
      {msg && <Alert severity="success" sx={{ mb: 2 }}>{msg}</Alert>}

      <Paper sx={{ p: 2, borderRadius: 3 }}>
        <TextField fullWidth label="Title" value={title} onChange={(e) => setTitle(e.target.value)} sx={{ mb: 2 }} />
        <TextField fullWidth label="Topic" value={topic} onChange={(e) => setTopic(e.target.value)} sx={{ mb: 2 }} />
        <TextField fullWidth label="Difficulty (easy/medium/hard)" value={diff} onChange={(e) => setDiff(e.target.value)} sx={{ mb: 2 }} />
        <Stack direction="row" spacing={1}>
          <Button variant="contained" onClick={create}>Create quiz</Button>
          <Button variant="text" onClick={() => nav(-1)}>Back</Button>
          <Button variant="outlined" onClick={() => nav("/createquiz/add")}>Go to Add Questions</Button>
        </Stack>
      </Paper>
    </Container>
  );
}
