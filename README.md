# AI Content Repurposing & Scoring Agent

Turns one piece of source content (blog draft, transcript, notes) into:
- A LinkedIn post
- A Twitter/X thread
- A short blog summary

...in your own voice, remembered across sessions via a Pinecone-backed
**agentic long-term memory** — the agent itself decides when to check memory
and when to write to it, via LangChain tools (not a hardcoded pipeline).

## Why this is different from a plain RAG bot
- **Agentic memory, not just chat history**: style examples and past content
  persist in Pinecone across sessions/users, and the agent chooses to query
  or write to them as tools — this is long-term memory, not a conversation buffer.
- **Self-scoring loop**: the agent scores its own LinkedIn draft (1–10) and
  rewrites automatically until it reaches 10/10 (or 4 attempts), only then
  shows you the final version.
- **No Docker/Kubernetes**: deployed straight to Azure App Service's native
  Python runtime via GitHub Actions CI/CD.

## Senior-level concepts implemented

1. **LLM-as-Judge Evaluation Framework** (`eval_framework.py`) — scores each post on
   independent rubric criteria (hook, clarity, authenticity, value, CTA) instead of one
   opaque number, and names the weakest dimension + a specific fix.
2. **Guardrails & Content Safety Layer** (`guardrails.py`) — checks for PII leakage,
   toxic language, and risky absolute/legal-exposure claims before anything is saved or shown.
3. **Observability & Tracing** (`observability.py`) — structured JSON-line trace log of every
   agent run: spans, latency, rough token estimates. Swap-in point for Azure App Insights/LangSmith.
4. **Human-in-the-Loop Review Gate** — if guardrails fail (or the agent can't resolve a flag
   after 2 rewrite attempts), the post is routed to `/approve` in the UI for manual
   edit/approve/reject instead of auto-publishing.
5. **Data Flywheel** (`data_flywheel.py`) — `/feedback` lets you report how a post actually
   performed after publishing; that's embedded into the same style-memory namespace the
   agent queries before drafting, so real performance (not just past style) shapes future output.
6. **A/B Variant Generation** — the agent produces two distinct opening hooks per post; whichever
   you pick is fed back into memory as a preference signal.

## Architecture
```
frontend/ (Streamlit)  --HTTP-->  backend/ (FastAPI + LangChain agent)
                                        |
                                        +--> Groq (LLM)
                                        +--> Pinecone (agentic memory: style + content)
```

## Local setup

### 1. Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
GROQ_API_KEY=your_groq_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=content-agent-memory
GROQ_MODEL=llama-3.3-70b-versatile
```

Run it:
```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export BACKEND_URL=http://localhost:8000   # Windows: set BACKEND_URL=...
streamlit run app.py
```

## Deploying to Azure App Service (CI/CD, no Docker/K8s)

1. Create **two** Azure App Service instances (Linux, Python 3.11 stack):
   - one for the backend (FastAPI)
   - one for the frontend (Streamlit)

2. On each App Service, set the **Startup Command**:
   - Backend: `gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app`
   - Frontend: `python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0`

3. On each App Service > Configuration > Application settings, add:
   - Backend: `GROQ_API_KEY`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `GROQ_MODEL`
   - Frontend: `BACKEND_URL` = your deployed backend's URL (e.g. `https://<backend-app>.azurewebsites.net`)

4. Download each App Service's **Publish Profile** (Overview > Get publish profile)
   and add them as GitHub repo secrets:
   - `AZURE_BACKEND_APP_NAME`, `AZURE_BACKEND_PUBLISH_PROFILE`
   - `AZURE_FRONTEND_APP_NAME`, `AZURE_FRONTEND_PUBLISH_PROFILE`

5. Push to `main` — `.github/workflows/azure-deploy.yml` builds and deploys
   both apps automatically via Azure's native Oryx Python build (no
   Dockerfile, no container registry, no Kubernetes involved).

## Notes
- The embedding model runs locally (`sentence-transformers/all-MiniLM-L6-v2`),
  so there's no separate embedding API cost.
- Pinecone index is created automatically on first run (serverless, free-tier
  compatible spec — adjust `cloud`/`region` in `memory_store.py` if needed).
- Each user's memory is isolated by Pinecone namespace (`style::<user_id>`,
  `content::<user_id>`), so this can scale to multiple users without changes.
