# Financial NL2SQL Agent 🚀
An enterprise-grade Natural Language to SQL pipeline designed to query financial metrics stored in an SQLite database effortlessly.

This project uses a layered architecture to securely convert conversational questions into optimal, strictly validated SQL queries, executing them against a local domain database, and serving the results through an elegant API and web UI.

---

## What Has Been Implemented 🛠️

1. **Schema-Aware LLM Generation Layer (`app/llm.py`, `app/schema.py`)** 🧠
    - Dynamically queries SQLite metadata at initialization and generates stringified schema representation.
    - Feeds metadata explicitly to Groq (a fast OpenAI-compatible wrapper) via the `SQLGenerator`.

2. **In-Context Few-Shot Semantic Memory (`app/memory.py`, `app/seed_memory.py`)** 📖
    - Utilizes a robust suite of optimized historical text-to-sql questions (e.g. `Show me the top 5 companies by total assets`) securely connected to Vanna's internal semantic capabilities.
    - Matches users' queries against memory entries, improving correct domain SQL generation natively.

3. **Strict Validation & Security Layer (`app/security.py`)** 🛡️
    - Ensures 100% read-only operations via rigid regular expressions preventing destructive SQL (`DROP`, `DELETE`, `ALTER`).
    - Validates returned SQL column paths and bindings specifically against the parsed Database Schema. 

4. **Pipeline Execution & Fallbacks (`app/pipeline.py`, `app/database.py`)** ⚙️
    - Safely unrolls operations: Extract Request ➔ Search Memory ➔ Generate SQL ➔ Validate Syntax ➔ Sanitize against Schema ➔ Execute Cursor Query ➔ Wrap to JSON.
    - Beautifully structures empty datasets, truncation caps, and gracefully explains syntax generation failures without crashing the server.

5. **FastAPI Web Delivery (`app/api.py`, `app/models.py`)** 🌐
    - Typed Pydantic data schemas for JSON integrity.
    - Exposes a `ChatResponse` at `POST /chat` and health states at `GET /health`.
    - Integrated with a NextGen Glassmorphic UI served dynamically from `static/`.

---

## Running the Application ⚡

Start up the Uvicorn server, running the `main.py` entry point:
```bash
.venv\Scripts\python main.py
```

- **Open the Front-End UI Application**: Visit `http://127.0.0.1:8000` in your web browser!
- **Test Endpoint (Health Check)**: `curl http://127.0.0.1:8000/health`

## File Structure 📂
- `app/api.py`: FastAPI Routes and Static file serving configurations.
- `app/pipeline.py`: The single operational chain for parsing natural language to SQL executing gracefully.
- `app/security.py`: Guardrails preventing bad SQL execution.
- `app/seed_memory.py`: Our domain expertise injected into local agent memory context.
- `static/`: Contains the beautiful Dark-Mode Glassmorphism Web Interface files (`index.html`, `style.css`, `script.js`).
- `main.py`: The Uvicorn entry program.
