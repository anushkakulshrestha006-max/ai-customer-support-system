# NovaStore Support — AI Customer Support Assistant

An intelligent, full-stack customer support application for a fictional e-commerce store, built with **FastAPI**, **MySQL**, **LangChain**, **FAISS**, and **Streamlit**.

The system uses **Retrieval-Augmented Generation (RAG)** to answer customer inquiries regarding store delivery timelines, refund terms, payment issues, cancellations, and account settings directly from policy documents. It also provides human escalation through support tickets, interactive ticket status management, and live support analytics.

---

## 1. Problem Statement

E-commerce support teams face high volumes of repetitive inquiries about shipping times, return windows, refund procedures, and payment failures. Manual handling of these inquiries leads to delayed responses and human agent fatigue.

**NovaStore Support** addresses this challenge by:
1. Grounding AI responses in store policy documents using FAISS semantic vector search to prevent hallucinations.
2. Automatically classifying user questions into 6 standard categories: *Payment*, *Delivery*, *Refund*, *Cancellation*, *Account*, and *Other*.
3. Persisting all customer inquiries and AI responses in MySQL for audit history.
4. Allowing customers to escalate unresolved issues into support tickets.
5. Equipping support staff with a dashboard for KPI tracking, distribution analytics, and ticket lifecycle management.

---

## 2. System Architecture

```text
       [ Customer / Support Agent ]
                    │
                    ▼
     [ Streamlit Web Interface ]
     (Port 8501: Dashboard, RAG, Tickets)
                    │
             HTTP / REST Calls
                    │
                    ▼
          [ FastAPI Backend ]
        (Port 8001: Uvicorn Server)
         │              │         │
         ▼              ▼         ▼
  [Intent & RAG]   [SQLAlchemy]  [Health Check]
   - Chunking          CRUD            │
   - Embeddings         │              ▼
   - FAISS Search       ▼         [Status Monitor]
   - Gemini / Demo   [ MySQL ]
                    - customers
                    - conversations
                    - tickets
```

### Component Roles

- **FastAPI**: Serves RESTful API endpoints for question answering, ticket management, customer profiles, and health checks with automatic OpenAPI schema validation via Pydantic.
- **FAISS (Facebook AI Similarity Search)**: Stores high-dimensional vector embeddings of policy document chunks and performs low-latency cosine/similarity search to retrieve relevant context.
- **Google Gemini (`gemini-1.5-flash`)**: Synthesizes customer-friendly answers constrained strictly to retrieved context. When no API key is provided, the application runs in a local **Demo Mode** using policy extraction without crashing.
- **MySQL & SQLAlchemy**: Provides relational persistence for customer records, conversation audit trails, and support tickets with cascade relationships and indexing.
- **Streamlit**: Delivers a multi-page interactive web interface with live support metrics, interactive RAG inquiry, and ticket lifecycle management.

---

## 3. Technology Stack

- **Backend:** Python 3.9, FastAPI, Uvicorn, Pydantic v2
- **Database:** MySQL 8.x, SQLAlchemy ORM, PyMySQL
- **RAG & AI:** LangChain Core, LangChain Community, FAISS, Google Generative AI (`gemini-1.5-flash`)
- **Frontend:** Streamlit
- **Testing:** Pytest, FastAPI TestClient, Streamlit AppTest
- **Configuration:** python-dotenv

---

## 4. MySQL Database Schema

The database consists of three normalized tables:

1. **`customers`**: Registered customer accounts.
   - `id` (INT, PK, Auto Increment)
   - `name` (VARCHAR(100))
   - `email` (VARCHAR(100), UNIQUE, Indexed)
   - `created_at` (DATETIME)

2. **`conversations`**: Historical log of customer inquiries and AI answers.
   - `id` (INT, PK, Auto Increment)
   - `customer_id` (INT, FK -> `customers.id`, Indexed)
   - `question` (TEXT)
   - `answer` (TEXT)
   - `created_at` (DATETIME)

3. **`tickets`**: Escalated customer issues requiring agent intervention.
   - `id` (INT, PK, Auto Increment)
   - `customer_id` (INT, FK -> `customers.id`, Indexed)
   - `issue` (TEXT)
   - `category` (VARCHAR(50): Payment, Delivery, Refund, Cancellation, Account, Other)
   - `status` (VARCHAR(50): Open, In Progress, Resolved, Closed)
   - `created_at` (DATETIME)

---

## 5. Application Pages & Features

