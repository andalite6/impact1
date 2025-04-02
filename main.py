import streamlit as st
import logging
from session_state import initialize_session_state, cleanup_threads, display_error
from theme import load_css
from ui_components import render_header
from navigation import sidebar_navigation, safe_rerun
from security_tests import start_security_test

logger = logging.getLogger("ImpactGuard")
logging.basicConfig(level=logging.INFO)

def render_dashboard():
    render_header()
    st.markdown("<h2>Dashboard</h2>", unsafe_allow_html=True)
    st.markdown("Welcome to ImpactGuard!")
    # Example metric card usage:
    from ui_components import metric_card
    st.markdown(metric_card("Targets", len(st.session_state.get("targets", [])), "Configured AI models"), unsafe_allow_html=True)

def page_router():
    page = st.session_state.get("current_page", "Dashboard")
    if page == "Dashboard":
        render_dashboard()
    else:
        st.markdown(f"<h2>{page}</h2>", unsafe_allow_html=True)
        st.markdown("Page under development...")

def main():
    initialize_session_state()
    cleanup_threads()
    st.markdown(load_css(), unsafe_allow_html=True)
    if st.session_state.get("error_message"):
        st.error(st.session_state["error_message"])
        if st.button("Clear Error"):
            st.session_state["error_message"] = None
            safe_rerun()
    sidebar_navigation()
    page_router()

if __name__ == "__main__":
    main()
