# 🎮 Game Maker – Trivia App

Full-stack trivia game built with **Flask (Python)** + **React (Vite)**.  
Backend runs on **port 5001**, Frontend on **port 5173**.

---

## Requirements

- Python 3.11+ (with `venv`)
- Node.js 18+ + npm

---

## Setup & Run

### 1. Clone repo
```bash
git clone <repo-url>
cd Game_maker

#Backend (Flask)

# create & activate venv
py -m venv .venv
.\.venv\Scripts\activate   # Windows

# install deps
pip install -r requirements.txt

# run backend
python app.py


#Frontend (React + Vite)

cd frontend

# install deps
npm install

# run frontend
npm run dev


###  API Test (Postman examples)

# Signup
# POST http://localhost:5001/users/signup
# { "username": "neo", "password": "1234" }

# Add question
# POST http://localhost:5001/library/add
# { "question": "2+2?", "answer": "4", "topic": "Math" }

# List questions
# GET http://localhost:5001/library/


# Notes

# Ignore files in Git: .venv, instance/users.db, .env, frontend/node_modules, frontend/dist

# Config values (DB URL, secrets) are in .env

# To reset DB: delete instance/users.db and rerun python app.py


# Run Backend and Frontend in two separate terminals