### 1. Support Dashboard (Analytics)
- **KPI Metrics:** Live counts for Total Customers, Total Questions, Total Tickets, Open Tickets, and Resolved Tickets.
- **Tickets by Category Chart:** Distribution across Payment, Delivery, Refund, Cancellation, Account, and Other.
- **Tickets by Status Chart:** Breakdown of Open, In Progress, Resolved, and Closed tickets.
- **Conversation Activity by Date Chart:** Chronological bar chart of inquiry volume.
- **Backend Health & Refresh:** Live connection status with an on-demand refresh button.

### 2. Ask Support (RAG)
- **Quick Example Questions:** One-click pre-filled inquiry prompts:
  - *How long does standard delivery take?*
  - *What is your refund policy?*
  - *How can I cancel an order?*
  - *What payment methods are supported?*
- **Custom Question Input:** Free-form text inquiry.
- **Grounded AI Answers:** Generates answers using only verified store policies with cited source files (e.g., `delivery_policy.md`).
- **Ticket Escalation:** In-place expander allowing customers to escalate unresolved inquiries into human support tickets with pre-filled context.

### 3. Conversation History
- Displays all past interactions stored in MySQL with timestamps and customer attribution.
- Supports filtering by the currently active customer profile.

### 4. Support Tickets
- Searchable data table displaying all support tickets, their status, customer details, and creation dates.
- **Interactive Status Transition Tool:** Support agents can update ticket statuses between **Open**, **In Progress**, **Resolved**, and **Closed** with live database synchronization.

### 5. Create Ticket
- Manual ticket escalation form for customers with category selection and issue details.

---

## 6. Getting Started

### Prerequisites
- Python 3.9+
- MySQL Server running locally on port 3306

### Step 1: Clone and Set Up Virtual Environment
```powershell
cd E:\ai_customer_support
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Environment Configuration
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Ensure your MySQL credentials match your local setup:
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=ai_customer_support

# Optional: Add your Gemini key for live LLM generation
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash

BACKEND_HOST=127.0.0.1
BACKEND_PORT=8001
BACKEND_URL=http://127.0.0.1:8001
```

### Step 3: Ingest Policy Documents
Rebuild the local FAISS vector store from markdown documents in `data/knowledge_base/`:
```powershell
.\venv\Scripts\python scripts/ingest_documents.py
```

### Step 4: Initialize and Seed Database
Create MySQL tables and insert initial demo customer profiles:
```powershell
.\venv\Scripts\python database/seed.py
```

---

## 7. Running the Application

Start the backend and frontend in separate terminal windows:

### Terminal 1 — FastAPI Backend:
```powershell
.\venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
- Interactive API Docs (Swagger): `http://127.0.0.1:8001/docs`
- Health Check: `http://127.0.0.1:8001/health`

### Terminal 2 — Streamlit Frontend:
```powershell
.\venv\Scripts\streamlit run streamlit_app/app.py
```
- Web Application: `http://localhost:8501`

---

## 8. Automated Testing

The project includes unit and integration tests across the API, database, and RAG pipeline:
```powershell
.\venv\Scripts\pytest -v
```
**Test Coverage (28 Automated Tests Passing):**
- **API Tests (`tests/test_api.py`):** Root endpoint, health check, customer listings, valid RAG inquiry, invalid customer handling, empty input validation, ticket creation, ticket listing, conversation retrieval, valid ticket status update (`PATCH /tickets/{id}/status`), invalid status rejection (400), non-existent ticket handling (404).
- **Database Tests (`tests/test_database.py`):** Connection verification, seeded customer validation, ticket creation/retrieval, conversation persistence, CRUD status update.
- **RAG Tests (`tests/test_rag.py`):** Document loader, recursive character chunking, semantic delivery search, semantic payment search, multi-intent classification, full RAG answer generation, quick example questions verification, policy-grounded demo answer quality (no technical tags), and out-of-scope question handling.
- **Streamlit UI Tests (`tests/test_streamlit_ui.py`):** AppTest verification of safe Clear Input execution (zero StreamlitAPIException), quick example selection and submission, and empty question validation.


---

## 9. Demo Mode & Portfolio Scope

- **Offline Demo Mode:** If `LLM_API_KEY` is omitted or left as default, the application runs in local demonstration mode using deterministic embeddings and retrieved context extraction.
- **Live Gemini Generation:** Adding a valid Google Gemini API key to `.env` seamlessly enables live generation using `gemini-1.5-flash`.
- **Project Scope:** This application is built as a portfolio project demonstrating practical skills in RAG architecture, vector search, relational database modeling, and full-stack API integration.