# Trivia Creator — Backend

A small Flask API for creating and playing trivia quizzes: user auth, quiz library (CRUD-lite + import), game sessions, and a leaderboard.

## Features
- **Users**: signup/login with hashed passwords.
- **Quizzes**: list by topic, create, add questions, bulk import.
- **Game sessions**: step through questions, scoring by speed.
- **Leaderboard**: top scores per quiz (tie-break by total time).
- **CORS** enabled for local frontends (Vite/CRA).

## Tech Stack
- **Python**, **Flask**, **Flask-CORS**
- **SQLAlchemy**, **Flask-Migrate** (Alembic)
- **python-dotenv**
- **SQLite** for local dev (or `DATABASE_URL` for Postgres, etc.)

## Project Structure
```text
.
├─ app.py                  # App factory, CORS, SQLAlchemy, Migrate, blueprint registration
├─ models.py               # SQLAlchemy models (User, Quiz, TriviaQuestion, QuizSession, QuizAnswerLog, LeaderboardEntry)
├─ blueprints/
│  ├─ __init__.py
│  ├─ users.py             # /users: signup/login/list
│  └─ library.py           # /library: topics, quizzes, import, sessions, leaderboard
├─ utils/
│  └─ db.py                # shared SQLAlchemy() instance
├─ instance/
│  ├─ .gitkeep
│  └─ users.db             # local SQLite (dev)
├─ frontend/               # frontend app (separate)
├─ .env                    # environment variables (see below)
├─ .gitignore
├─ requirements.txt
└─ README.md



## Prerequisites
- Python 3.10+ recommended
- `pip` and a virtual environment (optional but recommended)

## Environment Variables (`.env`)
Create `.env` at the project root (same folder as `app.py`):

FLASK_APP=app:create_app
FLASK_DEBUG=1
FLASK_SECRET_KEY=dev-secret-change-me
JWT_SECRET_KEY=dev-jwt-change-me
CORS_ORIGINS=http://localhost:5173, 
http://localhost:3000
PORT=5001

Optional: override DB (otherwise defaults to SQLite in instance/users.db)
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/game_maker


> The app calls `load_dotenv()`, so both `python app.py` and `flask db ...` will pick this up automatically.

## Setup & Run
Install dependencies and start the dev server:

```bash
pip install -r requirements.txt
python app.py
Server runs on http://localhost:5001.
Health check: GET / → {"ok": true, "db": "<engine url>"}.

Database & Migrations (Flask-Migrate)
Important: .env already sets FLASK_APP=app:create_app, so you can use flask db ... directly.

Scenario A — Fresh project, empty DB (first time only)

flask db init
flask db migrate -m "init schema"
flask db upgrade
python app.py

Scenario B — Existing DB, keep the data
If the repo already contains migrations/:

pip install -r requirements.txt
flask db upgrade
python app.py

If there is no migrations/ yet but you already have a populated DB and want to start managing migrations from now on:

flask db init
flask db stamp head
python app.py
Next schema change: flask db migrate -m "..." → flask db upgrade.

Scenario C — You changed the models/schema

flask db migrate -m "describe your change"
flask db upgrade
python app.py
Scenario D — Teammate just cloned the repo

pip install -r requirements.txt
flask db upgrade
python app.py

### Creating the Frontend client:
cd frontend
npm install
npm run dev



API (Quick Summary)
/users
GET /users/ — list users (id, username)

POST /users/signup — { "username", "password" } → creates user

POST /users/login — { "username", "password" } → { "user_id", "username" }

/library
GET /library/topics — distinct topics

GET /library/quizzes?topic=... — quizzes (with question count)

GET /library/quizzes/<quiz_id> — quiz + questions

POST /library/quizzes — { title, topic, difficulty? }

POST /library/questions — { quiz_id, question, difficulty?, answers[4] } (answers[0] is correct)

POST /library/import — bulk create quizzes + questions

POST /library/session/create — { player_name, quiz_id } → { session_id }

GET /library/session/<sid>/current — current question (options are shuffled)

POST /library/session/<sid>/answer — { answer, client_ms } → scoring & next/finish

GET /library/leaderboard?quiz_id=... — top 10 by score, then total time

All responses are normalized:

success → { "ok": true, "data": ... }

error → { "ok": false, "error": { "code", "message" } }

Troubleshooting
No such command 'db'
Ensure Flask-Migrate is installed and Migrate(app, db) is present in create_app().
.env must include FLASK_APP=app:create_app. You can also run:
python -m flask db upgrade

No changes detected during flask db migrate
Make sure the app imports all models inside an app context in create_app():


with app.app_context():
    from models import User, TriviaQuestion, Quiz, QuizSession, QuizAnswerLog, LeaderboardEntry
no such table: user
Run migrations: flask db migrate -m "init schema" → flask db upgrade.

Wrong DB?
Hit GET / (health) to see which DB URL was loaded (default is instance/users.db if no DATABASE_URL).
















