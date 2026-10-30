"""
Production Readiness & Cloud Deployment Test Suite.
Validates:
1. Environment configuration, port reading, and secret handling.
2. Health (/health), liveness (/health/live), and readiness (/health/ready) probes.
3. Sanitized error responses without stack traces or credential leaks.
4. Ticket status authorization protection via X-Admin-Key.
5. Grounded RAG fallback behavior when Gemini is unconfigured or fails.
6. Non-destructive schema initialization and data persistence.
7. Frontend cloud backend URL resolution.
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.main import app
from app.database.connection import SessionLocal, init_db, engine
from app.database import crud, models
from app.rag.vector_store import build_and_save_vector_store, load_vector_store
from app.rag.qa import answer_customer_question, generate_policy_answer
from app.services.response_formatter import is_test_record
from streamlit_app.app import _resolve_config_value

client = TestClient(app)


# ==========================================
# 1. CONFIGURATION & SECRETS TESTS
# ==========================================

def test_safe_local_development_defaults():
    """Verify safe defaults for local development."""
    custom_settings = Settings()
    assert custom_settings.BACKEND_PORT in [8001, int(os.getenv("PORT", 8001))]
    assert "mysql+pymysql://" in custom_settings.DATABASE_URL
    assert isinstance(custom_settings.CORS_ORIGINS, list)
    assert len(custom_settings.CORS_ORIGINS) > 0


def test_port_environment_variable_precedence():
    """Verify that cloud provider PORT takes precedence over default BACKEND_PORT."""
    with patch.dict(os.environ, {"PORT": "9000", "BACKEND_PORT": "8001"}):
        s = Settings()
        assert s.BACKEND_PORT == 9000
        assert s.BACKEND_HOST == "0.0.0.0"


def test_database_url_standardization():
    """Verify mysql:// is automatically rewritten to mysql+pymysql://."""
    with patch.dict(os.environ, {"DATABASE_URL": "mysql://user:pass@remote-host:3306/db"}):
        s = Settings()
        assert s.DATABASE_URL == "mysql+pymysql://user:pass@remote-host:3306/db"


def test_database_credentials_url_encoding():
    """Verify special characters in passwords and usernames are safely URL-encoded."""
    with patch.dict(os.environ, {
        "DATABASE_URL": "",
        "MYSQL_USER": "app_user",
        "MYSQL_PASSWORD": "p@ssword#123:special/chars",
        "MYSQL_HOST": "db.cloud.internal",
        "MYSQL_PORT": "3306",
        "MYSQL_DATABASE": "support_db",
    }):
        s = Settings()
        assert "p%40ssword%23123%3Aspecial%2Fchars" in s.DATABASE_URL
        assert "@db.cloud.internal:3306/support_db" in s.DATABASE_URL


def test_railway_mysql_environment_resolution():
    """Verify Railway environment variables (MYSQL_PRIVATE_URL and MYSQLHOST format) are parsed."""
    # 1. Test MYSQL_PRIVATE_URL
    with patch.dict(os.environ, {
        "DATABASE_URL": "",
        "MYSQL_URL": "",
        "MYSQL_PRIVATE_URL": "mysql://root:secret@mysql.railway.internal:3306/railway",
    }):
        s = Settings()
        assert s.DATABASE_URL == "mysql+pymysql://root:secret@mysql.railway.internal:3306/railway"

    # 2. Test Railway individual variables (MYSQLHOST, MYSQLUSER, etc.)
    with patch.dict(os.environ, {
        "DATABASE_URL": "",
        "MYSQL_URL": "",
        "MYSQL_PRIVATE_URL": "",
        "MYSQL_HOST": "",
        "MYSQL_USER": "",
        "MYSQL_PASSWORD": "",
        "MYSQL_DATABASE": "",
        "MYSQLHOST": "mysql.railway.internal",
        "MYSQLUSER": "railway_user",
        "MYSQLPASSWORD": "railway_password",
        "MYSQLPORT": "3306",
        "MYSQLDATABASE": "railway",
    }):
        s = Settings()
        assert "@mysql.railway.internal:3306/railway" in s.DATABASE_URL
        assert "railway_user" in s.DATABASE_URL



