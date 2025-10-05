import React from "react";
import { AppBar, Toolbar, IconButton, Typography, Button, TextField, Box, Tooltip } from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import LogoutIcon from "@mui/icons-material/Logout";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import { Link as RouterLink, useNavigate } from "react-router-dom";

export default function Navbar({
  onLogout, baseUrl, setBaseUrl,
}: { onLogout: () => void; baseUrl: string; setBaseUrl: (v: string) => void }) {
  const auth = JSON.parse(localStorage.getItem("auth") || "null");
  const nav = useNavigate();

  return (
    <AppBar position="sticky" color="primary" enableColorOnDark>
      <Toolbar>
        <Tooltip title="Back">
          <IconButton edge="start" color="inherit" sx={{ mr: 1 }} onClick={() => nav(-1)}>
            <ArrowBackIcon />
          </IconButton>
        </Tooltip>
        <IconButton edge="start" color="inherit" sx={{ mr: 1 }}>
          <MenuIcon />
        </IconButton>
        <Typography variant="h6" sx={{ mr: 2 }}>Trivia Creator</Typography>
        <Button component={RouterLink} to="/play" color="inherit">Play</Button>
        <Button component={RouterLink} to="/createquiz" color="inherit">Create</Button>
        <Box sx={{ flex: 1 }} />
        <TextField
          size="small"
          value={baseUrl}
          onChange={(e) => setBaseUrl(e.target.value)}
          label="Base URL"
          sx={{ mr: 2, minWidth: 280, display: { xs: "none", md: "inline-flex" } }}
        />
        {auth?.username ? (
          <Tooltip title={`Logged in as ${auth.username}`}>
            <Button color="inherit" onClick={onLogout} startIcon={<LogoutIcon />}>Logout</Button>
          </Tooltip>
        ) : (
          <Button component={RouterLink} to="/login" color="inherit">Login / Signup</Button>
        )}
      </Toolbar>
    </AppBar>
  );
}
