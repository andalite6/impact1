import streamlit as st
import logging
from theme import get_theme

logger = logging.getLogger("ImpactGuard")

def card(title, content, card_type="default"):
    """Generate an HTML card with a consistent style."""
    try:
        theme = get_theme()
        card_class = "card"
        if card_type == "warning":
            card_class += " warning-card"
        elif card_type == "error":
            card_class += " error-card"
        elif card_type == "success":
            card_class += " success-card"
        html = f"""
        <div class="{card_class}">
            <div style="font-weight:bold; font-size:18px; margin-bottom:10px; color:{theme['primary']}">{title}</div>
            {content}
        </div>
        """
        return html
    except Exception as e:
        logger.error(f"Error rendering card: {str(e)}")
        return f"<div class='card error-card'>Error: {str(e)}</div>"

def modern_card(title, content, card_type="default", icon=None):
    """Generate a modern style card with optional icon."""
    try:
        theme = get_theme()
        card_class = "modern-card"
        if card_type in ["warning", "error", "secondary", "accent"]:
            card_class += f" {card_type}"
        icon_html = f'<span style="margin-right: 8px;">{icon}</span>' if icon else ''
        html = f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                {icon_html}<span style="font-weight:bold; font-size:18px; color:{theme['primary']}">{title}</span>
            </div>
            <div>{content}</div>
        </div>
        """
        return html
    except Exception as e:
        logger.error(f"Error rendering modern card: {str(e)}")
        return f"<div class='modern-card error'>Error: {str(e)}</div>"

def metric_card(label, value, description="", prefix="", suffix=""):
    """Generate an HTML metric card."""
    try:
        html = f"""
        <div class="modern-card">
            <div style="font-size:14px; color:#555;">{label}</div>
            <div style="font-size:32px; font-weight:bold;">{prefix}{value}{suffix}</div>
            <div style="font-size:12px; opacity:0.7;">{description}</div>
        </div>
        """
        return html
    except Exception as e:
        logger.error(f"Error rendering metric card: {str(e)}")
        return "<div class='modern-card error'>Error rendering metric card.</div>"

def render_header():
    """Render the application header safely."""
    try:
        header_html = """
        <div style="display: flex; align-items: center; margin-bottom: 24px;">
            <div style="margin-right: 15px;">
                <svg width="38" height="38" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                    <path d="M100 10 L180 50 V120 C180 150 150 180 100 190 C50 180 20 150 20 120 V50 L100 10Z" fill="#003b7a" />
                    <path d="M75 70 C95 70 110 125 140 110" stroke="white" stroke-width="15" fill="none" />
                </svg>
            </div>
            <div>
                <h1 style="margin:0; color:#003b7a;">ImpactGuard</h1>
                <p style="margin:0; font-size:14px;">AI Security & Sustainability Hub</p>
            </div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    except Exception as e:
        st.markdown("<h1>ImpactGuard</h1>")
