import streamlit as st
import logging
from datetime import datetime
from theme import get_theme

logger = logging.getLogger("ImpactGuard")

def set_page(page_name):
    """Set the current page in session state."""
    try:
        st.session_state["current_page"] = page_name
        logger.info(f"Switched to page: {page_name}")
    except Exception as e:
        logger.error(f"Error setting page: {str(e)}")

def safe_rerun():
    """Safely rerun the app, supporting various Streamlit versions."""
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception as e:
            logger.error(f"Failed to rerun app: {str(e)}")

def sidebar_navigation():
    """Render the sidebar navigation menu."""
    try:
        st.sidebar.markdown("""
        <div style="padding:1rem; border-bottom:1px solid #ccc;">
            <h2>ImpactGuard</h2>
            <p>by HCLTech</p>
        </div>
        """, unsafe_allow_html=True)
        
        navigation_categories = {
            "Core Security": [
                {"icon": "🏠", "name": "Dashboard"},
                {"icon": "🎯", "name": "Target Management"},
                {"icon": "🧪", "name": "Test Configuration"},
                {"icon": "▶️", "name": "Run Assessment"},
                {"icon": "📊", "name": "Results Analyzer"}
            ],
            "Reports & Knowledge": [
                {"icon": "📝", "name": "Report Generator"},
                {"icon": "📚", "name": "Citation Tool"},
                {"icon": "💡", "name": "Insight Assistant"}
            ],
            "System": [
                {"icon": "⚙️", "name": "Settings"}
            ]
        }
        
        for category, options in navigation_categories.items():
            st.sidebar.markdown(f"<div style='font-weight:bold; margin:10px 0;'>{category}</div>", unsafe_allow_html=True)
            for opt in options:
                if st.sidebar.button(f"{opt['icon']} {opt['name']}", key=f"nav_{opt['name']}"):
                    set_page(opt["name"])
                    safe_rerun()
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Toggle Theme", key="toggle_theme"):
            current = st.session_state.get("current_theme", "dark")
            st.session_state["current_theme"] = "light" if current == "dark" else "dark"
            safe_rerun()
        
        st.sidebar.markdown(f"v1.0.0 | {datetime.now().strftime('%Y-%m-%d')}")
    except Exception as e:
        st.sidebar.error(f"Navigation error: {str(e)}")
