
# Kahoot-Style Office Trivia — Difficulty Edition (Flask + SQLite)

Participants: Roni, Tomer, Dani, Mor
Topics: **Music**, **Television**, **Eurovision**
Difficulties: **Easy / Medium / Hard** (Any = mixed)

## Run
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
python app.py
```
Open: http://127.0.0.1:5000/

## Notes
- If you previously ran an older version, delete `app.db` to reseed with the new question bank and difficulty.
- API `POST /api/kahoot/games/create` accepts: `topic_id`, optional `difficulty` (Any/Easy/Medium/Hard), and `num_questions`.
- Scoring: Easy=100, Medium=200, Hard=300.
