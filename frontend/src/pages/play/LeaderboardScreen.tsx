import React, { useEffect, useState } from "react";
import {
  Container, Paper, Typography, Table, TableHead, TableRow, TableCell, TableBody
} from "@mui/material";
import { useParams } from "react-router-dom";
import Crumbs from "@/components/Crumbs";
import { useApi } from "@/hooks/useApi";
import { LeaderRow } from "@/types";
import { msToSec } from "@/utils/time";

export default function LeaderboardScreen({ baseUrl }: { baseUrl: string }) {
  const api = useApi(baseUrl);
  const { quizId } = useParams();
  const [board, setBoard] = useState<LeaderRow[]>([]);

  useEffect(() => {
    let ignore = false;
    (async () => {
      if (!quizId) return;
      const r = await api.get<{ top: LeaderRow[] }>(`/library/leaderboard?quiz_id=${quizId}`);
      if (r.ok && !ignore) setBoard(r.data.top ?? []);
    })();
    return () => { ignore = true; };
  }, [quizId]);

  return (
    <Container maxWidth="md" sx={{ py: 3 }}>
      <Crumbs items={[{ label: "Play", to: "/play" }, { label: "Leaderboard" }]} />
      <Typography variant="h4" gutterBottom>Top 10</Typography>
      <Paper sx={{ p: 2, borderRadius: 3 }}>
        {board.length === 0 ? (
          <Typography variant="body2">No scores yet</Typography>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Player</TableCell>
                <TableCell align="right">Score</TableCell>
                <TableCell align="right">Time (s)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {board.map((r, i) => (
                <TableRow key={i} hover>
                  <TableCell>{i + 1}</TableCell>
                  <TableCell>{r.player_name}</TableCell>
                  <TableCell align="right">{r.score}</TableCell>
                  <TableCell align="right">{msToSec(r.duration_ms || 0)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>
    </Container>
  );
}
