# NovaStore — AI Customer Support System

An enterprise-ready, intelligent customer support and ticket management platform built with **FastAPI**, **LangChain**, **FAISS**, **MySQL**, and **Streamlit**.

NovaStore automates first-line e-commerce customer support. Instead of support agents manually handling repetitive inquiries about shipping times, refund terms, payment failures, and order cancellations, the system uses **Retrieval-Augmented Generation (RAG)** to provide instant, accurate answers strictly grounded in official store policy documents.

When an inquiry cannot be resolved automatically, customers can escalate the issue directly into a tracked support ticket, while support agents review, analyze, and update ticket statuses through a live management dashboard.

---

## Architecture & System Flow

```
                      +-----------------------------+
                      |     Streamlit Frontend      |
                      |  (User Chat & Dashboard UI) |
                      +--------------+--------------+
                                     |
                             REST API (JSON)
                                     |
                      +--------------v--------------+
                      |       FastAPI Backend       |
                      |   (Validation, Auth, CORS)  |
                      +-------+--------------+------+
                              |              |
           +------------------+              +------------------+
           |                                                    |
+----------v-----------+                             +----------v-----------+
|    RAG / QA Engine   |                             |   MySQL Relational   |
|   (LangChain+FAISS)  |                             |       Database       |
+----------+-----------+                             +----------+-----------+
| Semantic Policy Search                             | Customers & Profiles |
| HuggingFace Embeddings                             | Conversation History |
| Gemini / Demo Engine                               | Tickets & Statuses   |
+----------------------+                             +----------------------+
```

### Request Flow
1. **Inquiry:** Customer selects a customer profile and submits a policy question.
2. **Retrieval:** FAISS vector store searches chunked policy documents (`data/knowledge_base/*.md`) for top matching sections.
3. **Generation:** If Google Gemini is configured (`LLM_API_KEY`), the model synthesizes a grounded answer with citations. If absent or quota-exhausted, the resilient engine falls back seamlessly to offline policy synthesis.
4. **Persistence:** The query, grounded answer, category, and timestamp are stored in MySQL (`conversations` table).
5. **Escalation:** The customer can escalate unresolved questions directly into a support ticket with pre-filled context.
6. **Agent Management:** Support staff track KPIs, filter open/resolved cases, and securely update ticket statuses.

---

## Key Features

- **Grounded Policy Question Answering:** Semantic search across shipping, refund, payment, and cancellation policies to eliminate hallucinations.
- **Resilient AI Pipeline:** Automatic fallback from Gemini generative responses to local policy-grounded templates if the API key is omitted, invalid, or rate-limited.
- **Automatic Categorization:** Inquiries are classified into *Delivery*, *Payment*, *Refund*, *Cancellation*, *Account*, or *Other*.
- **Conversation Auditing:** Complete inquiry and answer history persisted in MySQL for compliance and auditing.
- **Customer Escalation:** Turn questions into formal support tickets (`Open`, `In Progress`, `Resolved`, `Closed`) with one click.
- **Role-Gated Ticket Updates:** Ticket status changes are protected via `ADMIN_API_KEY` and the `X-Admin-Key` HTTP header.
- **Comprehensive Analytics Dashboard:** Visualizes live KPIs, ticket category breakdowns, resolution rates, and inquiry activity trends.
- **Multi-Customer Profile Switching:** Switch between simulated customer accounts to test personalized interaction history.
- **Cloud-Ready Observability:** Dedicated `/health`, `/health/live`, and `/health/ready` probe endpoints for cloud container orchestrators.

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.9+ (3.10/3.11 recommended) | Core application runtime |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2 | High-performance asynchronous REST API |
| **Frontend UI** | Streamlit | Reactive web interface and analytics dashboard |
| **Vector Search** | FAISS (`faiss-cpu`), LangChain | In-memory semantic vector indexing and retrieval |
| **Embeddings** | HuggingFace MiniLM (`all-MiniLM-L6-v2`) | Local offline text embedding generation |
| **LLM Engine** | Google Gemini (`gemini-1.5-flash`) | Contextual generative responses with citations |
| **Database & ORM** | MySQL 8.x, SQLAlchemy, PyMySQL | Relational storage for customers, logs, and tickets |
| **Containerization** | Docker, Docker Compose | Multi-container reproducible deployment |
| **Testing** | Pytest, FastAPI TestClient, Streamlit AppTest | End-to-end automated test suite (59 tests) |

---

## Local Setup & Quickstart

### Prerequisites
- Python 3.9 or higher (Python 3.10 or 3.11 recommended)
- MySQL Server 8.x running locally (default port: `3306`)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/anushkakulshrestha006-max/ai-customer-support-system.git
cd ai-customer-support-system
```

### 2. Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Activate on Linux / macOS:
# source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to create your local `.env`:
```powershell
# Windows PowerShell:
Copy-Item .env.example .env

