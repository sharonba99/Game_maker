import React, { useEffect, useRef, useState } from "react";
import { Container, Paper, Stack, Chip, Alert, Typography, Box, Button } from "@mui/material";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import Crumbs from "../../components/Crumbs";
import { useApi } from "../../hooks/useApi";
import { TIME_LIMIT_SEC, msToSec } from "../../utils/time";


export default function GameScreen({ baseUrl }: { baseUrl: string }) {
  const api = useApi(baseUrl);
  const { sid } = useParams();
  const location = useLocation();
  const nav = useNavigate();
  const search = new URLSearchParams(location.search);
  const quizId = Number(search.get("quizId"));

  const [score, setScore] = useState(0);
  const [current, setCurrent] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);
  const [answering, setAnswering] = useState(false);
  const [totalMs, setTotalMs] = useState(0);

  const startMsRef = useRef(0);
  const prevScoreRef = useRef(0);
  const answeringRef = useRef(false);
  const deadlineRef = useRef<number | null>(null);
  const tickerRef = useRef<number | null>(null);

  const playerName = JSON.parse(localStorage.getItem("auth") || "null")?.username || "guest";

  function beginQuestion(q: any) {
    setCurrent(q);
    startMsRef.current = performance.now();
    deadlineRef.current = startMsRef.current + TIME_LIMIT_SEC * 1000;
    setSecondsLeft(TIME_LIMIT_SEC);
  }

  useEffect(() => {
    if (!sid) return;
    setScore(0);
    setTotalMs(0);
    prevScoreRef.current = 0;
    answeringRef.current = false;
    deadlineRef.current = null;
    setSecondsLeft(null);
    loadCurrent(Number(sid));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sid]);

  async function loadCurrent(sidX: number) {
    try {
      const res = await api.get<any>(`/library/session/${sidX}/current`);
      if (!res.ok) { setErr(res.error.message); return; }
      if (res.data.finished) {
        setCurrent({ finished: true });
        deadlineRef.current = null;
        setSecondsLeft(null);
      } else {
        beginQuestion(res.data);
      }
    } catch (e: any) {
      setErr("Network error loading question");
      console.error(e);
    }
  }

  useEffect(() => {
    if (tickerRef.current !== null) return;
    const id = window.setInterval(() => {
      if (!deadlineRef.current) { setSecondsLeft(null); return; }
      const now = performance.now();
      const leftMs = Math.max(0, deadlineRef.current - now);
      setSecondsLeft(Math.ceil(leftMs / 1000));
      if (leftMs <= 0 && !answeringRef.current) {
        answer("", -1);
      }
    }, 100);
    tickerRef.current = id;
    return () => { if (tickerRef.current !== null) { window.clearInterval(tickerRef.current); tickerRef.current = null; } };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function answer(opt: string, idx?: number) {
    if (!sid) return;
    if (answeringRef.current) return;
    answeringRef.current = true;
    setAnswering(true);
    setErr(null);

    try {
      const ms = Math.floor(performance.now() - startMsRef.current);
      setTotalMs((prev) => prev + ms);
      deadlineRef.current = null;
      setSecondsLeft(null);

      const before = prevScoreRef.current;
      const normalized = (opt ?? "").trim().replace(/\s+/g, " ");
      const payload: any = { answer: normalized, client_ms: ms };
      if (typeof idx === "number") { payload.answer_index = idx; payload.answer_key = idx; }

      const res = await api.post<any>(`/library/session/${sid}/answer`, payload);
      if (!res.ok) { setErr(res.error.message); return; }

      const nextScore = (typeof res.data.score === "number") ? res.data.score : before;
      setScore(nextScore);
      prevScoreRef.current = nextScore;

      if (res.data.finished) { setCurrent({ finished: true }); return; }
      if (res.data.next) { beginQuestion(res.data.next); return; }
      await loadCurrent(Number(sid));
    } catch (e: any) {
      setErr("Network error submitting answer");
      console.error(e);
    } finally {
      setAnswering(false);
      answeringRef.current = false;
    }
  }

  return (
    <Container maxWidth="md" sx={{ py: 3 }}>
      <Crumbs items={[{ label: "Play", to: "/play" }, { label: "Game" }]} />
      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Chip label={`Player: ${playerName}`} />
          <Stack direction="row" spacing={1}>
            <Chip label={`Score: ${score}`} color="primary" />
            {deadlineRef.current && (<Chip label={`⏳ ${secondsLeft ?? TIME_LIMIT_SEC}s`} />)}
            {current && !current.finished && (<Chip label={`Q ${(current.index ?? 0) + 1} / ${current.total}`} />)}
          </Stack>
        </Stack>

        {err && <Alert severity="error" sx={{ my: 2 }}>{err}</Alert>}

        {!current && <Typography sx={{ mt: 2 }}>Loading…</Typography>}

        {current && !current.finished && (
          <>
            <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>{current.question}</Typography>
            <Box sx={{ display: "grid", gap: 1 }}>
              {current.options?.map((o: string, i: number) => (
                <Button key={i} variant="outlined" onClick={() => answer(o, i)} disabled={answering}>
                  {answering ? "…" : o}
                </Button>
              ))}
            </Box>
          </>
        )}

        {current?.finished && (
          <Stack spacing={2} sx={{ mt: 3 }}>
            <Typography variant="h5">Finished!</Typography>
            <Stack direction="row" spacing={1}>
              <Chip label={`Final score: ${score}`} color="success" />
              <Chip label={`Total time: ${msToSec(totalMs)}s`} color="secondary" />
            </Stack>
            <Stack direction="row" spacing={1}>
              <Button variant="contained" onClick={() => nav(`/play/leaderboard/${quizId}`)}>View Leaderboard</Button>
              <Button variant="outlined" onClick={() => nav("/play")}>Back to Picker</Button>
            </Stack>
          </Stack>
        )}
      </Paper>
    </Container>
  );
}
