# AI Customer Support System

A clean, beginner-friendly, and production-structured **AI Customer Support System** built from scratch with **Python**, **FastAPI**, **MySQL**, **LangChain**, **FAISS**, and **Streamlit**.

Designed specifically for CSE students and software engineering candidates to demonstrate core competencies in:
- Relational Database Management (MySQL & SQLAlchemy)
- RESTful API Design (FastAPI & Pydantic V2)
- Retrieval-Augmented Generation (RAG)
- Semantic Vector Search (FAISS & Embeddings)
- Large Language Models (Google Gemini API)
- Interactive Fullstack Development (Streamlit)

---

## 1. Project Overview & Problem Statement

### The Problem
Customer support departments in e-commerce companies frequently answer repetitive inquiries regarding shipping schedules, return policies, payment issues, and cancellation rules. Manually addressing these simple questions leads to high support costs and slow response times.

### The Solution
The **AI Customer Support System** automates first-line customer assistance:
1. **Accurate Grounding:** Instead of relying on raw LLM hallucination, the system queries curated company policy documents using semantic vector search (RAG).
2. **Context-Aware Responses:** An LLM synthesizes clear, customer-friendly answers based strictly on retrieved context.
3. **Audit & Traceability:** Every question and answer is logged to a persistent MySQL relational database.
4. **Seamless Human Escalation:** If the AI response does not resolve the customer's issue, the user can immediately escalate to human staff by creating a categorized support ticket stored in MySQL.

---

## 2. Key Features

- **Semantic Policy Search (RAG):** Fast vector similarity retrieval using FAISS over local Markdown policy documents.
- **Intent / Category Classification:** Classifies user inquiries into 6 categories: *Payment, Delivery, Refund, Cancellation, Account, Other*.
- **Strict Hallucination Guards:** System prompt directs the LLM to only respond based on retrieved facts and clearly state when policies do not cover an inquiry.
- **MySQL Relational Persistence:** Full relational schema with foreign key constraints tracking Customers, Conversations, and Tickets.
- **Human Escalation (Support Tickets):** Converts unresolved questions into tracked support tickets with automatic category detection.
- **Clean Interactive UI (Streamlit):** Multi-page web dashboard with live backend health checks, customer switching, conversation review, and ticket monitoring.
- **Offline / Zero-Cost Fallback Mode:** Works seamlessly even before an API key is provided, using a local deterministic embedding fallback model.

---

## 3. Architecture & Data Flow

```text
       User Inquiry
            │
            ▼
    ┌───────────────┐
    │ Streamlit UI  │ (Port 8501)
    └───────┬───────┘
            │ HTTP POST /ask
            ▼
    ┌───────────────┐
    │ FastAPI API   │ (Port 8000)
    └───────┬───────┘
            │
    ┌───────┴───────────────────────────────┐
    │ 1. Validate Customer (MySQL)          │
    │ 2. Classify Category (Payment, etc.)   │
    │ 3. Query FAISS Vector Store           │
    │ 4. Prompt Gemini LLM with Context     │
    │ 5. Store Q&A in MySQL Conversations   │
    └───────┬───────────────────────────────┘
            │
            ▼
    ┌───────────────┐
    │ MySQL Database│ (ai_customer_support)
    └───────────────┘
```

---

## 4. Tech Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | FastAPI | High-performance, automatic OpenAPI docs, native async support. |
| **Data Validation** | Pydantic V2 | Type-safe schema validation for requests and responses. |
| **Database** | MySQL 8.0 | Industry-standard relational DBMS demonstrating SQL modeling. |
| **ORM** | SQLAlchemy 2.0 + PyMySQL | Object-Relational Mapping with connection pooling. |
| **RAG & Vector Store** | LangChain + FAISS | Fast in-memory similarity search with local disk persistence. |
| **LLM & Embeddings** | Google Gemini API / Local Fallback | Modern, cost-effective generative model (`gemini-1.5-flash`). |
| **Frontend UI** | Streamlit | Clean, interactive Python dashboard. |
| **Testing** | Pytest + HTTPX | Comprehensive integration and unit testing. |

---

## 5. Project Directory Structure

```text
ai_customer_support/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Environment variables and settings
│   ├── main.py                   # FastAPI app entry point & lifespan
│   ├── api/
│   │   ├── routes.py             # Root, /health, /customers, /ask endpoints
│   │   ├── ticket_routes.py      # /tickets endpoints
│   │   └── conversation_routes.py# /conversations endpoints
│   ├── database/
│   │   ├── connection.py         # SQLAlchemy engine and session dependency
│   │   ├── models.py             # ORM models (Customer, Ticket, Conversation)
│   │   └── crud.py               # Database CRUD operations
│   ├── rag/
│   │   ├── document_loader.py    # Markdown policy loader & text chunker
│   │   ├── embeddings.py         # Google Gemini & offline fallback embeddings
│   │   ├── vector_store.py       # FAISS index creation, persistence & retrieval
│   │   └── qa.py                 # RAG orchestration, prompt & classification
│   ├── schemas/
│   │   ├── support.py            # Pydantic models for Q&A and conversations
│   │   └── ticket.py             # Pydantic models for tickets
│   └── services/
│       ├── support_service.py    # RAG pipeline + conversation logging logic
│       └── ticket_service.py     # Ticket creation and validation logic
│
├── data/
│   ├── knowledge_base/           # Markdown policy documents
│   │   ├── delivery_policy.md
│   │   ├── refund_policy.md
│   │   ├── payment_policy.md
│   │   ├── cancellation_policy.md
│   │   └── account_faq.md
│   └── faiss_index/              # Persisted vector index (generated)
│
├── database/
│   ├── schema.sql                # Raw SQL database creation script
│   └── seed.py                   # Database seeding script for demo customers
│
├── scripts/
│   └── ingest_documents.py       # Offline vector indexing script
│
├── streamlit_app/
│   └── app.py                    # Multi-page Streamlit web interface
│
├── tests/
│   ├── test_api.py               # FastAPI endpoint tests
│   ├── test_database.py          # MySQL and CRUD tests
│   └── test_rag.py               # RAG, chunking, and FAISS tests
│
├── .env.example                  # Template for environment configuration
├── .gitignore                    # Git ignore file
├── requirements.txt              # Pinned Python package dependencies
└── README.md                     # Documentation
```

