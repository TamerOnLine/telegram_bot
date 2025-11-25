# apps/dashboard/helpers/style.py
from __future__ import annotations

import streamlit as st


def inject_global_css() -> None:
    """حقن تنسيق بسيط لواجهة احترافية (داكنة + كروت)."""
    css = """
    <style>
    .stApp {
        background: radial-gradient(circle at top left, #0f172a 0, #020617 45%, #020617 100%);
        color: #e5e7eb;
    }
    .main-header {
        padding: 1.1rem 1.4rem;
        border-radius: 1rem;
        background: linear-gradient(135deg, #0ea5e9, #6366f1);
        color: white;
        margin-bottom: 1.3rem;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.55);
    }
    .main-header h1 {
        font-size: 1.8rem;
        margin-bottom: 0.15rem;
    }
    .main-header p {
        margin: 0;
        opacity: 0.94;
        font-size: 0.95rem;
    }
    .bot-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.1rem 0.75rem;
        border-radius: 999px;
        background: rgba(15,23,42,0.18);
        border: 1px solid rgba(226,232,240,0.35);
        font-size: 0.78rem;
    }
    .metric-card {
        padding: 0.85rem 1rem;
        border-radius: 0.9rem;
        background: rgba(15,23,42,0.9);
        border: 1px solid rgba(148,163,184,0.35);
        margin-bottom: 0.25rem;
    }
    .metric-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: .08em;
        color: #9ca3af;
    }
    .metric-value {
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 0.2rem;
        color: #e5e7eb;
    }
    .tag {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        background: rgba(15,23,42,0.85);
        border: 1px solid rgba(55,65,81,0.85);
        font-size: 0.7rem;
        color: #cbd5f5;
        margin-right: 0.3rem;
        margin-bottom: 0.3rem;
    }
    .small-muted {
        font-size: 0.8rem;
        color: #9ca3af;
    }
    .stTabs [role="tablist"] {
        gap: .35rem;
    }
    .stTabs [role="tab"] {
        padding-top: 0.3rem;
        padding-bottom: 0.3rem;
    }
    footer, #MainMenu {
        visibility: hidden;
        height: 0;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
