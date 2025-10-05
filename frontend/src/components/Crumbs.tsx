import React from "react";
import { Breadcrumbs, Link, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

export type Crumb = { label: string; to?: string };

export default function Crumbs({ items }: { items: Crumb[] }) {
  return (
    <Breadcrumbs sx={{ mb: 2 }}>
      {items.map((it, i) =>
        it.to ? (
          <Link key={i} component={RouterLink} color="inherit" to={it.to} underline="hover">
            {it.label}
          </Link>
        ) : (
          <Typography key={i} color="text.primary">{it.label}</Typography>
        )
      )}
    </Breadcrumbs>
  );
}
