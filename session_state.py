import streamlit as st
import logging

logger = logging.getLogger("ImpactGuard")

def initialize_session_state():
    """Initialize all session state variables with proper error handling"""
    try:
        st.session_state.setdefault("targets", [])
        st.session_state.setdefault("test_results", {})
        st.session_state.setdefault("running_test", False)
        st.session_state.setdefault("progress", 0)
        st.session_state.setdefault("vulnerabilities_found", 0)
        st.session_state.setdefault("current_theme", "dark")
        st.session_state.setdefault("current_page", "Dashboard")
        st.session_state.setdefault("active_threads", [])
        st.session_state.setdefault("error_message", None)
        st.session_state.setdefault("bias_results", {})
        st.session_state.setdefault("show_bias_results", False)
        st.session_state.setdefault("carbon_tracking_active", False)
        st.session_state.setdefault("carbon_measurements", [])
        st.session_state.setdefault("VALIDATION_STRICTNESS", 2)
        st.session_state.setdefault("reports", [])
        st.session_state.setdefault("insights", [])
        logger.info("Session state initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        display_error(f"Failed to initialize application state: {str(e)}")

def cleanup_threads():
    """Remove completed threads from session state using a simple filter"""
    try:
        active = st.session_state.get("active_threads", [])
        st.session_state["active_threads"] = [thr for thr in active if thr.is_alive()]
        if st.session_state["active_threads"]:
            logger.info(f"Active threads: {len(st.session_state['active_threads'])}")
    except Exception as e:
        logger.error(f"Error cleaning up threads: {str(e)}")

def display_error(message):
    """Display error message to the user"""
    try:
        st.session_state["error_message"] = message
        logger.error(f"UI Error: {message}")
    except Exception as e:
        logger.critical(f"Failed to display error message: {str(e)}")
