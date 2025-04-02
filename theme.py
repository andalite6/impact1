import streamlit as st

# Define color schemes
themes = {
    "dark": {
        "bg_color": "#121212",
        "card_bg": "#1E1E1E",
        "primary": "#003b7a",
        "secondary": "#BB86FC",
        "accent": "#03DAC6",
        "warning": "#FF9800",
        "error": "#CF6679",
        "text": "#FFFFFF"
    },
    "light": {
        "bg_color": "#F5F5F5",
        "card_bg": "#FFFFFF",
        "primary": "#003b7a",
        "secondary": "#7C4DFF",
        "accent": "#00BCD4",
        "warning": "#FF9800",
        "error": "#F44336",
        "text": "#212121"
    }
}

def get_theme():
    """Get current theme with error handling; fall back to dark theme"""
    try:
        return themes[st.session_state.get("current_theme", "dark")]
    except Exception:
        return themes["dark"]

def load_css():
    """Load CSS styles with the current theme"""
    try:
        theme = get_theme()
        return f"""
        <style>
        .main .block-container {{ padding-top: 1rem; padding-bottom: 1rem; }}
        h1, h2, h3, h4, h5, h6 {{ color: {theme["primary"]}; }}
        .stProgress > div > div > div > div {{ background-color: {theme["primary"]}; }}
        .card {{ border-radius: 10px; background-color: {theme["card_bg"]}; padding: 1.5rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1rem; border-left: 3px solid {theme["primary"]}; }}
        .error-message {{ background-color: #CF6679; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
        </style>
        """
    except Exception as e:
        return "<style>.error-message { background-color: #CF6679; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; }</style>"
