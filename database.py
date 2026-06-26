import os
import streamlit as st


def apply_theme():
    st.markdown("""
    <style>
    .stApp { background: #f4f7fb; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #001a35 0%, #002b5c 55%, #001f3f 100%);
    }
    [data-testid="stSidebar"] * { color: white !important; }
    .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
    .top-header {
        background: white;
        padding: 18px 24px;
        border-radius: 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.06);
        border: 1px solid #e8eef7;
        margin-bottom: 20px;
    }
    .page-title { font-size: 28px; font-weight: 800; color: #002b5c; }
    .page-subtitle { color: #67748e; margin-top: 4px; }
    .metric-card {
        padding: 22px;
        border-radius: 20px;
        color: white;
        box-shadow: 0 12px 26px rgba(0,0,0,0.13);
        min-height: 135px;
    }
    .blue-card { background: linear-gradient(135deg, #0757d8, #1198ff); }
    .orange-card { background: linear-gradient(135deg, #ff7a00, #ffb703); }
    .green-card { background: linear-gradient(135deg, #079447, #19c865); }
    .purple-card { background: linear-gradient(135deg, #6224d8, #a64cff); }
    .red-card { background: linear-gradient(135deg, #e3344f, #ff6b2c); }
    .metric-title { font-size: 14px; font-weight: 700; opacity: .95; }
    .metric-value { font-size: 36px; font-weight: 900; margin-top: 12px; }
    .metric-sub { font-size: 13px; opacity: .88; margin-top: 4px; }
    .panel {
        background: white;
        border-radius: 18px;
        padding: 20px;
        box-shadow: 0 8px 22px rgba(0,0,0,0.06);
        border: 1px solid #e8eef7;
        margin-bottom: 18px;
    }
    .login-card {
        background: linear-gradient(135deg, #001f3f, #005bea);
        color: white;
        padding: 38px;
        border-radius: 22px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 14px 34px rgba(0,0,0,.18);
    }
    .login-title { font-size: 38px; font-weight: 900; }
    .login-subtitle { font-size: 16px; opacity: .9; margin-top: 8px; }
    div.stButton > button {
        border-radius: 12px;
        border: 0;
        background: linear-gradient(135deg, #005bea, #00c6fb);
        color: white;
        font-weight: 800;
    }
    div.stButton > button:hover { color: white; filter: brightness(.95); }
    </style>
    """, unsafe_allow_html=True)


def sidebar_header():
    if os.path.exists("assets/logo.png"):
        st.sidebar.image("assets/logo.png", use_container_width=True)
    else:
        st.sidebar.markdown("# ⚓ ALPORT")
        st.sidebar.markdown("### CFS SYSTEM")
    st.sidebar.markdown("---")


def page_header(title):
    st.markdown(f"""
    <div class="top-header">
        <div class="page-title">⚓ {title}</div>
        <div class="page-subtitle">ALPORT BANJUL TERMINAL | CFS Automation System</div>
    </div>
    """, unsafe_allow_html=True)


def metric_card(col, title, value, subtitle, card_class):
    col.markdown(f"""
    <div class="metric-card {card_class}">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)
