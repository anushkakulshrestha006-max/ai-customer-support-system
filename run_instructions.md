# AI Customer Support System - Quick Run Instructions

Follow these step-by-step commands in your terminal or VS Code to run the project.

---

## 1. Quick One-Line Automated Verification
To run the automated test suite across all layers (Database, RAG, API):
```powershell
.\venv\Scripts\pytest -v
```

---

## 2. Ingest Policy Documents (Rebuild FAISS Vector Store)
Whenever you modify or add `.md` files in `data/knowledge_base/`:
```powershell
.\venv\Scripts\python scripts/ingest_documents.py
```

---

## 3. Seed Database (Demo Customers)
To create tables and seed initial demo customer profiles:
```powershell
.\venv\Scripts\python database/seed.py
```

---

## 4. Run the Full Application Locally

You will run the backend and frontend in two separate terminal windows:

### Terminal 1 - FastAPI Backend:
```powershell
.\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: **http://127.0.0.1:8000/docs**
- Health check: **http://127.0.0.1:8000/health**

### Terminal 2 - Streamlit Frontend:
```powershell
.\venv\Scripts\streamlit run streamlit_app/app.py
```
- Web Application: **http://localhost:8501**

---

## 5. Adding Your Google Gemini API Key
To enable live AI answers using Google Gemini:
1. Open the file `.env` in the root folder.
2. Replace `LLM_API_KEY=` with your Gemini key (e.g. `LLM_API_KEY=AIzaSy...`).
3. Save the file. The backend will automatically reload and use live Google Gemini generation!
