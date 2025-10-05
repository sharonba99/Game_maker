import React from "react";
import { Container, Paper, Stack, Button, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import Crumbs from "../../components/Crumbs";

export default function CreateHome() {
  return (
    <Container maxWidth="sm" sx={{ py: 3 }}>
      <Crumbs items={[{ label: "Create" }]} />
      <Typography variant="h4" gutterBottom>Create Center</Typography>
      <Paper sx={{ p: 3, borderRadius: 3 }}>
        <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
          <Button fullWidth component={RouterLink} to="/createquiz/new" variant="contained">Create Quiz</Button>
          <Button fullWidth component={RouterLink} to="/createquiz/add" variant="outlined">Add Questions</Button>
        </Stack>
      </Paper>
    </Container>
  );
}
