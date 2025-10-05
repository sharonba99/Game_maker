import json, requests, sys
from pathlib import Path

# robust path: backend/tools -> parents[1] == backend/
ROOT = Path(__file__).resolve().parents[1]
API = "http://localhost:5001/library/import"  # שימי לב ל-/library
PATH = ROOT / "data" / "seed_quizzes.json"

def main():
    if not PATH.exists():
        print(f"File not found: {PATH}", file=sys.stderr)
        sys.exit(1)
    payload = json.loads(PATH.read_text(encoding="utf-8"))
    r = requests.post(API, json=payload, timeout=30)
    print("Status:", r.status_code)
    print(r.text)

if __name__ == "__main__":
    main()