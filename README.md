Trivia Creator 🎮

A full-stack trivia game built with Flask (backend) and React (Vite) (frontend).
Players can sign up, create quizzes, play timed sessions, and compete on the leaderboard.

Users: signup/login (hashed passwords)

Quizzes: list by topic, create, add questions, bulk import

Game sessions: per-question timing (client sends client_ms); total time used as a tiebreaker

Leaderboard: top scores per quiz (score ↓, then total duration ↑)

CORS-ready (Vite/CRA)

DB: SQLite for dev / Postgres via DATABASE_URL

Tech Stack

Backend: Python, Flask, Flask-CORS, SQLAlchemy, Flask-Migrate, python-dotenv

Frontend: React (Vite), Material UI

Database: SQLite (local) / Postgres (DATABASE_URL)

Other: Alembic migrations, dotenv for config

Project Structure
├─ backend/
│  ├─ app.py                      # Flask app factory: blueprints, CORS, DB, Migrate
│  ├─ models.py                   # SQLAlchemy models: User, Quiz, TriviaQuestion, QuizSession, QuizAnswerLog, LeaderboardEntry
│  ├─ routes/
│  │  ├─ __init__.py              # (optional) routes aggregator
│  │  ├─ users.py                 # /users: signup, login, (optional) list
│  │  └─ library.py               # /library: topics, quizzes CRUD-lite, import, sessions, leaderboard
│  ├─ utils/
│  │  ├─ db.py                    # Shared SQLAlchemy() instance & init helpers
│  │  └─ helpers.py               # JSON helpers (j_ok/j_err), normalization, etc.
│  ├─ data/
│  │  └─ seed_quizzes.json        # Example quizzes (safe to commit)
│  ├─ tools/
│  │  └─ seed_json.py             # Seeder: POSTs seed_quizzes.json to the API
│  ├─ migrations/                 # Alembic (Flask-Migrate)
│  └─ instance/
│     └─ .gitkeep                 # Local SQLite (users.db) lives here (not committed)
│
├─ frontend/
│  ├─ src/
│  │  ├─ App.tsx                  # App root, routes, theme; reads API base from env/LocalStorage
│  │  ├─ auth/
│  │  │  └─ RequireAuth.tsx       # Guard: redirects to /login if not authenticated
│  │  ├─ components/
│  │  │  ├─ Navbar.tsx            # Top bar with Base URL input, nav links, logout
│  │  │  └─ Crumbs.tsx            # Breadcrumbs helper
│  │  ├─ hooks/
│  │  │  └─ useApi.ts             # Tiny fetch wrapper (get/post → {ok,data|error})
│  │  ├─ utils/
│  │  │  └─ time.ts               # TIME_LIMIT_SEC, msToSec, etc.
│  │  ├─ types/
│  │  │  └─ index.ts              # Shared types (e.g., LeaderRow)
│  │  └─ pages/
│  │     ├─ AuthPageInline.tsx    # Login/Signup screen (toggle)
│  │     ├─ play/
│  │     │  ├─ PlayPicker.tsx     # Topic + Quiz picker, starts session
│  │     │  ├─ GameScreen.tsx     # Full-screen game; stable per-question timer; submits answers
│  │     │  └─ LeaderboardScreen.tsx  # Top scores table (score + duration)
│  │     └─ create/
│  │        ├─ CreateHome.tsx     # Two buttons: Create Quiz / Add Questions
│  │        ├─ CreateQuizForm.tsx # Create quiz (title/topic/…)
│  │        └─ AddQuestionForm.tsx# Add question to an existing quiz
│  ├─ public/
│  │  └─ screenshots/             # Actual screenshots used in README
│  ├─ package.json
│  └─ vite.config.ts
│
├─ .env                           # Local env (not committed) — includes VITE_API_BASE_URL, Flask vars
├─ .env.example                   # Safe template for teammates
├─ requirements.txt               # Backend deps
├─ README.md
└─ .gitignore                     # Single repo-wide ignore (frontend + backend)

Environment Variables

Create a root .env (alongside backend/ and frontend/). Example:

# Flask
FLASK_APP=app:create_app
FLASK_DEBUG=1
FLASK_SECRET_KEY=dev-secret-change-me

# CORS (Vite/CRA)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Server
PORT=5001

# Database (default SQLite at backend/instance/users.db)
# DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/game_maker

# Frontend → Backend base URL (Vite reads this from the repo root)
VITE_API_BASE_URL=http://localhost:5001


Commit .env.example (no secrets), and add .env to .gitignore.
After changing .env, restart the Vite dev server.

Backend — Setup & Run

Run these from backend/:

# Create & activate venv
# Windows (PowerShell):
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux:
# python3 -m venv .venv
# source .venv/bin/activate

# Install dependencies (requirements.txt is at repo root)
# Windows:
pip install -r ..\requirements.txt
# macOS/Linux:
# pip install -r ../requirements.txt

