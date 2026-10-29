# frontend/app.py
"""
Failure Forensics Tool — Streamlit multi-page app entry point.
Run with: streamlit run frontend/app.py
"""
import sys
from pathlib import Path

# Make backend importable
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import streamlit as st

# Import pages
from pages._trace_explorer import render as render_trace_explorer

st.set_page_config(
    page_title="Failure Forensics Tool",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    section[data-testid="stSidebar"] { background: #0f172a !important; }
    section[data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }
    .sidebar-logo {
        font-size: 22px;
        font-weight: 800;
        background: linear-gradient(135deg, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .sidebar-tagline {
        font-size: 11px;
        color: #475569;
        margin-bottom: 24px;
    }
    .nav-section {
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #334155;
        font-weight: 700;
        margin: 16px 0 8px 0;
    }
    </style>
    <div class="sidebar-logo">🔬 Failure Forensics</div>
    <div class="sidebar-tagline">AI Pipeline Diagnostics Tool</div>
    <div class="nav-section">Diagnostics</div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        options=["🔭 Trace Explorer", "📊 Analytics", "🔀 Diff View"],
        label_visibility="collapsed",
    )

    st.markdown("""
    <div style="position:fixed;bottom:20px;left:0;right:0;padding:0 20px;">
      <div style="background:#1e293b;border-radius:10px;padding:12px;font-size:11px;color:#475569;">
        <div style="color:#64748b;margin-bottom:4px;">Status</div>
        <div style="color:#1DB954;font-weight:600;">● System Online</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# --- Page Router ---
if page == "🔭 Trace Explorer":
    render_trace_explorer()
elif page == "📊 Analytics":
    st.markdown("## 📊 Analytics")
    st.info("Analytics dashboard coming soon. Run the pipeline to generate trace data.")
elif page == "🔀 Diff View":
    st.markdown("## 🔀 Diff View")
    st.info("Trace diff view coming soon.")
