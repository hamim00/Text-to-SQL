# Phase 1 Architecture

## Data flow (end-to-end)

User question (Streamlit)  
→ schema introspection (`t2s/sql/schema.py`)  
→ prompt assembly (`t2s/sql/prompting.py`)  
→ LLM provider (`t2s/providers/*`) generates SQL  
→ safety gate (`t2s/sql/safety.py`) validates & rewrites (enforce LIMIT)  
→ DB execution (`t2s/db/runner.py`)  
→ results rendered in UI

## Modules
- `t2s/providers/`: provider implementations (Ollama, Groq)
- `t2s/sql/`: schema, prompting, safety
- `t2s/db/`: database connection & query execution
- `ui/`: Streamlit UI
- `scripts/`: local utilities (seed DB)
- `tests/`: unit tests for SQL safety

## Design goals
- Small, readable codebase
- Hard safety boundary before DB execution
- Provider-agnostic core logic
