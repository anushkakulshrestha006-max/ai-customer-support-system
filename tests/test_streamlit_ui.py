"""
UI interaction tests for Streamlit interface using AppTest.
Run with: pytest tests/test_streamlit_ui.py
"""
import pytest
from streamlit.testing.v1 import AppTest


def test_clear_input_no_exception():
    """Verify Clear Input empties the question input without StreamlitAPIException."""
    at = AppTest.from_file("streamlit_app/app.py", default_timeout=15)
    at.run()
    at.sidebar.radio[0].set_value("Ask Support (RAG)").run()

    # Populate question via example button
    at.button(key="ex_btn_0").click().run()
    assert at.text_area(key="question_input").value == "How long does standard delivery take?"

    # Click Clear Input
    clear_btn = [b for b in at.button if b.label == "Clear"][0]
    clear_btn.click().run()

    # Verify no exceptions and input is empty
    assert len(at.exception) == 0
    assert at.text_area(key="question_input").value == ""


def test_quick_example_selection_and_submission():
    """Verify clicking an example question populates and submits successfully."""
    at = AppTest.from_file("streamlit_app/app.py", default_timeout=15)
    at.run()
    at.sidebar.radio[0].set_value("Ask Support (RAG)").run()

    # Click example button
    at.button(key="ex_btn_1").click().run()
    assert at.text_area(key="question_input").value == "What is your refund policy?"

    # Click Ask Support
    ask_btn = [b for b in at.button if b.label == "Ask Support"][0]
    ask_btn.click().run()

    assert len(at.exception) == 0
    assert at.session_state["last_question"] == "What is your refund policy?"
    assert at.session_state["last_result"]["category"] == "Refund"


def test_empty_question_graceful_warning():
    """Verify empty submission displays friendly validation message."""
    at = AppTest.from_file("streamlit_app/app.py", default_timeout=15)
    at.run()
    at.sidebar.radio[0].set_value("Ask Support (RAG)").run()

    at.text_area(key="question_input").input("   ").run()
    ask_btn = [b for b in at.button if b.label == "Ask Support"][0]
    ask_btn.click().run()

    assert len(at.exception) == 0
    assert len(at.warning) > 0
    assert "Please type a question" in at.warning[0].value