# Linux / macOS:
# cp .env.example .env
```

Open `.env` in your editor and configure your local settings:
```env
# Runtime Environment
ENVIRONMENT=development

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=ai_customer_support

# Gemini API Key (Optional — system runs offline fallback if empty)
LLM_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-1.5-flash

# Backend Network Settings
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8001
BACKEND_URL=http://127.0.0.1:8001

# CORS Allowed Origins
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501

# Admin Security Key (Optional for local testing; protects ticket status changes)
ADMIN_API_KEY=local-admin-dev-key
```

### 5. Initialize Knowledge Base & Database
Run the setup utilities to index store policies and initialize MySQL tables:
```bash
# Build the FAISS vector index from markdown policy documents:
python scripts/ingest_documents.py

# Initialize database tables and seed demo customers (Alice, Bob, Carol, David):
python scripts/init_database.py --seed
```

> **Note:** `scripts/init_database.py` is non-destructive and idempotent. Running it will create tables if they do not exist and seed default customer profiles only if the customer table is empty.

### 6. Run the Application
Open two separate terminal windows (with your virtual environment activated in both):

**Terminal 1 — FastAPI Backend:**
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
- Interactive Swagger API Documentation: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- Health Check: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

**Terminal 2 — Streamlit Frontend:**
```bash
streamlit run streamlit_app/app.py
```
- Web Application: [http://localhost:8501](http://localhost:8501)

---

## Environment Variables Reference

| Variable Name | Required | Default | Description |
|---|---|---|---|
| `ENVIRONMENT` | No | `development` | `development` or `production`. Disables verbose internal errors in production. |
| `PORT` | Cloud | `8001` | Server port injected by cloud hosting providers (Render, Railway, Heroku). |
| `BACKEND_HOST` | No | `127.0.0.1` | Host to bind backend server. Auto-switches to `0.0.0.0` if `PORT` is set. |
| `BACKEND_PORT` | No | `8001` | Fallback port if `PORT` is not set. |
| `BACKEND_URL` | Yes (Frontend) | `http://127.0.0.1:8001` | Base URL used by Streamlit to communicate with FastAPI. |
| `DATABASE_URL` / `MYSQL_URL` | Cloud | `None` | Full SQLAlchemy connection string for cloud DBs (e.g. `mysql+pymysql://user:pass@host:3306/db`). |
| `MYSQL_HOST` | Local | `localhost` | MySQL host address (used when `DATABASE_URL` is not set). |
| `MYSQL_PORT` | Local | `3306` | MySQL port number. |
| `MYSQL_USER` | Local | `root` | MySQL username. Handled with automatic URL encoding for special characters. |
| `MYSQL_PASSWORD` | Local | `""` | MySQL user password. Handled with automatic URL encoding for special characters. |
| `MYSQL_DATABASE` | Local | `ai_customer_support` | Name of MySQL database schema. |
| `DB_POOL_SIZE` | No | `5` | SQLAlchemy connection pool size. |
| `DB_MAX_OVERFLOW` | No | `10` | Maximum overflow connections allowed beyond pool size. |
| `DB_POOL_TIMEOUT` | No | `30` | Seconds to wait before timing out on connection pool checkout. |
| `DB_POOL_RECYCLE` | No | `1800` | Seconds before recycling idle MySQL connections (prevents timeout dropouts). |
| `LLM_API_KEY` | No | `""` | Google Gemini API key. If omitted, system activates local policy fallback. |
| `LLM_MODEL` | No | `gemini-1.5-flash` | Gemini model name. |
| `CORS_ORIGINS` | No | `http://localhost:8501,...` | Comma-separated list of allowed browser origins for FastAPI CORS middleware. |
| `ADMIN_API_KEY` | Optional | `""` | Secret token required to change ticket status (`X-Admin-Key` header). |

---

## Health Probes & Monitoring

The backend exposes three health endpoints designed for cloud platforms, uptime monitors, and container orchestrators:

- **`GET /health`** — General service health overview. Returns `status: "healthy"` or `"degraded"`, uptime, environment, and statuses for Database and Knowledge Base.
- **`GET /health/live`** — Kubernetes/PaaS Liveness probe. Always returns HTTP 200 while process is running:
  ```json
  {"status": "alive"}
  ```
- **`GET /health/ready`** — Kubernetes/PaaS Readiness probe. Checks connectivity to MySQL and verifies that the FAISS index files exist on disk:
  - Returns **HTTP 200 OK** when all components are operational:
    ```json
    {
      "status": "ready",
      "database": "connected",
      "knowledge_base": "indexed"
    }
    ```
  - Returns **HTTP 503 Service Unavailable** if MySQL is unreachable or FAISS index is missing.

