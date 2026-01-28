# Text-to-SQL (v2) — Safe, Schema-Aware, Streaming UI

This is a clean-room rebuild of a Text-to-SQL project.

## What you get in Phase 1
- Streamlit chat UI
- SQLite database (sample `student.db`)
- Runtime schema introspection
- SQL safety gate (SELECT-only, single statement, enforced LIMIT)
- Provider abstraction:
  - **Ollama** (local, free): default
  - **Groq** (cloud, free tier with rate limits): optional

> Feature 6 (observability/governance) is intentionally deferred.

---

## Quickstart (Windows / macOS / Linux)

### 1) Create venv & install dependencies
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### 2) Create a sample DB
```bash
python scripts/seed_student_db.py
```

### 3) Configure env
Copy `.env.example` to `.env` and edit values:
```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

### 4) Run the app
```bash
streamlit run ui/app.py
```

---

## Provider notes

### Ollama (local)
1) Install Ollama
2) Pull a model
```bash
ollama pull llama3.1:8b-instruct
```
3) Keep Ollama running. The app calls `http://localhost:11434`.

### Groq (cloud)
Set in `.env`:
- `T2S_PROVIDER=groq`
- `GROQ_API_KEY=...`
- `GROQ_MODEL=...`

---

## Project structure
See `docs/architecture.md`.
