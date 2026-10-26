# NovaStore — AI Customer Support System

An end-to-end intelligent customer support and ticket management platform built with **FastAPI**, **LangChain**, **FAISS**, **MySQL**, and **Streamlit**.

The main idea behind this project is to automate first-line customer support for an e-commerce platform. Instead of support agents manually handling repetitive inquiries about shipping times, refund terms, payment failures, and order cancellations, the system uses **Retrieval-Augmented Generation (RAG)** to provide instant, accurate answers strictly grounded in official store policy documents.

If an inquiry cannot be resolved automatically, customers can directly escalate the issue into a support ticket, and support agents can track, update, and analyze tickets through an interactive dashboard.

---

## What It Does

- **Answers Policy Questions:** Uses semantic search across policy documents to generate accurate, hallucination-free answers.
- **Auto-Categorizes Inquiries:** Classifies questions into *Delivery*, *Payment*, *Refund*, *Cancellation*, *Account*, or *Other*.
- **Logs Full Conversations:** Automatically persists inquiries, answers, and timestamps to MySQL for auditing.
- **Ticket Escalation:** Lets customers turn unresolved inquiries into support tickets with pre-filled context.
- **Ticket Status Management:** Allows support agents to review tickets and update statuses (*Open*, *In Progress*, *Resolved*, *Closed*).
- **Analytics Dashboard:** Visualizes live support KPIs, category distributions, ticket statuses, and inquiry activity trends.
- **Customer Profile Switching:** Allows testing and viewing support history across multiple customer accounts.

---

## How It Works

```text
Customer Question
       ↓
Search Store Policies (FAISS Vector Search)
       ↓
Generate Grounded Response (LangChain + Gemini / Demo Engine)
       ↓
Categorize & Save Conversation to MySQL
       ↓
Escalate to Support Ticket (if needed)
       ↓
Track & Manage on Support Dashboard
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.9+ |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2 |
| **Frontend UI** | Streamlit |
| **Vector Search & RAG** | LangChain, FAISS, Google Generative AI (`gemini-1.5-flash`) |
| **Database & ORM** | MySQL 8.x, SQLAlchemy, PyMySQL |
| **Testing** | Pytest, FastAPI TestClient, Streamlit AppTest |
| **Configuration** | python-dotenv |

---

## Application Pages

1. **Support Dashboard:** High-level metrics (Total Customers, Questions, Tickets, Open/Resolved status) and interactive charts showing tickets by category and daily activity.
2. **Ask Support (RAG):** Interactive chat interface with quick pre-set questions, custom text inquiry, grounded answers with policy citations, and in-place ticket escalation.
3. **Conversation History:** Chronological log of past interactions, with optional filtering by active customer.
4. **Support Tickets:** Data table of all logged support tickets with an interactive status updater for support agents.
5. **Create Ticket:** Dedicated form to submit a support ticket directly to the team.

---

## Installation & Setup

### Prerequisites

- Python 3.9+
- MySQL Server running locally on port 3306

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/anushkakulshrestha006-max/ai-customer-support-system.git
cd ai-customer-support-system

# 2. Create and activate a virtual environment
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
# Copy .env.example to .env
# Windows (PowerShell):
Copy-Item .env.example .env
# Linux/macOS:
# cp .env.example .env
```

### Environment Configuration (`.env`)

Configure your database credentials and optional Google Gemini API key:

```env
# MySQL Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=ai_customer_support

# Gemini API Key (Optional: runs in local demo mode if omitted)
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash

# Backend Settings
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8001
BACKEND_URL=http://127.0.0.1:8001
```

---

## Data Ingestion & Database Setup

Before running the application for the first time:

```bash
# 1. Build the FAISS vector index from store policy files
python scripts/ingest_documents.py

# 2. Create MySQL tables and seed initial customer profiles
python database/seed.py
```

---

## Running the Application

Start the backend and frontend in two separate terminal windows:

### 1. Start the FastAPI Backend:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
- **API Documentation (Swagger UI):** `http://127.0.0.1:8001/docs`
- **Health Check:** `http://127.0.0.1:8001/health`

### 2. Start the Streamlit Frontend:
```bash
streamlit run streamlit_app/app.py
```
- **Web Interface:** `http://localhost:8501`

---

## Running Tests

To run the complete automated test suite (covering API endpoints, database operations, RAG search, and UI flows):

```bash
pytest -v
```

---

## Project Structure

```text
ai-customer-support-system/
├── app/
│   ├── api/             # FastAPI route definitions (conversations, tickets, support)
│   ├── database/        # MySQL models, connection, and CRUD helpers
│   ├── rag/             # Document loader, embeddings, FAISS store, QA pipeline
│   ├── schemas/         # Pydantic request and response models
│   └── services/        # Business logic, response formatter, ticket service
├── data/
│   └── knowledge_base/  # Store policy markdown documents
├── database/            # MySQL schema DDL and seed scripts
├── scripts/             # Policy ingestion utilities
├── streamlit_app/       # Streamlit UI pages and dashboard
├── tests/               # Pytest suite (API, database, RAG, and UI tests)
├── .env.example         # Environment template
└── requirements.txt     # Python dependencies
```