---

## Cloud Deployment Guide

The recommended architecture deploys the **FastAPI Backend** and **Streamlit Frontend** as two separate web services, connected to a managed cloud MySQL database.

```
                      +-----------------------------+
                      | Streamlit Community Cloud / |
                      |    Frontend Web Service     |
                      +--------------+--------------+
                                     |
                          HTTPS (BACKEND_URL)
                                     |
                      +--------------v--------------+
                      |    FastAPI Web Service      |
                      |      (Render / Railway)     |
                      +-------+--------------+------+
                              |              |
                      Local FAISS Files   Managed MySQL
                      (built in Docker)  (Aiven / PlanetScale)
```

### Option A: Deploy to Render using `render.yaml`

The repository includes a ready-to-use Render Blueprint specification ([render.yaml](render.yaml)).

1. Push your code to GitHub (ensure `.env` remains gitignored).
2. Log into [Render.com](https://render.com) and create a managed MySQL instance (or use a free tier MySQL from [Aiven](https://aiven.io)).
3. Navigate to **Blueprints** > **New Blueprint Instance**.
4. Connect your GitHub repository.
5. In Render's dashboard, configure the required environment variables:
   - **For Backend (`novastore-api`):**
     - `DATABASE_URL`: Your full cloud MySQL connection string:
       `mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>?ssl_mode=REQUIRED`
     - `LLM_API_KEY`: Your Google Gemini API Key.
     - `ADMIN_API_KEY`: A secure random string (e.g. `openssl rand -hex 16`).
     - `CORS_ORIGINS`: Comma-separated URL of your deployed frontend (e.g. `https://novastore-ui.onrender.com`).
   - **For Frontend (`novastore-ui`):**
     - `BACKEND_URL`: The HTTPS URL of your deployed backend service (e.g. `https://novastore-api.onrender.com`).
     - `ADMIN_API_KEY`: Matching the admin key set on the backend.
6. Deploy the blueprint. Render automatically builds the FAISS index during the build phase (`python scripts/ingest_documents.py`) and launches both services.

---

### Option B: Streamlit Community Cloud (Frontend) + Render/Railway (Backend)

For zero-cost hosting:
1. **Database:** Create a free MySQL database on [Aiven.io](https://aiven.io).
2. **Backend:** Deploy the FastAPI backend on [Render.com](https://render.com) as a Docker or Python Web Service:
   - **Build Command:** `pip install -r requirements.txt && python scripts/ingest_documents.py && python scripts/init_database.py --seed`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Set environment variables (`DATABASE_URL`, `LLM_API_KEY`, `ADMIN_API_KEY`, `CORS_ORIGINS`).
3. **Frontend:** Deploy to [Streamlit Community Cloud](https://share.streamlit.io):
   - **Repository:** `your-username/ai-customer-support-system`
   - **Main file path:** `streamlit_app/app.py`
   - In **App Settings** > **Secrets**, enter your configuration using the template from [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example):
     ```toml
     BACKEND_URL = "https://your-backend-api.onrender.com"
     ADMIN_API_KEY = "your-admin-key"
     ```

---

### Option C: Docker & Docker Compose (Containerized Local or VPS)

A complete multi-container setup including MySQL 8.0, the FastAPI backend, and the Streamlit frontend is provided in [docker-compose.yml](docker-compose.yml).

1. Copy `.env.example` to `.env` and adjust passwords if needed.
2. Build and launch all three containers:
   ```bash
   docker-compose up --build -d
   ```
3. Initialize the database and seed initial customers inside the running backend container:
   ```bash
   docker-compose exec backend python scripts/init_database.py --seed
   ```
4. Access the applications:
   - Streamlit Frontend: [http://localhost:8501](http://localhost:8501)
   - FastAPI Backend Docs: [http://localhost:8001/docs](http://localhost:8001/docs)
5. Stop the containers:
   ```bash
   docker-compose down
   ```

---

## Deployment Verification Checklist

Once deployed to your hosting environment, perform this verification sequence:

- [ ] **Liveness Check:** Open `https://<backend-url>/health/live` in your browser. Verify it responds with `{"status": "alive"}`.
- [ ] **Readiness Check:** Open `https://<backend-url>/health/ready`. Verify it returns HTTP 200 with `database: "connected"` and `knowledge_base: "indexed"`.
- [ ] **Frontend Connection:** Open the Streamlit frontend URL. Confirm that the top metric cards load real numbers without connection error banners.
- [ ] **Customer Profile Switching:** Change the active customer in the sidebar. Verify the greeting updates.
- [ ] **Knowledge Base Query:** Navigate to **Ask Support**, submit a question (e.g., *"What is your return window?"*), and verify that an answer with policy citations appears.
- [ ] **Conversation History:** Navigate to **Conversation History** and confirm your question was logged.
- [ ] **Ticket Escalation:** On the Ask Support page, click **Escalate to Support Ticket**. Fill in the subject and submit. Verify success confirmation.
- [ ] **Ticket Management:** Navigate to **Support Tickets**, find your ticket, change its status from `Open` to `In Progress`, and click **Update Status**. Verify that the change persists upon refresh.

---

## Security Architecture & Considerations

### Implemented Protections
- **No Hardcoded Credentials:** All database credentials, external API keys, and internal secrets are loaded strictly from the environment or secrets store.
- **Safe Production Validation:** `settings.validate_production_settings()` verifies required variables without printing sensitive values to application logs.
- **Strict Request Payload Limits:** Pydantic schemas enforce length bounds (`AskRequest.question` ≤ 2,000 characters; `TicketCreate.description` ≤ 3,000 characters) to mitigate denial-of-service and payload-stuffing attacks.
- **Exception Shielding:** Unhandled backend exceptions return a standardized error message to clients rather than exposing internal file paths or stack traces.
- **Role-Protected Ticket Statuses:** The `PATCH /tickets/{id}/status` endpoint requires an `X-Admin-Key` header matching `ADMIN_API_KEY`.
- **CORS Allowlist:** Origin reflection is restricted to configured frontend domains rather than wildcard `*`.
- **URL-Encoded Database Credentials:** Special characters in database passwords (such as `@`, `!`, `#`, `/`) are properly escaped using `urllib.parse.quote_plus`.

### Student Portfolio Context & Known Limitations
- **Read Endpoints:** For portfolio presentation and demonstrability, read endpoints (`/customers`, `/conversations`, `/tickets`) do not enforce user authentication.
- **Python 3.9 Runtime Notice:** Python 3.9 has reached end-of-life. Certain underlying packages (`langchain-google-genai`, `google.generativeai`) emit deprecation warnings. Upgrading the deployment environment to Python 3.10 or 3.11 is recommended for production installations.
- **Knowledge Base Persistence:** The FAISS index is stored locally on the container filesystem (`data/faiss_index/`). On ephemeral container platforms (like basic free-tier instances), the index is automatically rebuilt at startup or container build time via `scripts/ingest_documents.py`.

---

## Troubleshooting & Common Issues

### 1. `503 Service Unavailable` on `/health/ready`
- **Cause:** Backend cannot connect to the MySQL instance, or FAISS index files are missing.
- **Fix:**
  - Check your `DATABASE_URL` or individual `MYSQL_*` environment variables.
  - If connecting to cloud MySQL (Aiven, DigitalOcean, PlanetScale), verify SSL configuration: append `?ssl_mode=REQUIRED` to your connection string.
  - If FAISS is unindexed, run `python scripts/ingest_documents.py`.

### 2. Frontend shows `Failed to connect to backend`
- **Cause:** Streamlit frontend has an incorrect `BACKEND_URL` or the backend service is spinning down on a free-tier sleep cycle.
- **Fix:**
  - Verify that `BACKEND_URL` in your Streamlit secrets/environment matches the backend URL exactly (e.g. `https://novastore-api.onrender.com` without a trailing slash).
  - Free tier instances on Render or Railway may take 30–60 seconds to spin up from an idle state.

### 3. `403 Forbidden` when updating ticket status
- **Cause:** `ADMIN_API_KEY` is configured on the backend, but the frontend request did not include a valid matching key.
- **Fix:** Ensure `ADMIN_API_KEY` in Streamlit secrets matches the backend's `ADMIN_API_KEY`. If left empty in development, admin checks are bypassed.

### 4. Database Password with Special Characters Fails
- **Cause:** Raw passwords containing symbols like `@`, `:`, `/` break URL connection parsing.
- **Fix:** The application automatically encodes `MYSQL_USER` and `MYSQL_PASSWORD` via `quote_plus`. If using `DATABASE_URL` directly, ensure you URL-encode the password component.

---

## Automated Testing

The project includes an automated test suite covering:
- Configuration parsing, URL encoding, and production validation
- Health, liveness, and readiness probe responses
- FAISS vector store loading and document ingestion
- Google Gemini integration and resilient offline fallback
- Database connection, models, CRUD operations, and transaction integrity
- API endpoints for conversations, inquiries, and ticket management
- Admin authorization on ticket status updates
- Streamlit UI component rendering and navigation

To run the complete test suite:
```powershell
.\venv\Scripts\pytest -v
```

---

## License

This project is licensed under the MIT License — feel free to use, adapt, and build upon this codebase for educational and portfolio purposes.