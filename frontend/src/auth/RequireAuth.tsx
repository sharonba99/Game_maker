import React, { type ReactNode } from "react";
import { Navigate } from "react-router-dom";

export default function RequireAuth({ children }: { children: ReactNode }) {
  const hasUser = !!JSON.parse(localStorage.getItem("auth") || "null")?.username;
  if (!hasUser) return <Navigate to="/login" replace />;
  return <>{children}</>;
}