---

## 6. Database Schema

The system uses three relational tables in the `ai_customer_support` database:

```sql
-- 1. Customers
CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Conversations
CREATE TABLE conversations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);

-- 3. Support Tickets
CREATE TABLE tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    issue TEXT NOT NULL,
    category ENUM('Payment', 'Delivery', 'Refund', 'Cancellation', 'Account', 'Other') DEFAULT 'Other',
    status ENUM('Open', 'In Progress', 'Resolved', 'Closed') DEFAULT 'Open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
);
```

---

## 7. Setup & Installation Guide

### Prerequisites
- Python 3.9 or higher
- MySQL Server (version 8.0 or compatible)

### Step 1: Clone or Navigate to the Repository
```bash
cd e:\ai_customer_support
```

### Step 2: Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Open `.env` and verify your MySQL credentials:
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=ai_customer_support

# Optional: Add your Google Gemini API Key for live AI generation
# (Free key available at https://aistudio.google.com/)
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash

BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
BACKEND_URL=http://127.0.0.1:8000
```
*(Note: If you do not have a Gemini API key yet, the application will automatically run in local offline demo mode with local embeddings!)*

### Step 5: Initialize and Seed MySQL Database
```bash
python database/seed.py
```
*Output: Creates tables and inserts 4 demo customers.*

### Step 6: Ingest Knowledge Base into FAISS
```bash
python scripts/ingest_documents.py
```
*Output: Loads 5 markdown policy documents, chunks them, and builds `data/faiss_index`.*

---

## 8. Running the Application

Open two terminal tabs:

### Terminal 1: Start FastAPI Backend
```bash
.\venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive API Documentation (Swagger UI): **http://127.0.0.1:8000/docs**
- Health Endpoint: **http://127.0.0.1:8000/health**

### Terminal 2: Start Streamlit Frontend
```bash
.\venv\Scripts\activate
streamlit run streamlit_app/app.py
```
- Streamlit Web Dashboard: **http://localhost:8501**

---

## 9. FastAPI Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API status and metadata. |
| `GET` | `/health` | Health checks for MySQL and FAISS. |
| `GET` | `/customers` | List all registered customers. |
| `POST` | `/customers` | Register a new customer profile. |
| `POST` | `/ask` | Ask a customer support question via RAG. |
| `POST` | `/tickets` | Create an escalated support ticket. |
| `GET` | `/tickets` | Retrieve all tickets (optional `?customer_id=1`). |
| `GET` | `/tickets/{ticket_id}` | Retrieve specific ticket details. |
| `GET` | `/conversations` | Retrieve conversation history (optional `?customer_id=1`). |

---

## 10. Example Inquiries & Test Scenarios

Try entering these questions in the Streamlit UI or via API:

1. **Payment Issue:**
   - Inquiry: *"My payment was deducted from my bank but the order failed."*
   - Detected Category: `Payment`
   - Retrieved Source: `payment_policy.md`
2. **Delivery Inquiry:**
   - Inquiry: *"How long does delivery take to regional areas?"*
   - Detected Category: `Delivery`
   - Retrieved Source: `delivery_policy.md`
3. **Refund Question:**
   - Inquiry: *"What is your return policy for broken or defective items?"*
   - Detected Category: `Refund`
   - Retrieved Source: `refund_policy.md`
4. **Order Cancellation:**
   - Inquiry: *"Can I cancel my order after it has shipped?"*
   - Detected Category: `Cancellation`
   - Retrieved Source: `cancellation_policy.md`
5. **Account Management:**
   - Inquiry: *"How can I change my email address or password?"*
   - Detected Category: `Account`
   - Retrieved Source: `account_faq.md`

---

## 11. Running the Automated Test Suite

The test suite covers database operations, the RAG retrieval pipeline, and all FastAPI endpoints:

```bash
pytest -v
```

All 18 tests will execute and validate:
- MySQL connectivity and foreign key cascading.
- Document loading, text splitting, and FAISS index similarity matching.
- Category classification across all 6 business categories.
- FastAPI endpoint responses and error validations (400, 404, 422).

---

## 12. Interview Talking Points (CSE Student Guide)

When presenting this project in a technical interview, highlight:
1. **Why RAG instead of Fine-Tuning?** Company policies change frequently (e.g., return windows, holiday delivery times). RAG allows updating Markdown documents without expensive model retraining.
2. **Chunking Strategy:** `RecursiveCharacterTextSplitter` with 500 characters and 80 overlap preserves natural paragraph boundaries and markdown headers (`##`), preventing split sentences.
3. **Database Normalization:** Relational design separating customers from conversations and tickets prevents data duplication and enforces relational integrity via foreign keys.
4. **Error Handling & Architecture:** Clean separation of concerns between API routers (`app/api`), business logic (`app/services`), data access (`app/database`), and AI retrieval (`app/rag`).
5. **Graceful Fallbacks:** The system runs in full offline demo mode if an external API key is absent, ensuring deterministic testability.

---

## 13. Future Improvements

- Add email notification webhooks when tickets are resolved.
- Implement session-based chat memory using Redis or SQL conversation threading.
- Add admin authentication for support staff to update ticket statuses (`In Progress` -> `Resolved`).