def test_production_settings_validation_without_secret_leak():
    """Verify production validator detects default root credentials without leaking secrets."""
    with patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "root",
        "BACKEND_URL": "http://127.0.0.1:8001",
    }):
        s = Settings()
        issues = s.validate_production_settings()
        assert len(issues) >= 2
        # Ensure no actual password is leaked in the message
        for issue in issues:
            assert "p@ssword" not in issue
            assert "password detected" in issue or "root" in issue or "localhost" in issue or "ADMIN_API_KEY" in issue


def test_cors_origins_parsing():
    """Verify comma-separated origins are parsed cleanly."""
    with patch.dict(os.environ, {"CORS_ORIGINS": "https://app.streamlit.app, https://custom.domain.com"}):
        s = Settings()
        assert "https://app.streamlit.app" in s.CORS_ORIGINS
        assert "https://custom.domain.com" in s.CORS_ORIGINS


# ==========================================
# 2. BACKEND HEALTH & PROBE TESTS
# ==========================================

def test_health_liveness_probe():
    """Verify /health/live returns HTTP 200 alive."""
    res = client.get("/health/live")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert "version" in data


def test_health_readiness_probe():
    """Verify /health/ready returns service readiness status."""
    res = client.get("/health/ready")
    assert res.status_code in [200, 503]
    data = res.json()
    assert "database" in data
    assert "vector_store" in data


def test_health_sanitized_no_credential_leak():
    """Verify /health does not expose credentials, hosts, or raw connection strings."""
    res = client.get("/health")
    assert res.status_code == 200
    content_str = res.text.lower()
    assert "password" not in content_str
    assert "mysql+pymysql" not in content_str
    assert "@localhost" not in content_str


# ==========================================
# 3. SECURITY & AUTHORIZATION TESTS
# ==========================================

def test_ticket_status_authorization_enforced():
    """Verify ticket status update requires X-Admin-Key when ADMIN_API_KEY is configured."""
    cust_res = client.get("/customers")
    cust_id = cust_res.json()[0]["id"]
    t_res = client.post("/tickets", json={"customer_id": cust_id, "issue": "Auth test ticket", "category": "Other"})
    ticket_id = t_res.json()["id"]

    # Temporarily set ADMIN_API_KEY on the app's settings
    from app.config import settings
    orig_key = settings.ADMIN_API_KEY
    try:
        settings.ADMIN_API_KEY = "test-secret-admin-key"

        # 1. Without header -> 401 Unauthorized
        unauth_res = client.patch(f"/tickets/{ticket_id}/status", json={"status": "In Progress"})
        assert unauth_res.status_code == 401
        assert "Admin access required" in unauth_res.json()["detail"]

        # 2. With wrong header -> 401 Unauthorized
        bad_res = client.patch(
            f"/tickets/{ticket_id}/status",
            json={"status": "In Progress"},
            headers={"X-Admin-Key": "wrong-key"},
        )
        assert bad_res.status_code == 401

        # 3. With correct header -> 200 OK
        ok_res = client.patch(
            f"/tickets/{ticket_id}/status",
            json={"status": "In Progress"},
            headers={"X-Admin-Key": "test-secret-admin-key"},
        )
        assert ok_res.status_code == 200
        assert ok_res.json()["status"] == "In Progress"
    finally:
        settings.ADMIN_API_KEY = orig_key