# Initialize/upgrade DB (Alembic)
# Windows PowerShell:
$env:FLASK_APP="app:create_app"
flask db upgrade

# macOS/Linux:
# export FLASK_APP=app:create_app
# flask db upgrade

# Run dev server (http://localhost:5001)
python app.py


Health check: GET / → {"ok": true, "db": "<engine url>"}

Reset dev DB (danger: deletes local SQLite only):

# Windows:
Remove-Item -Force .\instance\users.db
flask db upgrade

# macOS/Linux:
# rm -f instance/users.db
# flask db upgrade

(Optional) Seed example data

Open another terminal while the backend is running:

# Windows PowerShell:
cd backend
.\.venv\Scripts\Activate.ps1
python tools/seed_json.py

# macOS/Linux:
# cd backend
# source .venv/bin/activate
# python tools/seed_json.py

Frontend — Setup & Run

Run these from frontend/:

npm install
npm run dev
# Runs on: http://localhost:5173


The app reads the backend URL from the root .env via VITE_API_BASE_URL.

You can override it at runtime in the navbar’s Base URL field (localStorage).

After changing .env, restart npm run dev.

API (Quick Reference)
Users (/users)

POST /users/signup → { username, password } → returns { id, username }

POST /users/login → { username, password } → returns { user_id, username }

GET /users/ → list users (optional)

Library & Game (/library)

GET /library/topics

GET /library/quizzes?topic=<topic>

GET /library/quizzes/<quiz_id>

POST /library/quizzes → create quiz
body: { title, topic, difficulty? }

POST /library/questions → add question
body: { quiz_id, question, difficulty?, answers: [a0, a1, a2, a3] }
Note: answers[0] is the correct answer.

POST /library/import → bulk import (schema like backend/data/seed_quizzes.json)

POST /library/session/create → start session
body: { player_name, quiz_id } → returns { session_id }

GET /library/session/<sid>/current → current question (options are shuffled)

POST /library/session/<sid>/answer → submit answer
body: { answer, client_ms } (optionally also { answer_index })

GET /library/leaderboard?quiz_id=<id> → top 10
Sorted by score desc, then duration_ms asc, then id asc

Response envelope (normalized)
{ "ok": true,  "data": ... }
{ "ok": false, "error": { "code": "bad_request", "message": "..." } }

Timer & Scoring (How it works)

The frontend starts a per-question timer (performance.now()) when a question is received.

On answer, it POSTs client_ms to /library/session/<sid>/answer.

The backend:

checks correctness against answers[0];

computes awarded points: max(100, 1000 - client_ms/2) if correct, else 0;

logs to QuizAnswerLog;

on session end, sums all client_ms and writes LeaderboardEntry.duration_ms.

The frontend shows current score while playing; on finish, see final score + total time (server-stored).

Onboarding for Teammates (TL;DR)
git clone <repo>
cd Game_maker

# Backend — see "Backend — Setup & Run"
# Frontend — see "Frontend — Setup & Run"

Troubleshooting

ModuleNotFoundError: No module named 'flask'
venv not active / deps missing. Activate venv and pip install -r requirements.txt.

OperationalError: no such table: …
Run flask db upgrade. Still failing on local dev? Delete backend/instance/users.db and upgrade again.

Target database is not up to date.
Run flask db upgrade. If Alembic is confused but schema is correct, run flask db stamp head.

no such column: user.created_at
You added a column after DB existed. Create migration:
flask db migrate -m "add created_at" then flask db upgrade.
For dev only, you can reset SQLite and upgrade.

Roadmap by Phases (Updated)

Phase 1 — Core (✅ done)

User signup/login (hash)

Create quizzes & add questions

Single-player session flow

Leaderboard (score + time)

Phase 2 — Enhancements (▶ in progress)

JWT auth (tokens)

Admin actions: delete quizzes / topics

Better error handling/helpers

JSON import UX

Frontend filters – Category ✅

Frontend filters – Difficulty ⏳ not yet

Phase 3 — Advanced (🗺 planned)

Docker deployment

Multiplayer / realtime

Demo screenshots/GIFs ✅

## 📸 Demo

Below are some example screenshots from the project:

### Login/sign in Page
![Login Page](frontend/public/screenshots/login.png)

### Quiz Selection
![Topic Selection](frontend/public/screenshots/select_topic.png)
![Game Selection](frontend/public/screenshots/pick_a_quiz.png)

### Playing a Quiz
![Quiz Session](frontend/public/screenshots/play_session.png)

### Leaderboard
![Leaderboard](frontend/public/screenshots/leaderboard.png)

### Create a New Quiz
![Create a New Quiz](frontend/public/screenshots/create_quiz.png)

### Create a New Question

![Create a New Question](frontend/public/screenshots/add_and_match_q.png)









