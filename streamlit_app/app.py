"""
AI Customer Support System - Streamlit Web Interface
Connects to FastAPI backend to demonstrate RAG, Intent Classification, MySQL Logging, and Support Ticket Escalation.
"""
import os
import requests
import streamlit as st

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

# Page layout configuration
st.set_page_config(
    page_title="AI Customer Support System",
    page_icon="🛍️",
    layout="wide",
)

# Custom light styling for a clean, professional aesthetic
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge-category {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        background-color: #EEF2FF;
        color: #4F46E5;
        font-weight: 600;
        font-size: 0.85rem;
        margin-bottom: 0.75rem;
    }
    .source-tag {
        display: inline-block;
        background-color: #F1F5F9;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.82rem;
        color: #334155;
        margin-right: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def check_backend_health():
    """Checks if FastAPI backend is reachable and healthy."""
    try:
        res = requests.get(f"{BACKEND_URL}/health", timeout=3)
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


# ==========================================
# SIDEBAR
# ==========================================
st.sidebar.title("🛠️ NovaStore Support")

# Backend Health Status
is_online, health_info = check_backend_health()
if is_online:
    st.sidebar.success("● Backend: Connected (FastAPI)")
    if health_info and not health_info.get("api_key_configured"):
        st.sidebar.info("💡 Note: Running in local demo mode. Add LLM_API_KEY to .env for live Gemini generation.")
else:
    st.sidebar.error("● Backend: Offline (Cannot reach FastAPI)")
    st.sidebar.caption("Run: `uvicorn app.main:app --reload`")

st.sidebar.divider()

# Customer Profile Selection
customers = get_customers()
selected_customer = None

if customers:
    cust_options = {f"{c['name']} ({c['email']})": c for c in customers}
    chosen_label = st.sidebar.selectbox("Active Customer Profile", list(cust_options.keys()))
    selected_customer = cust_options[chosen_label]
else:
    st.sidebar.warning("No customers found. Please run seed script or start the backend.")

st.sidebar.divider()

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["Ask Support (RAG)", "Conversation History", "Support Tickets", "Create Ticket"],
)

st.sidebar.markdown("---")
st.sidebar.caption("Built with Python, FastAPI, MySQL, LangChain, FAISS & Streamlit.")


