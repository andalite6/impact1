import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import time
import logging
import os
import threading
import random
import base64
import traceback
import re
import difflib
from datetime import datetime, timedelta
from io import BytesIO
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("impactguard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ImpactGuard")

# Create a thread pool with reasonable limits
thread_executor = ThreadPoolExecutor(max_workers=4)

# Set page configuration with custom theme
st.set_page_config(
    page_title="ImpactGuard - AI Security & Sustainability Hub",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Setup OpenAI API key securely (for reporting functionality)
try:
    # Better approach using environment variables with fallback to secrets
    import os
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except:
            pass
    
    if api_key:
        import openai
        openai.api_key = api_key
    else:
        logger.warning("OpenAI API key not found. Some features may be limited.")
except Exception as e:
    logger.warning(f"OpenAI API key configuration error: {str(e)}")

# ----------------------------------------------------------------
# Session State Management
# ----------------------------------------------------------------

def initialize_session_state():
    """Initialize all session state variables with proper error handling"""
    try:
        # Core session states
        if 'targets' not in st.session_state:
            st.session_state.targets = []

        if 'test_results' not in st.session_state:
            st.session_state.test_results = {}

        if 'running_test' not in st.session_state:
            st.session_state.running_test = False

        if 'progress' not in st.session_state:
            st.session_state.progress = 0

        if 'vulnerabilities_found' not in st.session_state:
            st.session_state.vulnerabilities_found = 0

        if 'current_theme' not in st.session_state:
            st.session_state.current_theme = "dark"  # Default to dark theme
            
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Dashboard"

        # Thread management
        if 'active_threads' not in st.session_state:
            st.session_state.active_threads = []
            
        # Error handling
        if 'error_message' not in st.session_state:
            st.session_state.error_message = None
            
        # Initialize bias testing state
        if 'bias_results' not in st.session_state:
            st.session_state.bias_results = {}
            
        if 'show_bias_results' not in st.session_state:
            st.session_state.show_bias_results = False
            
        # Carbon tracking states
        if 'carbon_tracking_active' not in st.session_state:
            st.session_state.carbon_tracking_active = False
            
        if 'carbon_measurements' not in st.session_state:
            st.session_state.carbon_measurements = []

        # Citation tool states
        if 'VALIDATION_STRICTNESS' not in st.session_state:
            st.session_state.VALIDATION_STRICTNESS = 2
            
        # Reporting states
        if 'reports' not in st.session_state:
            st.session_state.reports = []
            
        # Insight report states
        if 'insights' not in st.session_state:
            st.session_state.insights = []
            
        logger.info("Session state initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing session state: {str(e)}")
        display_error(f"Failed to initialize application state: {str(e)}")

# Thread cleanup
def cleanup_threads():
    """Remove completed threads from session state"""
    try:
        if 'active_threads' in st.session_state:
            # Filter out completed threads
            st.session_state.active_threads = [
                thread for thread in st.session_state.active_threads if thread.is_alive()
            ]
            
            if len(st.session_state.active_threads) > 0:
                logger.info(f"Active threads: {len(st.session_state.active_threads)}")
    except Exception as e:
        logger.error(f"Error cleaning up threads: {str(e)}")

# ----------------------------------------------------------------
# UI Theme & Styling
# ----------------------------------------------------------------

# Define color schemes
themes = {
    "dark": {
        "bg_color": "#121212",
        "card_bg": "#1E1E1E",
        "primary": "#003b7a",    # ImpactGuard blue
        "secondary": "#BB86FC",  # Purple
        "accent": "#03DAC6",     # Teal
        "warning": "#FF9800",    # Orange
        "error": "#CF6679",      # Red
        "text": "#FFFFFF"
    },
    "light": {
        "bg_color": "#F5F5F5",
        "card_bg": "#FFFFFF",
        "primary": "#003b7a",    # ImpactGuard blue
        "secondary": "#7C4DFF",  # Deep purple
        "accent": "#00BCD4",     # Cyan
        "warning": "#FF9800",    # Orange
        "error": "#F44336",      # Red
        "text": "#212121"
    }
}

# Get current theme colors safely
def get_theme():
    """Get current theme with error handling"""
    try:
        return themes[st.session_state.current_theme]
    except Exception as e:
        logger.error(f"Error getting theme: {str(e)}")
        # Return dark theme as fallback
        return themes["dark"]

# CSS styles
def load_css():
    """Load CSS with the current theme"""
    try:
        theme = get_theme()
        
        return f"""
        <style>
        .main .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: {theme["primary"]};
        }}
        
        .stProgress > div > div > div > div {{
            background-color: {theme["primary"]};
        }}
        
        div[data-testid="stExpander"] {{
            border: none;
            border-radius: 8px;
            background-color: {theme["card_bg"]};
            margin-bottom: 1rem;
        }}
        
        div[data-testid="stVerticalBlock"] {{
            gap: 1.5rem;
        }}
        
        .card {{
            border-radius: 10px;
            background-color: {theme["card_bg"]};
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 1rem;
            border-left: 3px solid {theme["primary"]};
        }}
        
        .warning-card {{
            border-left: 3px solid {theme["warning"]};
        }}
        
        .error-card {{
            border-left: 3px solid {theme["error"]};
        }}
        
        .success-card {{
            border-left: 3px solid {theme["primary"]};
        }}
        
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: {theme["primary"]};
        }}
        
        .metric-label {{
            font-size: 14px;
            color: {theme["text"]};
            opacity: 0.7;
        }}
        
        .sidebar-title {{
            margin-left: 15px;
            font-size: 1.2rem;
            font-weight: bold;
            color: {theme["primary"]};
        }}
        
        .target-card {{
            border-radius: 8px;
            background-color: {theme["card_bg"]};
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 3px solid {theme["secondary"]};
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        
        .status-badge.active {{
            background-color: {theme["primary"]};
            color: white;
        }}
        
        .status-badge.inactive {{
            background-color: gray;
            color: white;
        }}
        
        .hover-card:hover {{
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }}
        
        .card-title {{
            color: {theme["primary"]};
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .nav-item {{
            padding: 8px 15px;
            border-radius: 5px;
            margin-bottom: 5px;
            cursor: pointer;
        }}
        
        .nav-item:hover {{
            background-color: rgba(0, 59, 122, 0.1);
        }}
        
        .nav-item.active {{
            background-color: rgba(0, 59, 122, 0.2);
            font-weight: bold;
        }}
        
        .tag {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            margin-right: 5px;
            margin-bottom: 5px;
        }}
        
        .tag.owasp {{
            background-color: rgba(187, 134, 252, 0.2);
            color: {theme["secondary"]};
        }}
        
        .tag.nist {{
            background-color: rgba(3, 218, 198, 0.2);
            color: {theme["accent"]};
        }}
        
        .tag.fairness {{
            background-color: rgba(255, 152, 0, 0.2);
            color: {theme["warning"]};
        }}
        
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            border-radius: 5px 5px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {theme["card_bg"]};
            border-bottom: 3px solid {theme["primary"]};
        }}
        
        .error-message {{
            background-color: #CF6679;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        
        /* Modern sidebar styling */
        section[data-testid="stSidebar"] {{
            background-color: {theme["card_bg"]};
            border-right: 1px solid rgba(0,0,0,0.1);
        }}
        
        /* Modern navigation categories */
        .nav-category {{
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
            color: {theme["text"]};
            opacity: 0.6;
            margin: 10px 15px 5px 15px;
        }}
        
        /* Main content area padding */
        .main-content {{
            padding: 20px;
        }}
        
        /* Modern cards with hover effects */
        .modern-card {{
            background-color: {theme["card_bg"]};
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
            transition: all 0.3s ease;
            border-left: none;
            border-top: 4px solid {theme["primary"]};
        }}
        
        .modern-card:hover {{
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            transform: translateY(-5px);
        }}
        
        .modern-card.warning {{
            border-top: 4px solid {theme["warning"]};
        }}
        
        .modern-card.error {{
            border-top: 4px solid {theme["error"]};
        }}
        
        .modern-card.secondary {{
            border-top: 4px solid {theme["secondary"]};
        }}
        
        .modern-card.accent {{
            border-top: 4px solid {theme["accent"]};
        }}
        
        /* App header styles */
        .app-header {{
            display: flex;
            align-items: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .app-title {{
            font-size: 24px;
            font-weight: bold;
            margin: 0;
            color: {theme["primary"]};
        }}
        
        .app-subtitle {{
            font-size: 14px;
            opacity: 0.7;
            margin: 0;
        }}
        </style>
        """
    except Exception as e:
        logger.error(f"Error loading CSS: {str(e)}")
        # Return minimal CSS as fallback
        return "<style>.error-message { background-color: #CF6679; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px; }</style>"

# ----------------------------------------------------------------
# Navigation and Control
# ----------------------------------------------------------------

# Helper function to set page
def set_page(page_name):
    """Set the current page safely"""
    try:
        st.session_state.current_page = page_name
        logger.info(f"Navigation: Switched to {page_name} page")
    except Exception as e:
        logger.error(f"Error setting page to {page_name}: {str(e)}")
        display_error(f"Failed to navigate to {page_name}")

# Safe rerun function
def safe_rerun():
    """Safely rerun the app, handling different Streamlit versions"""
    try:
        st.rerun()  # For newer Streamlit versions
    except Exception as e1:
        try:
            st.experimental_rerun()  # For older Streamlit versions
        except Exception as e2:
            logger.error(f"Failed to rerun app: {str(e1)} then {str(e2)}")
            # Do nothing - at this point we can't fix it

# Error handling
def display_error(message):
    """Display error message to the user"""
    try:
        st.session_state.error_message = message
        logger.error(f"UI Error: {message}")
    except Exception as e:
        logger.critical(f"Failed to display error message: {str(e)}")

# ----------------------------------------------------------------
# Custom UI Components
# ----------------------------------------------------------------

# Custom components
def card(title, content, card_type="default"):
    """Generate HTML card with error handling"""
    try:
        card_class = "card"
        if card_type == "warning":
            card_class += " warning-card"
        elif card_type == "error":
            card_class += " error-card"
        elif card_type == "success":
            card_class += " success-card"
        
        return f"""
        <div class="{card_class} hover-card">
            <div class="card-title">{title}</div>
            {content}
        </div>
        """
    except Exception as e:
        logger.error(f"Error rendering card: {str(e)}")
        return f"""
        <div class="card error-card">
            <div class="card-title">Error Rendering Card</div>
            <p>Failed to render card content: {str(e)}</p>
        </div>
        """

def modern_card(title, content, card_type="default", icon=None):
    """Generate a modern style card with optional icon"""
    try:
        card_class = "modern-card"
        if card_type == "warning":
            card_class += " warning"
        elif card_type == "error":
            card_class += " error"
        elif card_type == "secondary":
            card_class += " secondary"
        elif card_type == "accent":
            card_class += " accent"
        
        icon_html = f'<span style="margin-right: 8px;">{icon}</span>' if icon else ''
        
        return f"""
        <div class="{card_class}">
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                {icon_html}
                <div class="card-title">{title}</div>
            </div>
            <div>{content}</div>
        </div>
        """
    except Exception as e:
        logger.error(f"Error rendering modern card: {str(e)}")
        return f"""
        <div class="modern-card error">
            <div class="card-title">Error Rendering Card</div>
            <p>Failed to render card content: {str(e)}</p>
        </div>
        """

def metric_card(label, value, description="", prefix="", suffix=""):
    """Generate HTML metric card with error handling"""
    try:
        return f"""
        <div class="modern-card hover-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{prefix}{value}{suffix}</div>
            <div style="font-size: 14px; opacity: 0.7;">{description}</div>
        </div>
        """
    except Exception as e:
        logger.error(f"Error rendering metric card: {str(e)}")
        return f"""
        <div class="modern-card error">
            <div class="metric-label">Error</div>
            <div class="metric-value">N/A</div>
            <div style="font-size: 14px; opacity: 0.7;">Failed to render metric: {str(e)}</div>
        </div>
        """

# Logo and header
def render_header():
    """Render the application header safely"""
    try:
        logo_html = """
        <div class="app-header">
            <div style="margin-right: 15px; width: 38px; height: 38px;">
                <svg width="38" height="38" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                    <path d="M100 10 L180 50 V120 C180 150 150 180 100 190 C50 180 20 150 20 120 V50 L100 10Z" fill="#003b7a" />
                    <path d="M75 70 C95 70 110 125 140 110" stroke="white" strokeWidth="15" fill="none" />
                </svg>
            </div>
            <div>
                <div class="app-title">ImpactGuard</div>
                <div class="app-subtitle">Supercharging progress in AI Ethics and Governance – ORAIG</div>
            </div>
        </div>
        """
        st.markdown(logo_html, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error rendering header: {str(e)}")
        st.markdown("# 🛡️ ImpactGuard")

# ----------------------------------------------------------------
# Sidebar Navigation
# ----------------------------------------------------------------

def sidebar_navigation():
    """Render the sidebar navigation with organized categories"""
    try:
        st.sidebar.markdown("""
        <div style="display: flex; align-items: center; padding: 1rem 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <div style="margin-right: 10px;">
                <svg width="28" height="28" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                    <path d="M100 10 L180 50 V120 C180 150 150 180 100 190 C50 180 20 150 20 120 V50 L100 10Z" fill="#003b7a" />
                    <path d="M75 70 C95 70 110 125 140 110" stroke="white" strokeWidth="15" fill="none" />
                </svg>
            </div>
            <div>
                <div style="font-weight: bold; font-size: 1.2rem; color: #4299E1;">ImpactGuard</div>
                <div style="font-size: 0.7rem; opacity: 0.7;">By HCLTech</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Organize navigation options by category
        navigation_categories = {
            "Core Security": [
                {"icon": "🏠", "name": "Dashboard"},
                {"icon": "🎯", "name": "Target Management"},
                {"icon": "🧪", "name": "Test Configuration"},
                {"icon": "▶️", "name": "Run Assessment"},
                {"icon": "📊", "name": "Results Analyzer"}
            ],
            "AI Ethics & Bias": [
                {"icon": "🔍", "name": "Ethical AI Testing"},
                {"icon": "⚖️", "name": "Bias Testing"},
                {"icon": "📏", "name": "Bias Comparison"},
                {"icon": "🧠", "name": "HELM Evaluation"}
            ],
            "Sustainability": [
                {"icon": "🌱", "name": "Environmental Impact"},
                {"icon": "🌍", "name": "Sustainability Dashboard"}
            ],
            "Reports & Knowledge": [
                {"icon": "📝", "name": "Report Generator"},
                {"icon": "📚", "name": "Citation Tool"},
                {"icon": "💡", "name": "Insight Assistant"}
            ],
            "Integration & Tools": [
                {"icon": "📁", "name": "Multi-Format Import"},
                {"icon": "🚀", "name": "High-Volume Testing"},
                {"icon": "📚", "name": "Knowledge Base"}
            ],
            "System": [
                {"icon": "⚙️", "name": "Settings"},
                {"icon": "🧪", "name": "Run Tests"}  # Added test page
            ]
        }
        
        # Render each category and its navigation options
        for category, options in navigation_categories.items():
            st.sidebar.markdown(f'<div class="nav-category">{category}</div>', unsafe_allow_html=True)
            
            for option in options:
                # Create a button for each navigation option
                if st.sidebar.button(
                    f"{option['icon']} {option['name']}", 
                    key=f"nav_{option['name']}",
                    use_container_width=True,
                    type="secondary" if st.session_state.current_page != option["name"] else "primary"
                ):
                    set_page(option["name"])
                    safe_rerun()
        
        # Theme toggle
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Toggle Theme", key="toggle_theme", use_container_width=True):
            st.session_state.current_theme = "light" if st.session_state.current_theme == "dark" else "dark"
            logger.info(f"Theme toggled to {st.session_state.current_theme}")
            safe_rerun()
        
        # System status
        st.sidebar.markdown("---")
        st.sidebar.markdown('<div class="sidebar-title">📡 System Status</div>', unsafe_allow_html=True)
        
        if st.session_state.running_test:
            st.sidebar.success("⚡ Test Running")
        else:
            st.sidebar.info("⏸️ Idle")
        
        st.sidebar.markdown(f"🎯 Targets: {len(st.session_state.targets)}")
        
        # Active threads info
        if 'active_threads' in st.session_state and len(st.session_state.active_threads) > 0:
            st.sidebar.markdown(f"🧵 Active threads: {len(st.session_state.active_threads)}")
        
        # Add carbon tracking status if active
        if st.session_state.get("carbon_tracking_active", False):
            st.sidebar.markdown("🌱 Carbon tracking active")
        
        # Add version info
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"v1.0.0 | {datetime.now().strftime('%Y-%m-%d')}", unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error rendering sidebar: {str(e)}")
        st.sidebar.error("Navigation Error")
        st.sidebar.markdown(f"Error: {str(e)}")

# ----------------------------------------------------------------
# Utility Classes and Functions (Common)
# ----------------------------------------------------------------

# Mock data functions with error handling
def get_mock_test_vectors():
    """Get mock test vector data with error handling"""
    try:
        return [
            {
                "id": "sql_injection",
                "name": "SQL Injection",
                "category": "owasp",
                "severity": "high"
            },
            {
                "id": "xss",
                "name": "Cross-Site Scripting",
                "category": "owasp",
                "severity": "medium"
            },
            {
                "id": "prompt_injection",
                "name": "Prompt Injection",
                "category": "owasp",
                "severity": "critical"
            },
            {
                "id": "insecure_output",
                "name": "Insecure Output Handling",
                "category": "owasp",
                "severity": "high"
            },
            {
                "id": "nist_governance",
                "name": "AI Governance",
                "category": "nist",
                "severity": "medium"
            },
            {
                "id": "nist_transparency",
                "name": "Transparency",
                "category": "nist",
                "severity": "medium"
            },
            {
                "id": "fairness_demographic",
                "name": "Demographic Parity",
                "category": "fairness",
                "severity": "high"
            },
            {
                "id": "privacy_gdpr",
                "name": "GDPR Compliance",
                "category": "privacy",
                "severity": "critical"
            },
            {
                "id": "jailbreaking",
                "name": "Jailbreaking Resistance",
                "category": "exploit",
                "severity": "critical"
            }
        ]
    except Exception as e:
        logger.error(f"Error getting mock test vectors: {str(e)}")
        display_error("Failed to load test vectors")
        return []  # Return empty list as fallback

def run_mock_test(target, test_vectors, duration=30):
    """Simulate running a test in the background with proper error handling"""
    try:
        # Initialize progress
        st.session_state.progress = 0
        st.session_state.vulnerabilities_found = 0
        st.session_state.running_test = True
        
        logger.info(f"Starting mock test against {target['name']} with {len(test_vectors)} test vectors")
        
        # Create mock results data structure
        results = {
            "summary": {
                "total_tests": 0,
                "vulnerabilities_found": 0,
                "risk_score": 0
            },
            "vulnerabilities": [],
            "test_details": {}
        }
        
        # Simulate test execution
        total_steps = 100
        step_sleep = duration / total_steps
        
        for i in range(total_steps):
            # Check if we should stop (for handling cancellations)
            if not st.session_state.running_test:
                logger.info("Test was cancelled")
                break
                
            time.sleep(step_sleep)
            st.session_state.progress = (i + 1) / total_steps
            
            # Occasionally "find" a vulnerability
            if random.random() < 0.2:  # 20% chance each step
                vector = random.choice(test_vectors)
                severity_weight = {"low": 1, "medium": 2, "high": 3, "critical": 5}
                weight = severity_weight.get(vector["severity"], 1)
                
                # Add vulnerability to results
                vulnerability = {
                    "id": f"VULN-{len(results['vulnerabilities']) + 1}",
                    "test_vector": vector["id"],
                    "test_name": vector["name"],
                    "severity": vector["severity"],
                    "details": f"Mock vulnerability found in {target['name']} using {vector['name']} test vector.",
                    "timestamp": datetime.now().isoformat()
                }
                results["vulnerabilities"].append(vulnerability)
                
                # Update counters
                st.session_state.vulnerabilities_found += 1
                results["summary"]["vulnerabilities_found"] += 1
                results["summary"]["risk_score"] += weight
                
                logger.info(f"Found vulnerability: {vulnerability['id']} ({vulnerability['severity']})")
        
        # Complete the test results
        results["summary"]["total_tests"] = len(test_vectors) * 10  # Assume 10 variations per vector
        results["timestamp"] = datetime.now().isoformat()
        results["target"] = target["name"]
        
        logger.info(f"Test completed: {results['summary']['vulnerabilities_found']} vulnerabilities found")
        
        # Set the results in session state
        st.session_state.test_results = results
        return results
    
    except Exception as e:
        error_details = {
            "error": True,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        logger.error(f"Error in test execution: {str(e)}")
        logger.debug(traceback.format_exc())
        
        # Create error result
        st.session_state.error_message = f"Test execution failed: {str(e)}"
        return error_details
    
    finally:
        # Always ensure we reset the running state
        st.session_state.running_test = False

# Submit test to thread pool
def submit_test(target, test_vectors, duration):
    """Submit a test to the thread pool"""
    try:
        future = thread_executor.submit(run_mock_test, target, test_vectors, duration)
        st.session_state.active_threads.append(future)
        logger.info(f"Test submitted to thread pool for {target['name']}")
        return future
    except Exception as e:
        logger.error(f"Error submitting test to thread pool: {str(e)}")
        st.error(f"Failed to start test: {str(e)}")
        return None

# File Format Support Functions
def handle_multiple_file_formats(uploaded_file):
    """Process different file formats for impact assessments"""
    try:
        if uploaded_file is None:
            return {"error": "No file uploaded"}
            
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # JSON (already supported)
        if file_extension == 'json':
            import json
            return json.loads(uploaded_file.read())
        
        # CSV
        elif file_extension == 'csv':
            import pandas as pd
            return pd.read_csv(uploaded_file)
        
        # Excel
        elif file_extension in ['xlsx', 'xls']:
            import pandas as pd
            return pd.read_excel(uploaded_file)
        
        # PDF
        elif file_extension == 'pdf':
            from pypdf import PdfReader
            
            pdf_reader = PdfReader(BytesIO(uploaded_file.read()))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return {"text": text}
        
        # XML
        elif file_extension == 'xml':
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(BytesIO(uploaded_file.read()))
            root = tree.getroot()
            
            # Convert XML to dict (simplified)
            def xml_to_dict(element):
                result = {}
                for child in element:
                    child_data = xml_to_dict(child)
                    if child.tag in result:
                        if type(result[child.tag]) is list:
                            result[child.tag].append(child_data)
                        else:
                            result[child.tag] = [result[child.tag], child_data]
                    else:
                        result[child.tag] = child_data
                
                if len(result) == 0:
                    return element.text
                return result
            
            return xml_to_dict(root)
        
        # YAML/YML
        elif file_extension in ['yaml', 'yml']:
            import yaml
            return yaml.safe_load(uploaded_file)
        
        # Other formats are supported similarly...
        else:
            return {"error": f"Unsupported file format: {file_extension}"}
            
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {"error": f"Failed to process file: {str(e)}"}

# ----------------------------------------------------------------
# Main Class for WhyLabs Bias Testing
# ----------------------------------------------------------------

class WhyLabsBiasTest:
    """Class for WhyLabs-based bias testing functionality"""
    
    def __init__(self):
        # This would normally import whylogs, but for demonstration we'll create a mock
        self.session = None
        self.results = {}
    
    def initialize_session(self, dataset_name):
        """Initialize a WhyLogs profiling session"""
        try:
            self.session = True  # Mock initialization
            logger.info(f"WhyLogs session initialized for {dataset_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WhyLogs session: {str(e)}")
            return False
    
    def profile_dataset(self, df, dataset_name):
        """Profile a dataset for bias analysis"""
        try:
            if self.session is None:
                self.initialize_session(dataset_name)
                
            # Create a mock profile
            profile = {"name": dataset_name, "columns": list(df.columns)}
            self.results[dataset_name] = {"profile": profile}
            logger.info(f"Dataset {dataset_name} profiled successfully")
            return profile
        except Exception as e:
            logger.error(f"Failed to profile dataset: {str(e)}")
            return None
    
    def analyze_bias(self, df, protected_features, target_column, dataset_name):
        """Analyze bias in a dataset based on protected features"""
        try:
            # Profile the dataset first
            profile = self.profile_dataset(df, dataset_name)
            
            bias_metrics = {}
            
            # Calculate basic bias metrics
            for feature in protected_features:
                # Statistical parity difference
                feature_groups = df.groupby(feature)
                
                outcomes = {}
                disparities = {}
                
                for group_name, group_data in feature_groups:
                    # For binary target variable
                    if df[target_column].nunique() == 2:
                        positive_outcome_rate = group_data[target_column].mean()
                        outcomes[group_name] = positive_outcome_rate
                
                # Calculate disparities between groups
                if outcomes:  # Check if outcomes dict is not empty
                    baseline = max(outcomes.values())
                    for group, rate in outcomes.items():
                        disparities[group] = baseline - rate
                
                bias_metrics[feature] = {
                    "outcomes": outcomes,
                    "disparities": disparities,
                    "max_disparity": max(disparities.values()) if disparities else 0
                }
            
            self.results[dataset_name]["bias_metrics"] = bias_metrics
            logger.info(f"Bias analysis completed for {dataset_name}")
            return bias_metrics
        except Exception as e:
            logger.error(f"Failed to analyze bias: {str(e)}")
            return {"error": str(e)}
    
    def get_results(self, dataset_name=None):
        """Get analysis results"""
        if dataset_name:
            return self.results.get(dataset_name, {})
        return self.results

# ----------------------------------------------------------------
# Main Class for Carbon Impact Tracking
# ----------------------------------------------------------------

class CarbonImpactTracker:
    """Class for tracking environmental impact of AI systems"""
    
    def __init__(self):
        # Placeholder for codecarbon import
        self.tracker = None
        self.measurements = []
        self.total_emissions = 0.0
        self.is_tracking = False
    
    def initialize_tracker(self, project_name, api_endpoint=None):
        """Initialize the carbon tracker"""
        try:
            # Mock initialization for demonstration
            self.tracker = {"project_name": project_name, "initialized": True}
            logger.info(f"Carbon tracker initialized for {project_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize carbon tracker: {str(e)}")
            return False
    
    def start_tracking(self):
        """Start tracking carbon emissions"""
        try:
            if self.tracker is None:
                return False
                
            self.is_tracking = True
            logger.info("Carbon emission tracking started")
            return True
        except Exception as e:
            logger.error(f"Failed to start carbon tracking: {str(e)}")
            return False
    
    def stop_tracking(self):
        """Stop tracking and get the emissions data"""
        try:
            if not self.is_tracking or self.tracker is None:
                return 0.0
                
            # Generate a random emissions value for demonstration
            emissions = random.uniform(0.001, 0.1)
            self.is_tracking = False
            self.measurements.append(emissions)
            self.total_emissions += emissions
            
            logger.info(f"Carbon emission tracking stopped. Measured: {emissions} kg CO2eq")
            return emissions
        except Exception as e:
            logger.error(f"Failed to stop carbon tracking: {str(e)}")
            return 0.0
    
    def get_total_emissions(self):
        """Get total emissions tracked so far"""
        return self.total_emissions
    
    def get_all_measurements(self):
        """Get all measurements"""
        return self.measurements
    
    def generate_report(self):
        """Generate a report of carbon emissions"""
        try:
            energy_solutions = [
                {
                    "name": "Optimize AI Model Size",
                    "description": "Reduce model parameters and optimize architecture",
                    "potential_savings": "20-60% reduction in emissions",
                    "implementation_difficulty": "Medium"
                },
                {
                    "name": "Implement Model Distillation",
                    "description": "Create smaller, efficient versions of larger models",
                    "potential_savings": "40-80% reduction in emissions",
                    "implementation_difficulty": "High"
                },
                {
                    "name": "Use Efficient Hardware",
                    "description": "Deploy on energy-efficient hardware (e.g., specialized AI chips)",
                    "potential_savings": "30-50% reduction in emissions",
                    "implementation_difficulty": "Medium"
                }
            ]
            
            # Calculate the impact
            kwh_per_kg_co2 = 0.6  # Approximate conversion factor
            energy_consumption = self.total_emissions / kwh_per_kg_co2
            
            trees_equivalent = self.total_emissions * 16.5  # Each kg CO2 ~ 16.5 trees for 1 day
            
            return {
                "total_emissions_kg": self.total_emissions,
                "energy_consumption_kwh": energy_consumption,
                "measurements": self.measurements,
                "trees_equivalent": trees_equivalent,
                "mitigation_strategies": energy_solutions
            }
        except Exception as e:
            logger.error(f"Failed to generate emissions report: {str(e)}")
            return {"error": str(e)}

# ----------------------------------------------------------------
# Report Generation and Citation Functions
# ----------------------------------------------------------------

def generate_insight(user, category, prompt_text, response_text, knowledge_base, context, temperature, max_tokens):
    """Generate an insight using OpenAI API"""
    try:
        import openai
        
        system_prompt = f"{knowledge_base}\n\n{context}"
        user_prompt = f"""
        Given the following information:
        User: {user}
        Category: {category}
        Prompt: {prompt_text}
        Response: {response_text}
        Generate a concise, meaningful insight based on this information.
        """
        
        for attempt in range(3):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                return response['choices'][0]['message']['content'].strip()
            except Exception as e:
                if "RateLimitError" in str(e) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise e
        
        # If we get here, all attempts failed
        return "Error: Unable to generate insight after multiple attempts."
    except ImportError:
        return "Error: OpenAI module not available. Please install it or check your API key configuration."
    except Exception as e:
        return f"Error generating insight: {str(e)}"

def process_csv(uploaded_file):
    """Process a CSV file for insight generation"""
    try:
        if uploaded_file is None:
            return None
            
        df = pd.read_csv(uploaded_file)
        required_columns = {'User', 'Category', 'Prompt', 'Response'}
        if not required_columns.issubset(df.columns):
            st.error(f"CSV must contain these columns: {required_columns}")
            return None
        return df
    except Exception as e:
        st.error(f"Error processing CSV: {str(e)}")
        return None

def generate_report(title, test_results, bias_results, sustainability_results, include_recommendations=True):
    """Generate a comprehensive report combining security, bias, and sustainability data"""
    try:
        # Input validation
        if title is None or not isinstance(title, str):
            title = "Security Assessment Report"
        
        # Create report structure
        report = {
            "title": title,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "security": test_results if test_results else {"summary": {"total_tests": 0, "vulnerabilities_found": 0, "risk_score": 0}, "vulnerabilities": []},
            "bias": bias_results if bias_results else {},
            "sustainability": sustainability_results if sustainability_results else {},
            "recommendations": []
        }
        
        # Generate recommendations
        if include_recommendations:
            # Security recommendations
            if test_results and "vulnerabilities" in test_results and test_results["vulnerabilities"]:
                for vuln in test_results["vulnerabilities"][:3]:  # Top 3 vulnerabilities
                    report["recommendations"].append({
                        "area": "security",
                        "severity": vuln.get("severity", "medium"),
                        "recommendation": f"Address {vuln.get('test_name', 'unknown vulnerability')} issue.",
                        "details": vuln.get("details", "No details")
                    })
            
            # Bias recommendations
            if bias_results and "bias_metrics" in bias_results:
                for feature, metrics in bias_results.get("bias_metrics", {}).items():
                    if metrics.get("max_disparity", 0) > 0.1:  # Threshold for recommendation
                        report["recommendations"].append({
                            "area": "bias",
                            "severity": "high" if metrics.get("max_disparity", 0) > 0.2 else "medium",
                            "recommendation": f"Address bias in {feature} attribute.",
                            "details": f"Disparity of {metrics.get('max_disparity', 0):.2f} detected in {feature}."
                        })
            
            # Sustainability recommendations
            if sustainability_results and "total_emissions_kg" in sustainability_results:
                emissions = sustainability_results.get("total_emissions_kg", 0)
                if emissions > 1.0:
                    report["recommendations"].append({
                        "area": "sustainability",
                        "severity": "medium",
                        "recommendation": "Optimize model size and deployment to reduce carbon footprint.",
                        "details": f"Current emissions of {emissions:.2f} kg CO2e could be reduced with efficiency improvements."
                    })
        
        # Add timestamp and report ID
        report["id"] = f"REP-{int(time.time())}"
        
        return report
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return {"error": str(e), "title": title, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# ----------------------------------------------------------------
# Citation Helper Functions
# ----------------------------------------------------------------

def retry_request(url, method='head', retries=3, timeout=5):
    """Make HTTP request with retries for citation validation"""
    for attempt in range(retries):
        try:
            if method == 'head':
                response = requests.head(url, allow_redirects=True, timeout=timeout)
            elif method == 'get':
                response = requests.get(url, allow_redirects=True, timeout=timeout)
            else:
                return None
            if response.status_code == 200:
                return response
        except requests.RequestException as e:
            logger.error(f"Network error on attempt {attempt + 1}: {e}")
            time.sleep(2 ** attempt)
    return None

def is_valid_doi_format(doi):
    """Check if DOI format is valid"""
    if not doi or not isinstance(doi, str):
        return False
    pattern = r'^10.\d{4,9}/[-._;()/:A-Z0-9]+$'
    return re.match(pattern, doi, re.IGNORECASE) is not None

def validate_doi(doi):
    """Validate DOI by checking if it resolves"""
    if not is_valid_doi_format(doi):
        return False
    url = f"https://doi.org/{doi}"
    response = retry_request(url, method='head')
    return response is not None

def validate_url(url):
    """Validate a URL by checking if it resolves"""
    if not url or not isinstance(url, str):
        return False
    # Basic URL validation
    if not re.match(r'^https?://', url):
        return False
    response = retry_request(url, method='head')
    return response is not None

def is_metadata_complete(article):
    """Check if article metadata is complete according to validation strictness level"""
    if not article:
        return False
    essential_fields = ['author', 'title', 'issued']
    missing_fields = [field for field in essential_fields if field not in article or not article[field]]
    if missing_fields:
        logger.warning(f"Missing fields: {missing_fields}")
    return len(missing_fields) <= st.session_state.VALIDATION_STRICTNESS

def format_authors_apa(authors):
    """Format authors for APA style citation"""
    if not authors:
        return "Anonymous"
        
    authors_list = []
    for author in authors:
        last_name = author.get('family', '')
        initials = ''.join([name[0] + '.' for name in author.get('given', '').split()])
        authors_list.append(f"{last_name}, {initials}")
    
    if not authors_list:
        return "Anonymous"
    elif len(authors_list) == 1:
        return authors_list[0]
    elif len(authors_list) <= 20:
        return ', '.join(authors_list[:-1]) + ', & ' + authors_list[-1]
    else:
        return ', '.join(authors_list[:19]) + ', ... ' + authors_list[-1]

def format_citation(article, style="APA"):
    """Format a citation in the specified style"""
    if not article:
        return None
    
    authors = article.get('author', [])
    authors_str = format_authors_apa(authors)
    
    year = None
    
    # Look in published-print
    if 'published-print' in article and article['published-print'] and 'date-parts' in article['published-print']:
        date_parts = article['published-print']['date-parts']
        if date_parts and len(date_parts) > 0 and len(date_parts[0]) > 0:
            year = date_parts[0][0]
    
    # Look in published-online if still None
    if not year and 'published-online' in article and article['published-online'] and 'date-parts' in article['published-online']:
        date_parts = article['published-online']['date-parts']
        if date_parts and len(date_parts) > 0 and len(date_parts[0]) > 0:
            year = date_parts[0][0]
    
    # Look in issued if still None
    if not year and 'issued' in article and article['issued'] and 'date-parts' in article['issued']:
        date_parts = article['issued']['date-parts']
        if date_parts and len(date_parts) > 0 and len(date_parts[0]) > 0:
            year = date_parts[0][0]
    
    # Default to n.d. if still None
    if not year:
        year = 'n.d.'
        
    title = article.get('title', [''])[0] if isinstance(article.get('title', []), list) else article.get('title', '')
    journal = article.get('container-title', [''])[0] if isinstance(article.get('container-title', []), list) else article.get('container-title', '')
    doi = article.get('DOI', '')
    
    citation = f"{authors_str} ({year}). {title}"
    if journal:
        citation += f". {journal}"
    if doi:
        citation += f". https://doi.org/{doi}"
    
    return citation

@st.cache_data(show_spinner=False)
def search_articles(query):
    """Search for articles using CrossRef API"""
    try:
        if not query or not isinstance(query, str):
            return []
            
        response = requests.get(
            f"https://api.crossref.org/works?query={query}&rows=10",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("items", [])
    except Exception as e:
        logger.error(f"Error fetching articles: {str(e)}")
        return []

# ----------------------------------------------------------------
# Test Functions
# ----------------------------------------------------------------

def test_theme():
    """Test theme functionality"""
    success = True
    try:
        # Check dark theme
        st.session_state.current_theme = "dark"
        theme = get_theme()
        if theme["primary"] != "#003b7a":
            success = False
            return {"success": False, "error": "Theme function did not return correct value for dark theme"}
        
        # Check light theme
        st.session_state.current_theme = "light"
        theme = get_theme()
        if theme["primary"] != "#003b7a":
            success = False
            return {"success": False, "error": "Theme function did not return correct value for light theme"}
        
        # Check invalid theme falls back to dark
        st.session_state.current_theme = "invalid_theme"
        theme = get_theme()
        if theme["bg_color"] != "#121212":
            success = False
            return {"success": False, "error": "Theme function did not fall back to dark theme for invalid theme"}
            
        return {"success": True, "message": "Theme functionality works correctly"}
    except Exception as e:
        return {"success": False, "error": f"Theme test failed with exception: {str(e)}"}

def test_session_state_initialization():
    """Test session state initialization"""
    try:
        # Clear current session state for testing
        keys = ['targets', 'test_results', 'running_test', 'progress', 
                'vulnerabilities_found', 'current_theme', 'current_page']
        for key in keys:
            if key in st.session_state:
                del st.session_state[key]
        
        # Run initialization
        initialize_session_state()
        
        # Check that all required keys exist
        missing_keys = []
        for key in keys:
            if key not in st.session_state:
                missing_keys.append(key)
                
        if missing_keys:
            return {"success": False, "error": f"Missing session state keys: {missing_keys}"}
            
        # Check initial values
        if st.session_state.targets != []:
            return {"success": False, "error": "Targets should be initialized to empty list"}
            
        if st.session_state.current_theme != "dark":
            return {"success": False, "error": "Default theme should be 'dark'"}
            
        return {"success": True, "message": "Session state initialization passed"}
    except Exception as e:
        return {"success": False, "error": f"Session state test failed with exception: {str(e)}"}

def test_card_rendering():
    """Test UI card rendering functions"""
    try:
        # Test basic card rendering
        card_html = card("Test Title", "Test Content")
        
        if "Test Title" not in card_html or "Test Content" not in card_html:
            return {"success": False, "error": "Card doesn't contain expected content"}
            
        # Test error handling in card rendering
        card_with_error = card("Error Test", None)
        if "Error Rendering Card" not in card_with_error:
            return {"success": False, "error": "Card error handling didn't work properly"}
            
        return {"success": True, "message": "Card rendering tests passed"}
    except Exception as e:
        return {"success": False, "error": f"Card rendering test failed with exception: {str(e)}"}

def test_mock_test_vectors():
    """Test the mock test vectors functionality"""
    try:
        vectors = get_mock_test_vectors()
        
        if not vectors or len(vectors) == 0:
            return {"success": False, "error": "No test vectors returned"}
            
        if "id" not in vectors[0] or "name" not in vectors[0] or "severity" not in vectors[0]:
            return {"success": False, "error": "Test vectors missing required fields"}
            
        # Check categories
        categories = set(v["category"] for v in vectors)
        if len(categories) < 2:
            return {"success": False, "error": "Test vectors should have multiple categories"}
            
        return {"success": True, "message": f"Mock test vectors return {len(vectors)} items with {len(categories)} categories"}
    except Exception as e:
        return {"success": False, "error": f"Mock test vectors test failed with exception: {str(e)}"}

def test_citation_formatting():
    """Test the citation formatting functions"""
    try:
        # Create a mock article
        article = {
            "author": [
                {"family": "Smith", "given": "John"},
                {"family": "Jones", "given": "Alice"}
            ],
            "title": ["Test Article"],
            "issued": {"date-parts": [[2023]]},
            "container-title": ["Journal of Testing"],
            "DOI": "10.1234/test"
        }
        
        # Test APA formatting
        citation = format_citation(article, "APA")
        
        if "Smith, J., & Jones, A." not in citation:
            return {"success": False, "error": "Authors not formatted correctly"}
            
        if "Test Article" not in citation:
            return {"success": False, "error": "Title not included correctly"}
            
        if "Journal of Testing" not in citation:
            return {"success": False, "error": "Journal not included correctly"}
            
        if "https://doi.org/10.1234/test" not in citation:
            return {"success": False, "error": "DOI not formatted correctly"}
            
        # Test handling of missing data
        incomplete_article = {"title": ["Test"]}
        citation = format_citation(incomplete_article)
        
        if "Anonymous" not in citation:
            return {"success": False, "error": "Missing authors not handled correctly"}
            
        return {"success": True, "message": "Citation formatting tests passed"}
    except Exception as e:
        return {"success": False, "error": f"Citation formatting test failed with exception: {str(e)}"}

def run_all_tests():
    """Run all test functions and return results"""
    results = {}
    
    # Run each test
    results["theme"] = test_theme()
    results["session_state"] = test_session_state_initialization()
    results["ui_cards"] = test_card_rendering()
    results["test_vectors"] = test_mock_test_vectors()
    results["citation"] = test_citation_formatting()
    
    # Compute overall result
    overall_success = all(result["success"] for result in results.values())
    
    return {
        "overall_success": overall_success,
        "test_results": results,
        "timestamp": datetime.now().isoformat(),
        "pass_count": sum(1 for result in results.values() if result["success"]),
        "fail_count": sum(1 for result in results.values() if not result["success"])
    }

# ----------------------------------------------------------------
# Test Runner Page
# ----------------------------------------------------------------

def render_run_tests():
    """Render the test runner page"""
    try:
        render_header()
        
        st.markdown("""
        <h2>Test Runner</h2>
        <p>Run automated tests to verify application functionality</p>
        """, unsafe_allow_html=True)
        
        # Run tests button
        if st.button("Run All Tests", type="primary", key="run_all_tests"):
            with st.spinner("Running tests..."):
                results = run_all_tests()
                
                # Save results in session state
                st.session_state.test_results = results
                
                # Show overall result
                if results["overall_success"]:
                    st.success(f"✅ All tests passed! ({results['pass_count']}/{results['pass_count'] + results['fail_count']})")
                else:
                    st.error(f"❌ Tests failed. {results['pass_count']} passed, {results['fail_count']} failed.")
                    
                # Show detailed results
                st.markdown("### Test Results")
                
                for test_name, test_result in results["test_results"].items():
                    with st.expander(f"{test_name} - {'✅ Passed' if test_result['success'] else '❌ Failed'}"):
                        if test_result["success"]:
                            st.success(test_result["message"])
                        else:
                            st.error(test_result["error"])
        
        # Targeted test selection
        st.markdown("### Run Specific Tests")
        test_options = {
            "Theme System": test_theme,
            "Session State": test_session_state_initialization,
            "UI Card Rendering": test_card_rendering,
            "Mock Test Vectors": test_mock_test_vectors,
            "Citation Formatting": test_citation_formatting
        }
        
        selected_test = st.selectbox("Select Test", list(test_options.keys()))
        
        if st.button("Run Selected Test", key="run_selected_test"):
            with st.spinner(f"Running {selected_test}..."):
                test_func = test_options[selected_test]
                result = test_func()
                
                if result["success"]:
                    st.success(f"✅ Test passed: {result['message']}")
                else:
                    st.error(f"❌ Test failed: {result['error']}")
    
    except Exception as e:
        logger.error(f"Error rendering test runner: {str(e)}")
        logger.debug(traceback.format_exc())
        st.error(f"Error in test runner: {str(e)}")

# ----------------------------------------------------------------
# Main Application Routing
# ----------------------------------------------------------------

def main():
    """Main application entry point with error handling"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Clean up threads
        cleanup_threads()
        
        # Apply CSS
        st.markdown(load_css(), unsafe_allow_html=True)
        
        # Show error message if exists
        if st.session_state.error_message:
            st.markdown(f"""
            <div class="error-message">
                <strong>Error:</strong> {st.session_state.error_message}
            </div>
            """, unsafe_allow_html=True)
            
            # Add button to clear error
            if st.button("Clear Error"):
                st.session_state.error_message = None
                safe_rerun()
        
        # Render sidebar
        sidebar_navigation()
        
        # Render content based on current page
        if st.session_state.current_page == "Dashboard":
            render_dashboard()
        elif st.session_state.current_page == "Target Management":
            render_target_management()
        elif st.session_state.current_page == "Test Configuration":
            render_test_configuration()
        elif st.session_state.current_page == "Run Assessment":
            render_run_assessment()
        elif st.session_state.current_page == "Results Analyzer":
            render_results_analyzer()
        elif st.session_state.current_page == "Report Generator":
            render_report_generator()
        elif st.session_state.current_page == "Citation Tool":
            render_citation_tool()
        elif st.session_state.current_page == "Insight Assistant":
            render_insight_assistant()
        elif st.session_state.current_page == "Run Tests":
            render_run_tests()
        else:
            # Default to dashboard if invalid page
            logger.warning(f"Invalid page requested: {st.session_state.current_page}")
            st.session_state.current_page = "Dashboard"
            render_dashboard()
    
    except Exception as e:
        logger.critical(f"Critical application error: {str(e)}")
        logger.critical(traceback.format_exc())
        st.error(f"Critical application error: {str(e)}")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()
