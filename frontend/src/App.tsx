// frontend/src/App.tsx
import React, { useEffect, useState } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { CssBaseline, ThemeProvider, createTheme, Box } from "@mui/material";

import Navbar from "@/components/Navbar";
import RequireAuth from "@/auth/RequireAuth";
import AuthPage from "@/pages/AuthPageInline";

// Pages
import PlayPicker from "@/pages/play/PlayPicker";
import GameScreen from "@/pages/play/GameScreen";
import LeaderboardScreen from "@/pages/play/LeaderboardScreen";
import CreateHome from "@/pages/create/CreateHome";
import CreateQuizForm from "@/pages/create/CreateQuizForm";
import AddQuestionForm from "@/pages/create/AddQuestionForm";

function getInitialBaseUrl(): string {
  const fromLocal = window.localStorage.getItem("baseUrl");
  if (fromLocal && fromLocal.trim()) return fromLocal.trim();
  const fromEnv = (import.meta as any).env?.VITE_API_BASE_URL as string | undefined;
  if (fromEnv && fromEnv.trim()) return fromEnv.trim();
  return "/api";
}

export default function App() {
  const [baseUrl, setBaseUrl] = useState<string>(getInitialBaseUrl());
  const nav = useNavigate();

  useEffect(() => {
    // שמירה אוטומטית של הערך לטובת רענון/פתיחה מחדש
    try {
      window.localStorage.setItem("baseUrl", baseUrl || "");
    } catch {}
  }, [baseUrl]);

  function logout() {
    localStorage.removeItem("auth");
    nav("/login");
  }

  const theme = createTheme({ shape: { borderRadius: 12 }, palette: { mode: "light" } });

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Navbar onLogout={logout} baseUrl={baseUrl} setBaseUrl={setBaseUrl} />
      <Box component="main" sx={{ minHeight: "calc(100dvh - 64px)" }}>
        <Routes>
          {/* Auth */}
          <Route path="/login" element={<AuthPage baseUrl={baseUrl} />} />

          {/* Play flow */}
          <Route path="/play" element={<RequireAuth><PlayPicker baseUrl={baseUrl} /></RequireAuth>} />
          <Route path="/play/game/:sid" element={<RequireAuth><GameScreen baseUrl={baseUrl} /></RequireAuth>} />
          <Route path="/play/leaderboard/:quizId" element={<RequireAuth><LeaderboardScreen baseUrl={baseUrl} /></RequireAuth>} />

          {/* Create flow */}
          <Route path="/createquiz" element={<RequireAuth><CreateHome /></RequireAuth>} />
          <Route path="/createquiz/new" element={<RequireAuth><CreateQuizForm baseUrl={baseUrl} /></RequireAuth>} />
          <Route path="/createquiz/add" element={<RequireAuth><AddQuestionForm baseUrl={baseUrl} /></RequireAuth>} />

          {/* Default */}
          <Route path="*" element={<Navigate to="/play" replace />} />
        </Routes>
      </Box>
    </ThemeProvider>
  );
}