# ==========================================
# PAGE 1: ASK SUPPORT (RAG)
# ==========================================
if page == "Ask Support (RAG)":
    st.markdown('<div class="main-title">🛍️ AI Customer Support Assistant</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Ask any question regarding our store delivery, payment, return, or cancellation policies.</div>',
        unsafe_allow_html=True,
    )

    if not selected_customer:
        st.error("Please connect the backend and select a customer from the sidebar to continue.")
        st.stop()

    st.info(f"Logged in as **{selected_customer['name']}** (`{selected_customer['email']}`)")

    # Sample Quick Prompts
    st.write("**Quick Example Questions:**")
    quick_cols = st.columns(3)
    sample_q = ""
    if quick_cols[0].button("💳 Deducted payment but order failed"):
        sample_q = "My payment was deducted from my bank but the order failed."
    if quick_cols[1].button("📦 How long does delivery take?"):
        sample_q = "How long does standard delivery take to regional areas?"
    if quick_cols[2].button("🔄 What is the refund policy?"):
        sample_q = "What is your refund policy if an item arrives broken?"

    question = st.text_area(
        "Enter your support question:",
        value=sample_q if sample_q else "",
        placeholder="Type your question here (e.g., Can I cancel my order after dispatch?)...",
        height=100,
    )

    if st.button("Submit Question", type="primary", use_container_width=False):
        if not question.strip():
            st.warning("Please type a question before submitting.")
        else:
            with st.spinner("Searching knowledge base and generating answer..."):
                try:
                    payload = {
                        "customer_id": selected_customer["id"],
                        "question": question.strip(),
                    }
                    resp = requests.post(f"{BACKEND_URL}/ask", json=payload, timeout=25)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state["last_question"] = question.strip()
                        st.session_state["last_result"] = data
                    else:
                        err = resp.json().get("detail", "Error processing inquiry")
                        st.error(f"Error ({resp.status_code}): {err}")
                except Exception as ex:
                    st.error(f"Failed to communicate with FastAPI: {ex}")

    # Display Answer and Sources
    if "last_result" in st.session_state and st.session_state["last_result"]:
        res = st.session_state["last_result"]
        st.markdown("---")
        st.markdown("### Support Response")

        # Category Badge
        cat = res.get("category", "Other")
        st.markdown(f'<span class="badge-category">Category: {cat}</span>', unsafe_allow_html=True)

        # Answer
        st.markdown(f"**Answer:**\n\n{res.get('answer', '')}")

        # Sources Used
        sources = res.get("sources", [])
        if sources:
            st.markdown("**Knowledge Base Sources:**")
            sources_html = "".join([f'<span class="source-tag">📄 {s}</span>' for s in sources])
            st.markdown(sources_html, unsafe_allow_html=True)

        # Escalation Option: Create Ticket
        st.markdown("---")
        with st.expander("❓ Issue not resolved? Create a Support Ticket", expanded=False):
            st.write("Escalate this issue to a human support agent.")
            ticket_issue = st.text_area(
                "Describe your problem in detail:",
                value=st.session_state.get("last_question", ""),
                key="rag_ticket_issue",
            )
            ticket_cat = st.selectbox(
                "Ticket Category:",
                ["Payment", "Delivery", "Refund", "Cancellation", "Account", "Other"],
                index=["Payment", "Delivery", "Refund", "Cancellation", "Account", "Other"].index(cat) if cat in ["Payment", "Delivery", "Refund", "Cancellation", "Account", "Other"] else 5,
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
                            st.success(f"Support ticket #{t_data['id']} has been created successfully.")
                        else:
                            st.error(f"Error creating ticket: {t_res.text}")
                    except Exception as e:
                        st.error(f"Request failed: {e}")


# ==========================================
# PAGE 2: CONVERSATION HISTORY
# ==========================================
elif page == "Conversation History":
    st.markdown('<div class="main-title">📜 Conversation History</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Review previous customer support inquiries and AI responses saved in MySQL.</div>',
        unsafe_allow_html=True,
    )

    filter_cust = st.checkbox("Filter by active customer only", value=True)
    target_id = selected_customer["id"] if (filter_cust and selected_customer) else None

    params = {"limit": 50}
    if target_id is not None:
        params["customer_id"] = target_id

    try:
        res = requests.get(f"{BACKEND_URL}/conversations", params=params, timeout=5)
        if res.status_code == 200:
            history = res.json()
            if not history:
                st.info("No conversations recorded yet. Ask a question on the 'Ask Support' page!")
            else:
                st.write(f"Showing **{len(history)}** recent conversation(s):")
                for item in history:
                    with st.container():
                        st.markdown(f"**Q:** {item['question']}")
                        st.markdown(f"**A:** {item['answer']}")
                        st.caption(f"Logged at: {item['created_at']} | Customer ID: {item['customer_id']}")
                        st.divider()
        else:
            st.error(f"Failed to fetch conversations ({res.status_code})")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")


# ==========================================
# PAGE 3: SUPPORT TICKETS
# ==========================================
elif page == "Support Tickets":
    st.markdown('<div class="main-title">🎫 Support Tickets</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">View and monitor support tickets escalated to human agents.</div>',
        unsafe_allow_html=True,
    )

    filter_cust = st.checkbox("Filter by active customer only", value=False)
    target_id = selected_customer["id"] if (filter_cust and selected_customer) else None

    params = {"limit": 50}
    if target_id is not None:
        params["customer_id"] = target_id

    try:
        res = requests.get(f"{BACKEND_URL}/tickets", params=params, timeout=5)
        if res.status_code == 200:
            tickets = res.json()
            if not tickets:
                st.info("No support tickets currently on file.")
            else:
                # Format into a clean display table
                table_data = []
                for t in tickets:
                    table_data.append({
                        "Ticket ID": f"#{t['id']}",
                        "Customer": t.get("customer_name") or f"ID #{t['customer_id']}",
                        "Category": t["category"],
                        "Issue Description": t["issue"],
                        "Status": t["status"],
                        "Created At": t["created_at"],
                    })
                st.dataframe(table_data, use_container_width=True)
        else:
            st.error(f"Failed to fetch tickets ({res.status_code})")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")


# ==========================================
# PAGE 4: CREATE TICKET DIRECTLY
# ==========================================
elif page == "Create Ticket":
    st.markdown('<div class="main-title">➕ Create Support Ticket</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Directly escalate an inquiry to our support staff.</div>',
        unsafe_allow_html=True,
    )

    if not selected_customer:
        st.error("Please select a customer profile in the sidebar first.")
        st.stop()

    with st.form("manual_ticket_form"):
        st.text_input("Customer Name", value=selected_customer["name"], disabled=True)
        st.text_input("Customer Email", value=selected_customer["email"], disabled=True)

        cat = st.selectbox(
            "Category",
            ["Payment", "Delivery", "Refund", "Cancellation", "Account", "Other"],
        )
        issue_text = st.text_area(
            "Describe the issue in detail",
            placeholder="Please detail your problem, order IDs, or error messages...",
            height=120,
        )

        submitted = st.form_submit_button("Submit Support Ticket", type="primary")
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
                        st.success(f"Support ticket #{ticket['id']} has been created successfully.")
                    else:
                        st.error(f"Failed to create ticket: {res.text}")
                except Exception as ex:
                    st.error(f"Connection error: {ex}")