def test_ticket_status_production_mode_requires_admin_key():
    """Verify that in production mode, missing or empty ADMIN_API_KEY does NOT bypass authorization."""
    cust_res = client.get("/customers")
    cust_id = cust_res.json()[0]["id"]
    t_res = client.post("/tickets", json={"customer_id": cust_id, "issue": "Prod auth test ticket", "category": "Other"})
    ticket_id = t_res.json()["id"]

    from app.config import settings
    orig_env = settings.ENVIRONMENT
    orig_key = settings.ADMIN_API_KEY
    try:
        settings.ENVIRONMENT = "production"
        settings.ADMIN_API_KEY = ""  # Empty in production

        # In production with empty key, status update MUST return 401 Unauthorized
        res = client.patch(f"/tickets/{ticket_id}/status", json={"status": "Resolved"})
        assert res.status_code == 401
        assert "locked because ADMIN_API_KEY is not configured" in res.json()["detail"]
    finally:
        settings.ENVIRONMENT = orig_env
        settings.ADMIN_API_KEY = orig_key



# ==========================================
# 4. RAG & GEMINI FALLBACK BEHAVIOR
# ==========================================

def test_faiss_vector_store_build_and_load_in_temp_dir():
    """Verify FAISS index can be built from policy documents in a fresh directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "faiss_test"
        vs = build_and_save_vector_store(index_path=tmp_path)
        assert vs is not None
        assert (tmp_path / "index.faiss").exists()
        assert (tmp_path / "index.pkl").exists()

        # Reloading from disk
        loaded_vs = load_vector_store(index_path=tmp_path)
        assert loaded_vs is not None
        docs = loaded_vs.similarity_search("How long does delivery take?", k=2)
        assert len(docs) > 0


def test_grounded_policy_fallback_response_quality():
    """Verify policy fallback generates polite, factual answers without demo tags."""
    cat, answer, sources = answer_customer_question("What is your refund policy?")
    assert cat == "Refund"
    assert len(sources) > 0
    assert "[Demo Mode" not in answer
    assert "LLM_API_KEY" not in answer
    assert "cancellation_policy.md" not in answer
    assert "refund_policy.md" in sources


def test_gemini_api_failure_handled_gracefully():
    """Verify that an unexpected Gemini API exception triggers graceful fallback."""
    from app.config import settings
    orig_key = settings.LLM_API_KEY
    try:
        settings.LLM_API_KEY = "simulated_api_key"
        with patch("langchain_google_genai.ChatGoogleGenerativeAI.invoke", side_effect=RuntimeError("Quota exceeded")):
            cat, answer, sources = answer_customer_question("What payment methods are supported?")
            assert cat == "Payment"
            assert len(answer) > 20
            assert "payment_policy.md" in sources
    finally:
        settings.LLM_API_KEY = orig_key


# ==========================================
# 5. DATABASE PERSISTENCE & NON-DESTRUCTIVE INIT
# ==========================================

def test_init_db_is_idempotent_and_preserves_records():
    """Verify init_db() can be called repeatedly without dropping or truncating tables."""
    session = SessionLocal()
    try:
        cust = crud.get_customers(session, limit=1)[0]
        # Create a ticket
        ticket = crud.create_ticket(
            session,
            customer_id=cust.id,
            issue="Persistence test across multiple inits",
            category="Delivery",
            status="Open",
        )
        ticket_id = ticket.id

        # Re-run init_db multiple times
        init_db()
        init_db()

        # Verify the record is still present and unaltered
        re_fetched = crud.get_ticket_by_id(session, ticket_id)
        assert re_fetched is not None
        assert re_fetched.issue == "Persistence test across multiple inits"
    finally:
        session.close()


def test_test_record_detection_filters_synthetic_data():
    """Verify test-only records are properly recognized for exclusion."""
    assert is_test_record("[TEST] Can I cancel an order?", "Mock answer") is True
    assert is_test_record("Test Q from C1", "Answer for C1") is True
    assert is_test_record("How long does delivery take?", "Standard shipping takes 3-5 days") is False



# ==========================================
# 6. STREAMLIT FRONTEND CONFIGURATION
# ==========================================

def test_frontend_backend_url_resolution():
    """Verify Streamlit config resolver reads custom public URLs without defaulting to localhost."""
    with patch.dict(os.environ, {"BACKEND_URL": "https://api.novastore-support.com"}):
        resolved = _resolve_config_value("BACKEND_URL", "http://127.0.0.1:8001")
        assert resolved == "https://api.novastore-support.com"
