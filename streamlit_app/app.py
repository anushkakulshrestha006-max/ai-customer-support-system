"""
AI Customer Support System - Streamlit Web Interface
NovaStore Support: RAG-powered customer inquiries, ticket escalation, and support analytics.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
import requests
import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
load_dotenv(dotenv_path=BASE_DIR / ".env")

from app.services.response_formatter import (
    clean_conversation_record,
    clean_question,
    clean_answer,
    get_readable_source_title,
    is_test_record,
    SOURCE_TITLE_MAP,
)

# Configuration & Cloud Secret Handling
def _resolve_config_value(key: str, default: str = "") -> str:
    """Reads setting from Streamlit secrets (for cloud deployments) or environment."""
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            val = str(st.secrets[key]).strip()
            if val:
                return val
    except Exception:
        pass
    return os.getenv(key, default).strip()

BACKEND_URL = _resolve_config_value("BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")
ADMIN_API_KEY = _resolve_config_value("ADMIN_API_KEY", "")


# Page layout configuration
st.set_page_config(
    page_title="NovaStore Support — AI Customer Support",
    page_icon="🛍️",
    layout="wide",
)

# Aliases for backward compatibility
SOURCE_LABEL_MAP = SOURCE_TITLE_MAP
get_readable_source_label = get_readable_source_title

# ==========================================
# GLOBAL CSS — Dark sidebar, bordered cards, modern typography
# ==========================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Light workspace background */
    .stApp {
        background-color: #F1F5F9;
    }

    /* Dark sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        color: #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #CBD5E1 !important;
    }
    section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4 {
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: #1E293B !important;
    }
    section[data-testid="stSidebar"] .stAlert {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
    }

    /* Page titles */
    .page-title {
        font-size: 1.75rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 2px;
        line-height: 1.3;
    }
    .page-subtitle {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 20px;
        line-height: 1.5;
    }

    /* KPI metric card */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px 18px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .kpi-icon {
        font-size: 1.6rem;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 0.82rem;
        font-weight: 500;
        color: #64748B;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Panel / section cards */
    .panel-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }
    .panel-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 12px;
    }

    /* Bordered container override for st.container(border=True) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
        padding: 20px 24px !important;
        margin-bottom: 16px !important;
    }

    /* Category badge */
    .badge-category {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        background-color: #EEF2FF;
        color: #4338CA;
        font-weight: 600;
        font-size: 0.82rem;
    }

    /* Status badges */
    .badge-open { background-color: #FEF3C7; color: #92400E; padding: 3px 10px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; }
    .badge-in-progress { background-color: #DBEAFE; color: #1E40AF; padding: 3px 10px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; }
    .badge-resolved { background-color: #D1FAE5; color: #065F46; padding: 3px 10px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; }
    .badge-closed { background-color: #F1F5F9; color: #475569; padding: 3px 10px; border-radius: 9999px; font-size: 0.78rem; font-weight: 600; }

    /* Source tags */
    .source-tag {
        display: inline-block;
        background-color: #F8FAFC;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.82rem;
        color: #334155;
        margin-right: 8px;
        margin-top: 6px;
        font-weight: 500;
    }

    /* Conversation card typography */
    .card-meta {
        font-size: 0.83rem;
        color: #64748B;
        margin-bottom: 8px;
    }
    .section-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94A3B8;
        margin-top: 10px;
        margin-bottom: 4px;
    }
    .card-question {
        font-size: 1.0rem;
        font-weight: 600;
        color: #0F172A;
        line-height: 1.5;
        margin-bottom: 6px;
    }
    .sources-heading {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94A3B8;
        margin-top: 14px;
        margin-bottom: 4px;
    }

    /* Hide default Streamlit metric delta and clean metric display */
    div[data-testid="stMetric"] {
        background-color: transparent;
    }

    /* Sidebar status indicators */
    .sidebar-status {
        font-size: 0.82rem;
        padding: 4px 0;
    }
    .status-dot-green { color: #22C55E; }
    .status-dot-red { color: #EF4444; }
    .status-dot-yellow { color: #F59E0B; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def check_backend_health():
    """Checks if FastAPI backend is reachable and reports health metrics."""
    try:
        res = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if res.status_code == 200:
            return True, res.json()
        return False, None
    except Exception:
        return False, None



def get_customers():
    """Fetches customer list from FastAPI backend."""
    try:
        res = requests.get(f"{BACKEND_URL}/customers", timeout=4)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return []


def fetch_dashboard_data():
    """Fetches customers, conversations, and tickets for analytics."""
    customers = []
    conversations = []
    tickets = []
    errors = []

    try:
        res = requests.get(f"{BACKEND_URL}/customers", timeout=4)
        if res.status_code == 200:
            customers = res.json()
        else:
            errors.append(f"Failed to fetch customers (HTTP {res.status_code})")
    except Exception as e:
        errors.append(f"Error fetching customers: {e}")

    try:
        res = requests.get(
            f"{BACKEND_URL}/conversations",
            params={"limit": 100, "exclude_tests": True},
            timeout=5,
        )
        if res.status_code == 200:
            conversations = [
                c for c in res.json()
                if not (c.get("is_test") or is_test_record(c.get("question"), c.get("answer")))
            ]
        else:
            errors.append(f"Failed to fetch conversations (HTTP {res.status_code})")
    except Exception as e:
        errors.append(f"Error fetching conversations: {e}")

    try:
        res = requests.get(f"{BACKEND_URL}/tickets", params={"limit": 100}, timeout=5)
        if res.status_code == 200:
            tickets = res.json()
        else:
            errors.append(f"Failed to fetch tickets (HTTP {res.status_code})")
    except Exception as e:
        errors.append(f"Error fetching tickets: {e}")

    return customers, conversations, tickets, errors


def render_kpi_card(icon: str, value, label: str):
    """Renders a single KPI metric card with icon, value, and label."""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_status_badge(status_text: str) -> str:
    """Returns HTML for a styled status badge."""
    css_class = {
        "Open": "badge-open",
        "In Progress": "badge-in-progress",
        "Resolved": "badge-resolved",
        "Closed": "badge-closed",
    }.get(status_text, "badge-open")
    return f'<span class="{css_class}">{status_text}</span>'


# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.markdown("### NovaStore Support")

# Health check — result used by dashboard and other pages; not displayed in sidebar
is_online, health_info = check_backend_health()

# Customer Profile Selection
customers = get_customers()
selected_customer = None

if customers:
    cust_options = {f"{c['name']} ({c['email']})": c for c in customers}
    chosen_label = st.sidebar.selectbox("Active Customer Profile", list(cust_options.keys()))
    selected_customer = cust_options[chosen_label]
else:
    st.sidebar.warning("No customers found.")

st.sidebar.divider()

# Navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "Support Dashboard",
        "Ask Support (RAG)",
        "Conversation History",
        "Support Tickets",
        "Create Ticket",
    ],
)




# ==========================================
# PAGE 1: SUPPORT DASHBOARD
# ==========================================
if page == "Support Dashboard":
    # Header
    col_head, col_refresh = st.columns([5, 1])
    with col_head:
        st.markdown('<div class="page-title">Welcome to NovaStore Support</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="page-subtitle">AI-powered customer support dashboard — track inquiries, monitor tickets, and analyze support activity.</div>',
            unsafe_allow_html=True,
        )
    with col_refresh:
        st.write("")
        if st.button("Refresh", use_container_width=True, key="dash_refresh"):
            st.rerun()

    if not is_online:
        st.error("Unable to connect to the backend service. Please ensure the backend server is running.")
        st.stop()

    customers_data, conversations_data, tickets_data, fetch_errors = fetch_dashboard_data()

    if fetch_errors:
        for err_msg in fetch_errors:
            st.warning(f"{err_msg}")

    # Calculate KPI metrics
    total_customers = len(customers_data)
    total_questions = len(conversations_data)
    total_tickets = len(tickets_data)

    status_counts = {"Open": 0, "In Progress": 0, "Resolved": 0, "Closed": 0}
    category_counts = {
        "Payment": 0,
        "Delivery": 0,
        "Refund": 0,
        "Cancellation": 0,
        "Account": 0,
        "Other": 0,
    }

    for t in tickets_data:
        cat = t.get("category", "Other")
        if cat in category_counts:
            category_counts[cat] += 1
        else:
            category_counts["Other"] += 1

        stat = str(t.get("status", "Open")).strip()
        matched = False
        for expected in status_counts:
            if stat.lower() == expected.lower():
                status_counts[expected] += 1
                matched = True
                break
        if not matched:
            status_counts["Open"] += 1

    open_tickets = status_counts["Open"]
    resolved_tickets = status_counts["Resolved"]

    # KPI Cards Row
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card("👥", total_customers, "Total Customers")
    with k2:
        render_kpi_card("💬", total_questions, "Total Questions")
    with k3:
        render_kpi_card("🎫", total_tickets, "Total Tickets")
    with k4:
        render_kpi_card("📂", open_tickets, "Open Tickets")
    with k5:
        render_kpi_card("✅", resolved_tickets, "Resolved Tickets")

    st.write("")

    # Analytics Cards Row
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Tickets by Category</div>', unsafe_allow_html=True)
            if total_tickets == 0:
                st.info("No tickets recorded yet.")
            else:
                cat_chart_data = {
                    "Category": list(category_counts.keys()),
                    "Tickets": list(category_counts.values()),
                }
                st.bar_chart(cat_chart_data, x="Category", y="Tickets")

    with col_c2:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Tickets by Status</div>', unsafe_allow_html=True)
            if total_tickets == 0:
                st.info("No tickets recorded yet.")
            else:
                status_chart_data = {
                    "Status": list(status_counts.keys()),
                    "Tickets": list(status_counts.values()),
                }
                st.bar_chart(status_chart_data, x="Status", y="Tickets")

    # Recent Activity
    st.write("")
    with st.container(border=True):
        st.markdown('<div class="panel-title">Recent Support Activity</div>', unsafe_allow_html=True)

        if not conversations_data and not tickets_data:
            st.info("No activity recorded yet. Start by asking a question on the Ask Support page.")
        else:
            # Recent conversations
            if conversations_data:
                st.markdown("**Latest Conversations**")
                recent_convs = conversations_data[:5]
                for c in recent_convs:
                    q_text = clean_question(c.get("question", ""))
                    ts = str(c.get("created_at", "")).replace("T", " ")[:16]
                    cid = c.get("customer_id", "—")
                    st.markdown(f"- **{q_text[:80]}{'…' if len(q_text) > 80 else ''}** — Customer #{cid}, {ts}")

            # Recent tickets
            if tickets_data:
                st.markdown("**Latest Tickets**")
                recent_tickets = tickets_data[:5]
                for t in recent_tickets:
                    issue = t.get("issue", "")[:60]
                    ts = str(t.get("created_at", "")).replace("T", " ")[:16]
                    status_text = t.get("status", "Open")
                    st.markdown(f"- **{issue}{'…' if len(t.get('issue','')) > 60 else ''}** — {status_text}, {ts}")

    # Conversation Activity by Date
    if conversations_data:
        st.write("")
        with st.container(border=True):
            st.markdown('<div class="panel-title">Conversation Activity by Date</div>', unsafe_allow_html=True)
            date_counts = {}
            for c in conversations_data:
                raw_ts = c.get("created_at")
                if raw_ts:
                    d_str = str(raw_ts).replace("T", " ")[:10]
                    date_counts[d_str] = date_counts.get(d_str, 0) + 1

            if date_counts:
                sorted_dates = sorted(date_counts.keys())
                activity_data = {
                    "Date": sorted_dates,
                    "Questions": [date_counts[d] for d in sorted_dates],
                }
                st.bar_chart(activity_data, x="Date", y="Questions")


# ==========================================
# PAGE 2: ASK SUPPORT (RAG)
# ==========================================
elif page == "Ask Support (RAG)":
    st.markdown('<div class="page-title">AI Customer Support Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Ask any question about our store policies — delivery, payment, returns, cancellations, and more.</div>',
        unsafe_allow_html=True,
    )

    if not selected_customer:
        st.error("Please connect the backend and select a customer profile from the sidebar.")
        st.stop()

    # Two-column layout
    col_ask, col_response = st.columns([1, 1], gap="medium")

    with col_ask:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Ask the Assistant</div>', unsafe_allow_html=True)
            st.caption(f"Asking as **{selected_customer['name']}** ({selected_customer['email']})")

            # Example questions
            EXAMPLE_QUESTIONS = [
                ("📦 Standard delivery time?", "How long does standard delivery take?"),
                ("🔄 Refund policy?", "What is your refund policy?"),
                ("🚫 Cancel an order?", "How can I cancel an order?"),
                ("💳 Payment methods?", "What payment methods are supported?"),
            ]

            def select_example_question(text: str):
                st.session_state["question_input"] = text

            def clear_question_input():
                st.session_state["question_input"] = ""
                st.session_state.pop("last_result", None)
                st.session_state.pop("last_question", None)

            if "question_input" not in st.session_state:
                st.session_state["question_input"] = ""

            st.markdown("**Quick Examples**")
            eq_c1, eq_c2 = st.columns(2)
            for idx, (label, query_text) in enumerate(EXAMPLE_QUESTIONS):
                with [eq_c1, eq_c2][idx % 2]:
                    st.button(
                        label,
                        key=f"ex_btn_{idx}",
                        on_click=select_example_question,
                        args=(query_text,),
                        use_container_width=True,
                    )

            st.text_area(
                "Your question:",
                key="question_input",
                placeholder="Type your question here…",
                height=100,
            )

            btn_c1, btn_c2 = st.columns([1, 1])
            with btn_c1:
                submit_clicked = st.button("Ask Support", type="primary", use_container_width=True)
            with btn_c2:
                st.button("Clear", type="secondary", on_click=clear_question_input, use_container_width=True)

            if submit_clicked:
                user_question = st.session_state.get("question_input", "").strip()
                if not user_question:
                    st.warning("Please type a question or select an example before submitting.")
                else:
                    with st.spinner("Searching knowledge base…"):
                        try:
                            payload = {
                                "customer_id": selected_customer["id"],
                                "question": user_question,
                            }
                            resp = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=25)
                            if resp.status_code == 200:
                                data = resp.json()
                                st.session_state["last_question"] = user_question
                                st.session_state["last_result"] = data
                            else:
                                err = resp.json().get("detail", "Error processing inquiry")
                                st.error(f"Error ({resp.status_code}): {err}")
                        except Exception as ex:
                            st.error(f"Failed to communicate with backend: {ex}")

    with col_response:
        with st.container(border=True):
            st.markdown('<div class="panel-title">Support Response</div>', unsafe_allow_html=True)

            if "last_result" in st.session_state and st.session_state["last_result"]:
                res = st.session_state["last_result"]
                raw_ans = res.get("answer", "")
                raw_sources = res.get("sources", [])
                cleaned_res = clean_answer(raw_ans, sources=raw_sources)
                cat = res.get("category", "Other")

                # Category badge
                st.markdown(f'<span class="badge-category">Category: {cat}</span>', unsafe_allow_html=True)

                # Customer question
                if "last_question" in st.session_state and st.session_state["last_question"]:
                    st.markdown('<div class="section-label">Customer Question</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="card-question">{clean_question(st.session_state["last_question"])}</div>', unsafe_allow_html=True)
                    st.divider()

                # Answer
                st.markdown('<div class="section-label">Answer</div>', unsafe_allow_html=True)
                st.markdown(cleaned_res["answer"] if cleaned_res["answer"] else "_No response content._")

                # Policy references
                if cleaned_res["sources"]:
                    st.markdown('<div class="sources-heading">Policy References</div>', unsafe_allow_html=True)
                    sources_html = "".join([f'<span class="source-tag">📄 {get_readable_source_title(s)}</span>' for s in cleaned_res["sources"]])
                    st.markdown(sources_html, unsafe_allow_html=True)
            else:
                st.caption("Submit a question to see the AI-generated response here.")

    # Escalation
    if "last_result" in st.session_state and st.session_state["last_result"]:
        cat = st.session_state["last_result"].get("category", "Other")
        with st.expander("Need more help? Escalate to a support ticket", expanded=False):
            ticket_issue = st.text_area(
                "Describe your problem:",
                value=st.session_state.get("last_question", ""),
                key="rag_ticket_issue",
            )
            standard_categories = ["Payment", "Delivery", "Refund", "Cancellation", "Account", "Other"]
            ticket_cat = st.selectbox(
                "Ticket Category:",
                standard_categories,
                index=standard_categories.index(cat) if cat in standard_categories else 5,
                key="rag_ticket_cat",
            )
            if st.button("Submit Escalated Ticket", type="secondary"):
                if not ticket_issue.strip():
                    st.warning("Please provide an issue description.")
                else:
                    t_payload = {
                        "customer_id": selected_customer["id"],
                        "issue": ticket_issue.strip(),
                        "category": ticket_cat,
                    }
                    try:
                        t_res = requests.post(f"{BACKEND_URL}/tickets", json=t_payload, timeout=10)
                        if t_res.status_code == 201:
                            t_data = t_res.json()
                            st.success(f"Support ticket #{t_data['id']} created successfully.")
                        else:
                            st.error(f"Error creating ticket: {t_res.text}")
                    except Exception as e:
                        st.error(f"Request failed: {e}")


# ==========================================
# PAGE 3: CONVERSATION HISTORY
# ==========================================
elif page == "Conversation History":
    st.markdown('<div class="page-title">Conversation History</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Review previous customer support inquiries and AI-generated responses.</div>',
        unsafe_allow_html=True,
    )

    filter_cust = st.checkbox("Filter by active customer only", value=True)
    target_id = selected_customer["id"] if (filter_cust and selected_customer) else None

    params = {"limit": 50, "exclude_tests": True}
    if target_id is not None:
        params["customer_id"] = target_id

    try:
        res = requests.get(f"{BACKEND_URL}/conversations", params=params, timeout=5)
        if res.status_code == 200:
            raw_history = res.json()
            # Filter out synthetic unit test records to display genuine customer interactions only
            history = [
                item for item in raw_history
                if not (item.get("is_test") or is_test_record(item.get("question"), item.get("answer")))
            ]
            if not history:
                st.info("No conversations recorded yet. Ask a question on the Ask Support page to get started.")
            else:
                st.caption(f"Showing {len(history)} recent conversation(s)")
                for item in history:
                    # The backend already cleans via support_service, but we
                    # apply a second pass for any edge cases from older records
                    cleaned_item = clean_conversation_record(
                        item.get("question"),
                        item.get("answer"),
                        sources=item.get("sources"),
                    )
                    formatted_time = str(item.get("created_at", "")).replace("T", " ")[:19] if item.get("created_at") else ""
                    cust_id = item.get("customer_id", "—")

                    with st.container(border=True):
                        # Card header: timestamp + customer ID
                        meta_parts = []
                        if formatted_time:
                            meta_parts.append(f"<strong>Logged:</strong> {formatted_time}")
                        meta_parts.append(f"<strong>Customer ID:</strong> #{cust_id}")
                        st.markdown(
                            f'<div class="card-meta">{" &nbsp;|&nbsp; ".join(meta_parts)}</div>',
                            unsafe_allow_html=True,
                        )

                        # Customer Question
                        st.markdown('<div class="section-label">Customer Question</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="card-question">{cleaned_item["question"]}</div>', unsafe_allow_html=True)

                        st.divider()

                        # Support Response
                        st.markdown('<div class="section-label">Support Response</div>', unsafe_allow_html=True)
                        if cleaned_item["answer"]:
                            st.markdown(cleaned_item["answer"])
                        else:
                            st.caption("_No response content recorded._")

                        # Policy References
                        if cleaned_item["sources"]:
                            st.markdown('<div class="sources-heading">Policy References</div>', unsafe_allow_html=True)
                            sources_html = " ".join([f'<span class="source-tag">📄 {get_readable_source_title(s)}</span>' for s in cleaned_item["sources"]])
                            st.markdown(sources_html, unsafe_allow_html=True)
        else:
            st.error(f"Failed to fetch conversations ({res.status_code})")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")


# ==========================================
# PAGE 4: SUPPORT TICKETS
# ==========================================
elif page == "Support Tickets":
    st.markdown('<div class="page-title">Support Tickets</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Monitor and manage escalated support tickets.</div>',
        unsafe_allow_html=True,
    )

    filter_cust = st.checkbox("Filter by active customer only", value=False)
    target_id = selected_customer["id"] if (filter_cust and selected_customer) else None

    params = {"limit": 100}
    if target_id is not None:
        params["customer_id"] = target_id

    try:
        res = requests.get(f"{BACKEND_URL}/tickets", params=params, timeout=5)
        if res.status_code == 200:
            tickets = res.json()
            if not tickets:
                st.info("No support tickets on file. Tickets are created when inquiries need human follow-up.")
            else:
                with st.container(border=True):
                    st.markdown('<div class="panel-title">All Tickets</div>', unsafe_allow_html=True)
                    table_data = []
                    for t in tickets:
                        table_data.append({
                            "ID": f"#{t['id']}",
                            "Customer": t.get("customer_name") or f"Customer #{t['customer_id']}",
                            "Category": t["category"],
                            "Issue": t["issue"][:80] + ("…" if len(t["issue"]) > 80 else ""),
                            "Status": t["status"],
                            "Created": str(t.get("created_at", "")).replace("T", " ")[:16],
                        })
                    st.dataframe(table_data, use_container_width=True, hide_index=True)

                # Update ticket status
                st.write("")
                with st.container(border=True):
                    st.markdown('<div class="panel-title">Update Ticket Status</div>', unsafe_allow_html=True)

                    ticket_choices = {
                        f"#{t['id']} — [{t['status']}] {t['category']}: {t['issue'][:50]}": t
                        for t in tickets
                    }
                    selected_ticket_label = st.selectbox(
                        "Select Ticket:",
                        list(ticket_choices.keys()),
                        key="status_ticket_select",
                    )
                    chosen_t = ticket_choices[selected_ticket_label]

                    current_status = chosen_t.get("status", "Open")
                    status_options = ["Open", "In Progress", "Resolved", "Closed"]
                    default_idx = status_options.index(current_status) if current_status in status_options else 0

                    col_s1, col_s2 = st.columns([2, 1])
                    with col_s1:
                        new_status = st.selectbox("New Status:", status_options, index=default_idx, key="new_status_select")
                    with col_s2:
                        st.write("")
                        st.write("")
                        apply_clicked = st.button("Apply Change", type="primary", use_container_width=True)

                    with st.expander("Admin Authorization (required if enabled in production)", expanded=False):
                        entered_admin_key = st.text_input(
                            "Admin Secret Key:",
                            value="",
                            type="password",
                            help="Leave blank if pre-configured in server environment. Enter secret key if backend enforces ADMIN_API_KEY.",
                            key="admin_secret_key_input",
                        )

                    if apply_clicked:
                        if new_status == current_status:
                            st.info(f"Ticket #{chosen_t['id']} is already '{current_status}'.")
                        else:
                            try:
                                headers = {}
                                key_to_send = (entered_admin_key.strip() if entered_admin_key else "") or ADMIN_API_KEY
                                if key_to_send:
                                    headers["X-Admin-Key"] = key_to_send
                                patch_res = requests.patch(
                                    f"{BACKEND_URL}/tickets/{chosen_t['id']}/status",
                                    json={"status": new_status},
                                    headers=headers,
                                    timeout=8,
                                )
                                if patch_res.status_code == 200:
                                    st.success(f"Ticket #{chosen_t['id']} updated to '{new_status}'.")
                                    st.rerun()
                                else:
                                    err_detail = patch_res.json().get("detail", patch_res.text)
                                    st.error(f"Failed to update: {err_detail}")
                            except Exception as ex:
                                st.error(f"Connection error: {ex}")

        else:
            st.error(f"Failed to fetch tickets ({res.status_code})")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")


# ==========================================
# PAGE 5: CREATE TICKET
# ==========================================
elif page == "Create Ticket":
    st.markdown('<div class="page-title">Create Support Ticket</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Escalate an inquiry directly to the support team.</div>',
        unsafe_allow_html=True,
    )

    if not selected_customer:
        st.error("Please select a customer profile in the sidebar first.")
        st.stop()

    with st.container(border=True):
        st.markdown('<div class="panel-title">New Ticket</div>', unsafe_allow_html=True)

        with st.form("manual_ticket_form"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.text_input("Customer Name", value=selected_customer["name"], disabled=True)
            with col_f2:
                st.text_input("Customer Email", value=selected_customer["email"], disabled=True)

            cat = st.selectbox(
                "Category",
                ["Payment", "Delivery", "Refund", "Cancellation", "Account", "Other"],
            )
            issue_text = st.text_area(
                "Issue Description",
                placeholder="Describe the problem, include order IDs or error details…",
                height=120,
            )

            submitted = st.form_submit_button("Submit Ticket", type="primary")
            if submitted:
                if not issue_text.strip():
                    st.warning("Please enter an issue description.")
                else:
                    payload = {
                        "customer_id": selected_customer["id"],
                        "issue": issue_text.strip(),
                        "category": cat,
                    }
                    try:
                        res = requests.post(f"{BACKEND_URL}/tickets", json=payload, timeout=8)
                        if res.status_code == 201:
                            ticket = res.json()
                            st.success(f"Ticket #{ticket['id']} created successfully under **{cat}** category.")
                        else:
                            st.error(f"Failed to create ticket: {res.text}")
                    except Exception as ex:
                        st.error(f"Connection error: {ex}")
