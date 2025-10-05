import React, { useState } from "react";
import { Container, Paper, Typography, TextField, Button, Box, Alert } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { useApi } from "@/hooks/useApi";

export default function AuthPage({ baseUrl }: { baseUrl: string }) {
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
              אין לך חשבון?{" "}
              <Button onClick={() => { setMode("signup"); setErr(null); setMsg(null); }} size="small">
                Signup
              </Button>
            </Typography>
          ) : (
            <Typography variant="body2">
              יש לך חשבון?{" "}
              <Button onClick={() => { setMode("login"); setErr(null); setMsg(null); }} size="small">
                Login
              </Button>
            </Typography>
          )}
        </Box>
      </Paper>
    </Container>
  );
}
