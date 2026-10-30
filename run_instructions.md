# AI Customer Support System - Quick Run Instructions

Follow these step-by-step commands in your terminal or VS Code to run the project locally.

---

## 1. Quick Automated Test Suite
To run the automated test suite across all layers (Database, RAG, API, Cloud Deployment, and UI):
```powershell
.\venv\Scripts\pytest -v
```

---

## 2. Ingest Policy Documents (Rebuild FAISS Vector Store)
Build or rebuild the FAISS vector index from `data/knowledge_base/*.md`:
```powershell
.\venv\Scripts\python scripts/ingest_documents.py
```

---

## 3. Initialize & Seed Database
Create MySQL tables safely (non-destructive) and seed initial demo customer profiles:
```powershell
.\venv\Scripts\python scripts/init_database.py --seed
```

---

## 4. Run the Full Application Locally

Run the backend and frontend in two separate terminal windows:

### Terminal 1 — FastAPI Backend:
```powershell
.\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
- Interactive API Docs: **http://127.0.0.1:8001/docs**
- Health Overview: **http://127.0.0.1:8001/health**
- Liveness Probe: **http://127.0.0.1:8001/health/live**
- Readiness Probe: **http://127.0.0.1:8001/health/ready**

### Terminal 2 — Streamlit Frontend:
```powershell
.\venv\Scripts\streamlit run streamlit_app/app.py
```
- Web Application: **http://localhost:8501**

---

## 5. Adding Your Google Gemini API Key
To enable live AI answers using Google Gemini:
1. Open the file `.env` in the root folder.
2. Set `LLM_API_KEY=your_gemini_api_key_here`.
3. Save the file. The backend will automatically reload and use live Google Gemini generation!
*(Note: If the key is omitted or invalid, the system automatically falls back to offline policy-grounded answers without crashing.)*
