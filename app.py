import os
import requests
import time
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import base64
import warnings
from pathlib import Path
from PIL import Image as PILImage

# Load environment variables dari .env sebelum import database
from dotenv import load_dotenv
_env_file = Path(__file__).parent / ".env"
if not _env_file.exists():
    import sys as _sys
    _sys.stderr.write("WARNING: File .env tidak ditemukan. Buat dari .env.example\n")
load_dotenv(_env_file)

from database import (  # noqa: E402
    login, get_defect_data, save_defect_data,
    get_demand_history, add_demand_row,
    get_destinasi, save_destinasi, save_hasil_rute,
)

#  Project root & subfolder paths 
BASE_DIR   = Path(__file__).parent
DIR_DATA   = BASE_DIR / "data"
DIR_MODELS = BASE_DIR / "models"
DIR_ASSETS = BASE_DIR / "assets"

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

try:
    import joblib
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from sklearn.exceptions import InconsistentVersionWarning
    warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
    warnings.filterwarnings("ignore", message=".*InconsistentVersionWarning.*")
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

#  helpers 
def get_logologo_b64():
    for name in ("logo2.png", "logo.png"):
        p = BASE_DIR / "assets" / name
        if p.exists():
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None

_logo_path = BASE_DIR / "assets" / "logo2.png"
if not _logo_path.exists():
    _logo_path = BASE_DIR / "assets" / "logo.png"
favicon   = PILImage.open(_logo_path) if _logo_path.exists() else ""

st.set_page_config(
    page_title="Agrinesia — Supply Chain Dashboard",
    page_icon=favicon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# 
# GLOBAL CSS
# 
st.markdown("""
<style>
*, html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    box-sizing: border-box;
}
#MainMenu, footer { visibility: hidden !important; }
header, [data-testid="stHeader"], .stAppToolbar { display: none !important; }
.stMainBlockContainer, .block-container { padding-top: 0 !important; margin-top: 0 !important; }
div[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarCollapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] > div > div:first-child > div[data-testid] { display: none !important; }
.st-emotion-cache-1cypcdb, [class*="sidebarHeader"], [class*="sidebarCollapse"] { display: none !important; }
section[data-testid="stSidebar"] > div > div > div:first-child > button { display: none !important; }

/*  Scrollbar  */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }

/* 
   SIDEBAR — dark
 */
section[data-testid="stSidebar"] {
    background: #1a1f2e !important;
    border-right: 1px solid #2d3548 !important;
    width: 224px !important;
    min-width: 224px !important;
}
section[data-testid="stSidebar"] > div {
    background: #1a1f2e !important;
    padding: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="collapsedControl"] { display: none !important; }
button[data-testid="collapsedControl"] { display: none !important; }
span.material-symbols-rounded,
span.material-symbols-outlined,
span.material-symbols-sharp,
span.material-icons,
i.material-icons {
    font-size: 0 !important;
    line-height: 0 !important;
    color: transparent !important;
    width: 0 !important;
    overflow: hidden !important;
    visibility: hidden !important;
}
/* Hide raw icon text leaking from date_input calendar nav */
button[aria-label="Go to previous month"] span,
button[aria-label="Go to next month"] span,
[data-baseweb="calendar"] button > span[role="img"] {
    font-size: 0 !important;
    color: transparent !important;
}
[data-testid="stFileUploadDropzone"] { position: relative !important; }
[data-testid="stFileUploadDropzone"] > div > p { display: none !important; }
[data-testid="stFileUploadDropzone"] button { font-size: 0.85rem !important; }
[data-testid="stExpander"] summary svg { display: inline-block !important; visibility: visible !important; }
[data-testid="stExpander"] summary > div > span { display: none !important; }

/*  Hide radio HANYA di sidebar  */
section[data-testid="stSidebar"] .stRadio { display: none !important; }

/*  Radio di main content (Pilih Zona) — paksa teks terlihat  */
.main div[data-testid="stRadio"],
[data-testid="stMainBlockContainer"] div[data-testid="stRadio"] {
    display: block !important;
    visibility: visible !important;
}
.main div[data-testid="stRadio"] label,
.main div[data-testid="stRadio"] label span,
.main div[data-testid="stRadio"] label p,
[data-testid="stMainBlockContainer"] div[data-testid="stRadio"] label,
[data-testid="stMainBlockContainer"] div[data-testid="stRadio"] label span,
[data-testid="stMainBlockContainer"] div[data-testid="stRadio"] label p {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    opacity: 1 !important;
    visibility: visible !important;
    display: inline !important;
}
/* Titik radio aktif hijau */
.main div[data-testid="stRadio"] [role="radio"][aria-checked="true"],
[data-testid="stMainBlockContainer"] div[data-testid="stRadio"] [role="radio"][aria-checked="true"] {
    background-color: #10b981 !important;
    border-color: #10b981 !important;
}

/*  Nav Buttons  */
section[data-testid="stSidebar"] .stButton {
    margin: 0 !important;
    padding: 0 8px !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    color: #9ca3af !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    text-align: left !important;
    padding: 10px 14px !important;
    width: 100% !important;
    display: flex !important;
    justify-content: flex-start !important;
    transition: background 0.15s, color 0.15s !important;
    box-shadow: none !important;
    margin-bottom: 2px !important;
    letter-spacing: 0 !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #252b3b !important;
    color: #f9fafb !important;
}
section[data-testid="stSidebar"] .stButton > button:active {
    background: #2d3548 !important;
}
section[data-testid="stSidebar"] .stButton > button p,
section[data-testid="stSidebar"] .stButton > button span {
    color: #9ca3af !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    margin: 0 !important;
    transition: color 0.15s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover p,
section[data-testid="stSidebar"] .stButton > button:hover span {
    color: #f9fafb !important;
}

/* 
   APP + MAIN CONTENT
 */
.stApp, .stApp > div { background: #f5f6fa !important; }
.main .block-container { padding: 0 !important; max-width: 100% !important; }
.main > div { padding: 0 !important; }

/*  Topbar  */
.topbar {
    background: #ffffff;
    border-bottom: 1px solid #eaecf0;
    padding: 18px 28px 16px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.topbar-title { font-size: 1.25rem; font-weight: 700; color: #111827; letter-spacing: -0.4px; margin: 0 0 3px; line-height: 1.3; }
.topbar-sub   { font-size: 0.8rem; color: #9ca3af; font-weight: 400; margin: 0; }
.topbar-date  { font-size: 0.75rem; color: #6b7280; background: #f9fafb; border: 1px solid #eaecf0; border-radius: 6px; padding: 5px 12px; }
.page-body    { padding: 0 28px 40px; }

[data-testid="metric-container"] { display: none !important; }

.chart-card { background: #ffffff; border: 1px solid #eaecf0; border-radius: 12px; padding: 18px 20px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); margin-bottom: 16px; }
.chart-card-title { font-size: 0.9rem; font-weight: 600; color: #111827; }
.chart-card-sub   { font-size: 0.75rem; color: #9ca3af; margin-top: 2px; }
.sec-title { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; color: #9ca3af; margin: 0 0 12px; padding-bottom: 8px; border-bottom: 1px solid #f3f4f6; }
.divider { border: none; height: 1px; background: #f3f4f6; margin: 18px 0; }

.badge { display: inline-flex; align-items: center; padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
.bg  { background: #dcfce7; color: #15803d; }
.bw  { background: #fef9c3; color: #854d0e; }
.bc  { background: #fee2e2; color: #991b1b; }

.info-note { background: #f0fdf4; border-left: 3px solid #22c55e; padding: 10px 14px; border-radius: 0 8px 8px 0; font-size: 0.83rem; color: #166534; margin-bottom: 16px; line-height: 1.6; }

/*  Radio buttons (main content) — fallback rule  */
div[data-testid="stRadio"] label {
    color: #374151 !important;
    -webkit-text-fill-color: #374151 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    opacity: 1 !important;
    visibility: visible !important;
}
div[data-testid="stRadio"] label span { color: #374151 !important; -webkit-text-fill-color: #374151 !important; }
div[data-testid="stRadio"] > div { background: transparent !important; }
div[data-testid="stToggle"] label p,
div[data-testid="stToggle"] span,
div[data-testid="stToggle"] p { color: #111827 !important; -webkit-text-fill-color: #111827 !important; }

/*  Expander  */
div[data-testid="stExpander"] {
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
div[data-testid="stExpander"] summary {
    color: #374151 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    background: #f9fafb !important;
    padding: 10px 16px !important;
    letter-spacing: 0.01em !important;
}
div[data-testid="stExpander"] summary p { color: #374151 !important; font-size: 0.85rem !important; }
div[data-testid="stExpander"] summary span { color: #374151 !important; }
div[data-testid="stExpander"] summary svg { color: #9ca3af !important; }
div[data-testid="stExpander"] > div[data-testid="stExpanderDetails"] {
    background: #ffffff !important;
    padding: 12px 16px !important;
}

.param-panel { background: #f9fafb; border: 1px solid #eaecf0; border-radius: 10px; padding: 16px 18px; }
.param-title { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #9ca3af; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #eaecf0; }

.status-card { background: #fff; border: 1px solid #eaecf0; border-radius: 12px; padding: 16px; text-align: center; }
.status-card-label { font-size: 0.7rem; font-weight: 500; color: #9ca3af; margin-bottom: 8px; }
.status-card-value { font-size: 1.8rem; font-weight: 700; color: #111827; margin-bottom: 8px; letter-spacing: -0.6px; }

.pred-card  { background: #fff; border: 1px solid #eaecf0; border-radius: 12px; padding: 22px 18px; text-align: center; }
.pred-label { font-size: 0.7rem; font-weight: 500; color: #9ca3af; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.4px; }
.pred-value { font-size: 2.8rem; font-weight: 700; color: #111827; letter-spacing: -1.5px; line-height: 1; margin-bottom: 10px; }
.pred-rec   { font-size: 0.8rem; color: #6b7280; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f3f4f6; line-height: 1.5; }

.route-card { background: #fff; border: 1px solid #eaecf0; border-radius: 8px; padding: 11px 14px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }
.route-card:hover { border-color: #d1fae5; }
.route-city   { font-size: 0.875rem; font-weight: 600; color: #111827; }
.route-detail { font-size: 0.75rem; color: #9ca3af; margin-top: 2px; }

.dmaic-wrap { display: flex; border-radius: 10px; overflow: hidden; border: 1px solid #eaecf0; margin-bottom: 20px; }
.dmaic-cell { flex: 1; padding: 12px 6px; text-align: center; font-size: 0.95rem; font-weight: 700; }
.dmaic-cell small { display: block; font-size: 0.6rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 2px; opacity: 0.7; }

.stNumberInput label, .stNumberInput p,
.stSelectbox label, .stSelectbox p,
.stSlider label, .stSlider p,
.stTextInput label, .stTextInput p,
.stTextArea label, .stTextArea p,
.stMultiSelect label, .stMultiSelect p,
.stDateInput label, .stDateInput p,
[class*="InputLabel"], [class*="inputLabel"] {
    color: #374151 !important;
    font-size: 0.83rem !important;
    font-weight: 500 !important;
    -webkit-text-fill-color: #374151 !important;
    background: transparent !important;
}

[data-testid="stNumberInput"] {
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stNumberInput"] > div {
    display: flex !important;
    align-items: center !important;
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    height: 40px !important;
}
[data-testid="stNumberInput"] input {
    background: #ffffff !important;
    color: #111827 !important;
    border: none !important;
    border-radius: 0 !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    padding: 0 12px !important;
    flex: 1 !important;
    height: 100% !important;
    -webkit-text-fill-color: #111827 !important;
}
[data-testid="stNumberInput"] input:focus { outline: none !important; box-shadow: none !important; }
[data-testid="stNumberInput"] button {
    background: #f9fafb !important;
    color: #374151 !important;
    border: none !important;
    border-left: 1px solid #e5e7eb !important;
    width: 36px !important;
    height: 100% !important;
    font-size: 1rem !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: background 0.12s !important;
}
[data-testid="stNumberInput"] button:hover { background: #f3f4f6 !important; }
[data-testid="stNumberInput"] button:first-of-type { border-left: 1px solid #e5e7eb !important; }

[data-testid="stSelectbox"] > div > div {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    color: #111827 !important;
    min-height: 40px !important;
}
[data-testid="stSelectbox"] > div > div > div { color: #111827 !important; -webkit-text-fill-color: #111827 !important; }

[data-testid="stSlider"] [role="slider"] { background: #10b981 !important; }
[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid] { background: #10b981 !important; }

.stTextInput input, .stTextArea textarea {
    background: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    font-size: 0.875rem !important;
    -webkit-text-fill-color: #111827 !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 3px rgba(16,185,129,0.1) !important;
}

[data-testid="stDataFrame"] { border-radius: 10px !important; }

.stTabs [data-baseweb="tab-list"] { gap: 0; background: #f5f6fa; border-radius: 10px; padding: 3px; border: 1px solid #eaecf0; width: fit-content; margin-bottom: 16px; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; color: #6b7280; font-size: 0.83rem; font-weight: 500; padding: 7px 16px; border: none; }
.stTabs [aria-selected="true"] { background: #ffffff !important; color: #111827 !important; font-weight: 600 !important; box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

.stButton > button[kind="primary"] { background: #16a34a !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 0.83rem !important; padding: 8px 16px !important; }
.stButton > button[kind="primary"]:hover { background: #15803d !important; }
.stButton > button[kind="secondary"] { background: #ffffff !important; color: #374151 !important; border: 1px solid #d1d5db !important; border-radius: 8px !important; font-weight: 500 !important; font-size: 0.83rem !important; }
.stButton > button[kind="secondary"]:hover { background: #f9fafb !important; }

[data-testid="stAlert"] { border-radius: 8px !important; }


/* Hide "Press Enter to submit form" hint */
[data-testid="InputInstructions"],
small[data-testid="InputInstructions"],
div[data-testid="InputInstructions"] {
    display: none !important;
}

/* Hide all material icon text leaking in widgets */
[data-testid="stBaseButton-secondary"] p,
[data-testid="stBaseButton-primary"] p,
button[kind="secondary"] p,
button[kind="primary"] p {
    display: inline !important;
}
span[data-testid="stIconMaterial"],
.stButton button span.material-symbols-rounded,
.stButton button span.material-symbols-outlined,
.stDownloadButton button span.material-symbols-rounded,
[data-testid*="Button"] span.material-symbols-rounded,
[data-testid*="Button"] span.material-symbols-outlined {
    display: none !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    font-size: 0 !important;
    color: transparent !important;
}

/* Force all plotly chart text to be black */
.js-plotly-plot .plotly .xtick text,
.js-plotly-plot .plotly .ytick text,
.js-plotly-plot .plotly .legendtext,
.js-plotly-plot .plotly .gtitle,
.js-plotly-plot .plotly text {
    fill: #111827 !important;
}
</style>
""", unsafe_allow_html=True)

#  JS: hide Material icon text 
st.markdown("""
<script>
(function() {
    const ICON_TEXTS = ['upload', 'arrow_downward', 'arrow_drop_down',
                        'expand_more', 'chevron_right',
                        'keyboard_arrow_down', 'keyboard_double_arrow_right',
                        'cloud_upload', 'attach_file'];

    function hideIconText(root) {
        root.querySelectorAll(
            'span.material-symbols-rounded, span.material-symbols-outlined, ' +
            'span.material-icons, i.material-icons'
        ).forEach(el => {
            if (ICON_TEXTS.includes(el.textContent.trim())) {
                el.style.cssText = 'font-size:0!important;color:transparent!important;' +
                                   'width:0!important;overflow:hidden!important;' +
                                   'visibility:hidden!important;';
            }
        });
    }

    hideIconText(document);
    const observer = new MutationObserver(() => hideIconText(document));
    observer.observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)


#  Login page 
def show_login_page():
    logo_b64     = get_logologo_b64()
    login_failed = st.session_state.pop('_login_failed', False)
    login_locked = st.session_state.pop('_login_locked', None)
    if login_locked:
        st.error(login_locked)

    st.markdown("""
    <style>

    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], [data-testid="stMainBlockContainer"],
    .main, .block-container {
        background: linear-gradient(135deg,#052e16 0%,#064e3b 50%,#047857 100%) !important;
        min-height: 100vh !important;
        padding: 0 !important; margin: 0 !important;
        max-width: 100% !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    [data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
    [data-testid="stStatusWidget"],#MainMenu,footer,header { display:none !important; }
    section[data-testid="stSidebar"] { display:none !important; }

    [data-testid="stHorizontalBlock"] > div:nth-child(2) {
        background: #ffffff !important;
        border-radius: 24px !important;
        padding: 32px 28px 24px !important;
        box-shadow: 0 32px 80px rgba(0,0,0,0.35) !important;
        margin-top: 5vh !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) p,
    [data-testid="stHorizontalBlock"] > div:nth-child(2) span,
    [data-testid="stHorizontalBlock"] > div:nth-child(2) div {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput label,
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput p {
        font-size: 0.67rem !important; font-weight: 700 !important;
        color: #374151 !important; letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        -webkit-text-fill-color: #374151 !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput input {
        background: #f0fdf4 !important;
        border: none !important;
        border-radius: 0 !important;
        color: #111827 !important;
        font-size: 0.9rem !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        -webkit-text-fill-color: #111827 !important;
        padding: 11px 14px !important;
        box-shadow: none !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput input:-webkit-autofill,
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput input:-webkit-autofill:hover,
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput input:-webkit-autofill:focus {
        -webkit-box-shadow: 0 0 0px 1000px #f0fdf4 inset !important;
        -webkit-text-fill-color: #111827 !important;
        background-color: #f0fdf4 !important;
        transition: background-color 9999s ease-in-out 0s !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput input:focus {
        background: #fff !important;
        -webkit-box-shadow: 0 0 0px 1000px #fff inset !important;
        box-shadow: none !important;
        outline: none !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput button {
        background: #059669 !important;
        border-radius: 0 8px 8px 0 !important;
        border: none !important;
        color: #fff !important;
        box-shadow: none !important;
        outline: none !important;
        margin: 0 !important;
        padding: 0 12px !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput [data-baseweb="input"] {
        border-radius: 10px !important;
        overflow: hidden !important;
        border: 1.5px solid #d1fae5 !important;
        background: #f0fdf4 !important;
        gap: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput [data-baseweb="base-input"] {
        background: transparent !important;
        gap: 0 !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stFormSubmitButton button {
        width: 100% !important;
        background: linear-gradient(135deg,#059669,#047857) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        padding: 13px !important;
        box-shadow: 0 4px 18px rgba(5,150,105,0.45) !important;
        margin-top: 4px !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stFormSubmitButton button:hover {
        background: linear-gradient(135deg,#047857,#065f46) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stFormSubmitButton { overflow: hidden !important; }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) [data-testid="stForm"] {
        border: none !important; padding: 0 !important;
        background: transparent !important; overflow: visible !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) > div > div > div > div:last-child > div[data-testid="stFormSubmitButton"] ~ * { display: none !important; }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) > div { overflow: hidden !important; }
    [data-baseweb="tooltip"],[role="tooltip"],div[class*="Tooltip"],div[id*="tooltip"] {
        display: none !important; visibility: hidden !important;
        opacity: 0 !important; pointer-events: none !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput > div > div > div ~ * { display: none !important; }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput input:focus::placeholder,
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput input:focus::-webkit-input-placeholder {
        color: transparent !important; opacity: 0 !important;
    }
    [data-testid="stHorizontalBlock"] > div:nth-child(2) .stTextInput input:focus {
        background: #fff !important;
        -webkit-box-shadow: 0 0 0px 1000px #fff inset !important;
        box-shadow: none !important; outline: none !important;
        caret-color: #059669 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1.2, 1, 1.2])
    with mid:
        if logo_b64:
            st.markdown(f'<div style="text-align:center;margin-bottom:8px;">'
                        f'<img src="data:image/png;base64,{logo_b64}" style="height:52px;object-fit:contain;"></div>',
                        unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-size:1.55rem;font-weight:800;'
                    'color:#064e3b;letter-spacing:-0.5px;margin-bottom:4px;">Agrinesia</div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;font-size:0.63rem;font-weight:700;color:#9ca3af;'
                    'letter-spacing:0.14em;text-transform:uppercase;margin-bottom:24px;">'
                    'Supply Chain Intelligence System</div>',
                    unsafe_allow_html=True)

        if login_failed:
            st.error("Username atau password salah.")

        with st.form("login_form", clear_on_submit=False):
            uname     = st.text_input("Username", placeholder="Masukkan username")
            pw        = st.text_input("Password",  placeholder="Masukkan password", type="password")
            submitted = st.form_submit_button("Masuk", width='stretch')

        st.markdown('<div style="text-align:center;font-size:0.63rem;color:#9ca3af;margin-top:16px;">'
                    'PT Agrinesia Raya &nbsp;·&nbsp; Internal Use Only</div>',
                    unsafe_allow_html=True)

    if submitted:
        if not uname or not pw:
            st.session_state['_login_failed'] = True
            st.rerun()
        else:
            try:
                user = login(uname, pw)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user      = user
                    st.rerun()
                else:
                    st.session_state['_login_failed'] = True
                    st.rerun()
            except PermissionError as _lock_err:
                st.session_state['_login_locked'] = str(_lock_err)
                st.rerun()


#  SEED 
np.random.seed(42)
random.seed(42)

#  Auth gate 
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user      = None

if not st.session_state.logged_in:
    show_login_page()
    st.stop()

current_user = st.session_state.user

#  DATA 
def gen_temp(days=60):
    dates = pd.date_range(end=datetime.today(), periods=days, freq='D')
    base  = 85 + 5*np.sin(np.linspace(0, 4*np.pi, days))
    return pd.DataFrame({'Tanggal': dates, 'Suhu': (base + np.random.normal(0,1.5,days)).round(1)})

def gen_defect(weeks=24):
    dates  = pd.date_range(end=datetime.today(), periods=weeks, freq='7D')
    defect = np.abs(np.random.normal(2.8, 1.1, len(dates))).round(2)
    return pd.DataFrame({'Minggu': list(dates), 'Defect': list(defect)})

def gen_orders():
    m = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agt','Sep','Okt','Nov','Des']
    f = [920,870,1010,940,990,1050,1080,1020,960,1100,1030,980]
    u = [80,130,90,110,70,60,50,90,120,40,70,80]
    return pd.DataFrame({'Bulan': m, 'Terpenuhi': f, 'Tidak Terpenuhi': u})

C = {'green':'#10b981','dark':'#0f172a','amber':'#f59e0b',
     'red':'#ef4444','grid':'#f8fafc','muted':'#94a3b8','blue':'#3b82f6'}

def bl(h=320, title=""):
    return dict(
        height=h, paper_bgcolor='#f5f6fa', plot_bgcolor='#f5f6fa',
        font=dict(family='system-ui', color='#111827', size=11),
        margin=dict(l=4, r=8, t=8, b=4),
        xaxis=dict(gridcolor='#e5e7eb', showgrid=True, zeroline=False,
                   linecolor='#d1d5db', tickfont=dict(size=11, color='#111827'),
                   title_font=dict(color='#111827')),
        yaxis=dict(gridcolor='#e5e7eb', showgrid=True, zeroline=False,
                   linecolor='#d1d5db', tickfont=dict(size=11, color='#111827'),
                   title_font=dict(color='#111827')),
        legend=dict(bgcolor='rgba(0,0,0,0)', borderwidth=0,
                    font=dict(size=11, color='#111827'), orientation='h',
                    y=1.08, x=0),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='white', bordercolor='#e5e7eb',
                        font=dict(family='system-ui', size=12, color='#111827')),
    )

# 
# SIDEBAR
# 
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

NAV = [
    ("Dashboard",            "Dashboard"),
    ("Peramalan Permintaan", "Peramalan Permintaan"),
    ("Prediksi Suhu Zona",   "Prediksi Suhu Zona"),
    ("Pengendalian Mutu",    "Pengendalian Mutu"),
    ("Optimasi Distribusi",  "Optimasi Distribusi"),
]
with st.sidebar:
    logo_b64 = get_logologo_b64()
    logo_img = (f'<img src="data:image/png;base64,{logo_b64}" '
            f'style="height:36px;object-fit:contain;display:block;">') if logo_b64 else ""

    st.markdown(f"""
    <div style="padding:20px 16px 14px;border-bottom:1px solid #2d3548;margin-bottom:6px;">
        {logo_img}
        <div style="margin-top:10px;font-size:0.9rem;font-weight:700;color:#f9fafb;">Agrinesia</div>
        <div style="font-size:0.72rem;color:#6b7280;margin-top:2px;">Supply Chain System</div>
    </div>
    <div style="padding:10px 16px 6px;font-size:0.6rem;font-weight:700;
         letter-spacing:1px;text-transform:uppercase;color:#4b5563;">Menu</div>
    """, unsafe_allow_html=True)

    for nav_key, nav_label in NAV:
        if st.button(nav_label, key=f"nav_{nav_key}", width='stretch'):
            st.session_state.page = nav_key
            st.rerun()

    st.markdown(f"""
    <div style="margin-top:20px;padding:12px 16px;border-top:1px solid #2d3548;">
        <div style="font-size:0.68rem;color:#6b7280;line-height:1.9;">
            <span style="color:#9ca3af;">Login sebagai</span><br>
            <b style="color:#d1d5db;">{current_user['nama']}</b>
            <span style="background:#1f2937;color:#6b7280;font-size:0.6rem;
                  padding:1px 6px;border-radius:8px;margin-left:4px;">{current_user['role']}</span><br>
            <span style="color:#4b5563;">PT Agrinesia Raya · {datetime.now().strftime("%d %b %Y")}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Keluar", key="btn_logout", width='stretch'):
        st.session_state.logged_in = False
        st.session_state.user      = None
        st.rerun()

page = st.session_state.page

active_map = {
    "Dashboard":            1,
    "Peramalan Permintaan": 2,
    "Prediksi Suhu Zona":   3,
    "Pengendalian Mutu":    4,
    "Optimasi Distribusi":  5,
}
active_idx = active_map.get(page, 1)
st.markdown(f"""
<style>
section[data-testid="stSidebar"] .stButton:nth-of-type({active_idx}) > button {{
    background: #252b3b !important;
    border-left: 3px solid #10b981 !important;
    padding-left: 11px !important;
    color: #10b981 !important;
}}
section[data-testid="stSidebar"] .stButton:nth-of-type({active_idx}) > button p,
section[data-testid="stSidebar"] .stButton:nth-of-type({active_idx}) > button span {{
    color: #10b981 !important;
    font-weight: 600 !important;
}}
</style>
""", unsafe_allow_html=True)

#  TOPBAR helper 
def topbar(title, sub):
    now = datetime.now().strftime("%d %b %Y")
    st.markdown(f"""
    <div class="topbar">
        <div>
            <p class="topbar-title">{title}</p>
            <p class="topbar-sub">{sub}</p>
        </div>
        <div class="topbar-date">{now}</div>
    </div>
    <div class="page-body">
    """, unsafe_allow_html=True)

def chart_card(title, chart_fig, subtitle=""):
    sub_html = f'<p style="font-size:0.75rem;color:#9ca3af;margin:2px 0 0 0;">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
    <div style="background:#ffffff;border:1px solid #eaecf0;border-radius:12px;
         padding:18px 20px 6px;box-shadow:0 1px 3px rgba(0,0,0,0.04);margin-bottom:4px;">
        <div style="font-size:0.92rem;font-weight:600;color:#111827;
             letter-spacing:-0.1px;margin-bottom:2px;">{title}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.plotly_chart(chart_fig, width='stretch', config={'displayModeBar': False})

def skpi(col, label, value, delta=None, up=True):
    if delta:
        dc = "#10b981" if up else "#ef4444"
        db = "#f0fdf4" if up else "#fef2f2"
        ar = "↑" if up else "↓"
        delta_html = f"""<div style="display:inline-flex;align-items:center;gap:3px;
            background:{db};color:{dc};font-size:0.72rem;font-weight:600;
            padding:2px 7px;border-radius:20px;margin-top:8px;">{ar} {delta}</div>"""
    else:
        delta_html = ""
    col.markdown(f"""
    <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;
         padding:16px 18px;box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="font-size:0.77rem;font-weight:600;color:#374151;margin-bottom:6px;">{label}</div>
        <div style="font-size:1.55rem;font-weight:700;color:#111827;
             letter-spacing:-0.5px;line-height:1;">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# 
# PAGE — DASHBOARD
# 
def load_demand_excel(src):
    df_raw = pd.read_excel(src, sheet_name='Black Forest', header=0)
    df_raw['Date'] = pd.to_datetime(df_raw['Date'])
    df_agg = df_raw.groupby(['Date','Produk'])['Qty'].sum().reset_index()
    df_agg['Date'] = df_agg['Date'].dt.strftime('%Y-%m-%d')
    df_agg.columns = ['Tanggal','Produk','Permintaan']
    df_agg = df_agg[df_agg['Produk'] == 'LBS BLACK FOREST'].reset_index(drop=True)
    return df_agg

def load_default():
    csv_path = str(BASE_DIR / 'data' / 'data_blackforest.csv')
    df_default  = pd.read_csv(csv_path)
    df_default['Produk'] = 'LBS BLACK FOREST'
    return df_default[['Tanggal','Produk','Permintaan']].reset_index(drop=True)

@st.cache_data(ttl=60, show_spinner=False)
def _cached_demand():
    return get_demand_history()

_dh_rows = _cached_demand()
if _dh_rows:
    st.session_state.demand_history = pd.DataFrame([
        {"Tanggal": str(r["tanggal"]), "Permintaan": r["permintaan"], "Produk": r["produk"]}
        for r in _dh_rows
    ])
    st.session_state.demand_history["Tanggal"] = pd.to_datetime(st.session_state.demand_history["Tanggal"])
elif "demand_history" not in st.session_state:
    xlsx_path = str(BASE_DIR / "data" / "PT_Agrinesia_-_Volume___Traffic__LBS_Black_Forest_.xlsx")
    if os.path.exists(xlsx_path):
        st.session_state.demand_history = load_demand_excel(xlsx_path)
    else:
        st.session_state.demand_history = load_default()


if page == "Dashboard":
    topbar("Dashboard",
           "Ringkasan kinerja operasional supply chain PT Agrinesia Raya")

    def kpi_card(col, label, value, delta, delta_up=True, accent="#10b981"):
        delta_color = "#10b981" if delta_up else "#ef4444"
        delta_bg    = "#f0fdf4" if delta_up else "#fef2f2"
        arrow       = "↑" if delta_up else "↓"
        col.markdown(f"""
        <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:14px;
             padding:18px 20px 16px;box-shadow:0 1px 4px rgba(0,0,0,0.05);
             position:relative;overflow:hidden;">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;
                 background:{accent};border-radius:14px 14px 0 0;"></div>
            <div style="margin-bottom:12px;">
                <div style="font-size:0.8rem;font-weight:600;color:#374151;">{label}</div>
            </div>
            <div style="font-size:1.8rem;font-weight:700;color:#111827;
                 letter-spacing:-0.8px;line-height:1;margin-bottom:10px;">{value}</div>
            <div style="display:inline-flex;align-items:center;gap:4px;
                 background:{delta_bg};color:{delta_color};
                 font-size:0.75rem;font-weight:600;padding:3px 8px;border-radius:20px;">
                {arrow} {delta}
            </div>
        </div>
        """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap="small")
    kpi_card(c1, "Permintaan Bulan Ini",    "83.775 unit",  "+3.2%",  True,  "#10b981")
    kpi_card(c2, "Avg. Suhu Zona (°C)",     "147.3 °C",     "+1.2%",  True,  "#3b82f6")
    kpi_card(c3, "Order Fulfillment Rate",  "93.6 %",       "+1.4%",  True,  "#3b82f6")
    kpi_card(c4, "Defect Rate",             "2.8 %",        "−0.3%",  True,  "#ef4444")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        dh = st.session_state.get('demand_history', pd.DataFrame())
        if not dh.empty:
            df_trend = dh.copy()
            df_trend['Tanggal']    = pd.to_datetime(df_trend['Tanggal'])
            df_trend['Permintaan'] = pd.to_numeric(df_trend['Permintaan'], errors='coerce').fillna(0)
            df_trend['Kuartal']    = df_trend['Tanggal'].dt.to_period('Q').dt.to_timestamp()
            df_q = (
                df_trend.groupby('Kuartal')['Permintaan']
                .sum().reset_index()
                .rename(columns={'Kuartal': 'Tanggal'})
            )
            df_q['MA'] = df_q['Permintaan'].rolling(2, min_periods=1).mean()
            yr_min = df_trend['Tanggal'].dt.year.min()
            yr_max = df_trend['Tanggal'].dt.year.max()
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_q['Tanggal'], y=df_q['Permintaan'],
                fill='tozeroy', fillcolor='rgba(16,185,129,0.07)',
                line=dict(color=C['green'], width=2.5), name='Permintaan',
                mode='lines+markers', marker=dict(size=6, color=C['green']),
                hovertemplate='%{x|%Y}<br><b>%{y:,} unit</b><extra></extra>'
            ))
            fig.add_trace(go.Scatter(
                x=df_q['Tanggal'], y=df_q['MA'],
                line=dict(color=C['amber'], width=1.5, dash='dot'),
                name='Moving Avg', hovertemplate='MA: %{y:,.0f}<extra></extra>'
            ))
            fig.update_layout(**bl(265))
            chart_card("Tren Permintaan", fig, f"{yr_min}–{yr_max} · Per Kuartal")
        else:
            st.info("Data belum tersedia.")

    with col2:
        # Tren Suhu Zona 1-4 dari data asli
        try:
            _df_suhu = pd.read_excel(DIR_DATA / "Steam_Tunnel_5__Lengkap___9_.xlsx")
            _suhu_cols = ['Suhu Zona 1 (°C)', 'Suhu Zona 2 (°C)', 'Suhu Zona 3 (°C)', 'Suhu Zona 4 (°C)']
            for _c in _suhu_cols:
                _df_suhu[_c] = pd.to_numeric(_df_suhu[_c], errors='coerce')
            _df_suhu['Timestamp'] = pd.to_datetime(_df_suhu['Timestamp'])
            _df_suhu = _df_suhu.dropna(subset=_suhu_cols).copy()
            _df_suhu['Date'] = _df_suhu['Timestamp'].dt.date
            _daily_suhu = _df_suhu.groupby('Date')[_suhu_cols].mean().reset_index()
            _daily_suhu['Date'] = pd.to_datetime(_daily_suhu['Date'])
            _zona_colors = {"Suhu Zona 1 (°C)": "#3b82f6", "Suhu Zona 2 (°C)": "#10b981",
                            "Suhu Zona 3 (°C)": "#f59e0b", "Suhu Zona 4 (°C)": "#8b5cf6"}
            _zona_labels = {"Suhu Zona 1 (°C)": "Zona 1", "Suhu Zona 2 (°C)": "Zona 2",
                            "Suhu Zona 3 (°C)": "Zona 3", "Suhu Zona 4 (°C)": "Zona 4"}
            fig2 = go.Figure()
            for _col in _suhu_cols:
                fig2.add_trace(go.Scatter(
                    x=_daily_suhu['Date'], y=_daily_suhu[_col].round(2),
                    mode='lines+markers',
                    line=dict(color=_zona_colors[_col], width=1.8),
                    marker=dict(size=5),
                    name=_zona_labels[_col],
                    hovertemplate=f'{_zona_labels[_col]}<br>%{{x|%d %b %Y}}<br><b>%{{y:.1f}} °C</b><extra></extra>'
                ))
            _suhu_layout = bl(295)
            _suhu_layout['yaxis'].update(title='Suhu (°C)', range=[80, 115])
            fig2.update_layout(**_suhu_layout)
            chart_card("Tren Suhu Zona 1–4", fig2, "Rata-rata harian · Steam Tunnel data asli")
        except Exception:
            st.info("File data suhu tidak ditemukan di folder data/.")

    col3, col4 = st.columns(2, gap="medium")

    with col3:
        df_o = gen_orders()
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=df_o['Bulan'], y=df_o['Terpenuhi'],
                              name='Terpenuhi', marker_color=C['green'], marker_line_width=0))
        fig3.add_trace(go.Bar(x=df_o['Bulan'], y=df_o['Tidak Terpenuhi'],
                              name='Tidak Terpenuhi', marker_color='#fca5a5', marker_line_width=0))
        fig3.update_layout(**bl(295), barmode='stack')
        chart_card("Order Fulfillment", fig3, "Terpenuhi vs tidak terpenuhi per bulan")

    with col4:
        # Pareto diagram defect (sama dengan modul Pengendalian Mutu)
        _pareto_d = {"Jenis Defect": ["Tinggi kurang dari 4 cm","Basah","Belah","Permukaan kue Kering","Warna kurang sesuai","Tekstur Crumbling","Bantet"],
                     "Frekuensi": [62, 45, 15, 11, 11, 5, 0]}
        _df_p = pd.DataFrame(_pareto_d).sort_values("Frekuensi", ascending=False).reset_index(drop=True)
        _total = _df_p["Frekuensi"].sum()
        _df_p["kum"] = (_df_p["Frekuensi"].cumsum() / _total * 100).round(2)
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            x=_df_p["Jenis Defect"], y=_df_p["Frekuensi"],
            name="Frekuensi", marker_color=C["green"], yaxis="y1",
            text=_df_p["Frekuensi"], textposition="outside",
            textfont=dict(size=10, color="#111827"),
        ))
        fig4.add_trace(go.Scatter(
            x=_df_p["Jenis Defect"], y=_df_p["kum"],
            name="% Kumulatif", mode="lines+markers",
            line=dict(color=C["red"], width=2),
            marker=dict(color=C["red"], size=6),
            yaxis="y2",
        ))
        fig4.add_hline(y=80, line_dash="dot", line_color=C["amber"],
                       annotation_text="80%", annotation_position="top right",
                       annotation_font=dict(size=9, color=C["amber"]), yref="y2")
        _lp = bl(295)
        _lp["yaxis"].update(title="Frekuensi", gridcolor=C["grid"],
                             range=[0, _df_p["Frekuensi"].max() * 1.3])
        _lp["yaxis2"] = dict(title="% Kumulatif", overlaying="y", side="right",
                              range=[0, 130], tickformat=".0f", ticksuffix="%", showgrid=False)
        _lp["xaxis"].update(tickangle=-20, tickfont=dict(size=9))
        _lp["bargap"] = 0.3
        _lp["legend"] = dict(orientation="h", y=1.1, x=0.5, xanchor="center", font=dict(size=10))
        fig4.update_layout(**_lp)
        chart_card("Pareto Defect", fig4, "Frekuensi jenis defect · 149 total")

    st.markdown("</div>", unsafe_allow_html=True)


# 
# PAGE — PERAMALAN PERMINTAAN
# 
elif page == "Peramalan Permintaan":
    topbar("Peramalan Permintaan",
           "Model Ensemble (XGBoost + LightGBM + CatBoost) — peramalan permintaan harian")

    @st.cache_resource
    def load_demand_model():
        warnings.filterwarnings("ignore")
        m = joblib.load(BASE_DIR / "models" / "model_ensemble_blackforest.pkl")
        return m

    if not ML_AVAILABLE:
        st.error("Install: pip install joblib scikit-learn xgboost lightgbm catboost")
        st.stop()

    try:
        dem_model = load_demand_model()
        feat_names = dem_model['features']
        weights     = dem_model['weights']
        demand_model_ok = True
    except Exception as e:
        st.error(f"Gagal memuat model: {e}")
        demand_model_ok = False

    if not demand_model_ok:
        st.stop()

    def ensemble_predict(df_feat):
        X = df_feat[feat_names]
        p_xgb = dem_model['xgb'].predict(X)
        p_lgb = dem_model['lgb'].predict(X)
        p_cat = dem_model['cat'].predict(X)
        return weights[0]*p_xgb + weights[1]*p_lgb + weights[2]*p_cat

    def build_features(df_hist, target_dates):
        LEBARAN = {
            2022: pd.Timestamp('2022-05-02'),
            2023: pd.Timestamp('2023-04-22'),
            2024: pd.Timestamp('2024-04-10'),
            2025: pd.Timestamp('2025-03-30'),
            2026: pd.Timestamp('2026-03-20'),
        }
        RAMADHAN_START = {yr: (leb - pd.Timedelta(days=30)) for yr, leb in LEBARAN.items()}

        rows = []
        hist = list(df_hist['Permintaan'].values)

        for td in target_dates:
            n_hist = len(hist)
            lag1_raw  = hist[-1]  if n_hist >= 1  else 0
            lag7_raw  = hist[-7]  if n_hist >= 7  else lag1_raw
            lag14_raw = hist[-14] if n_hist >= 14 else lag7_raw
            ma7_raw   = np.mean(hist[-7:])  if n_hist >= 7  else np.mean(hist)
            lag1  = np.log1p(lag1_raw)
            lag7  = np.log1p(lag7_raw)
            lag14 = np.log1p(lag14_raw)
            ma7   = np.log1p(ma7_raw)
            std7  = np.std(np.log1p(hist[-7:]))  if n_hist >= 7  else 0
            std30 = np.std(np.log1p(hist[-30:])) if n_hist >= 30 else std7

            td_dt = pd.Timestamp(td)
            dow   = td_dt.dayofweek
            is_we = int(dow >= 5)
            dsin  = np.sin(2*np.pi*dow/7)
            dcos  = np.cos(2*np.pi*dow/7)

            yr = td_dt.year
            leb_date  = LEBARAN.get(yr, LEBARAN.get(2025))
            ram_start = RAMADHAN_START.get(yr, RAMADHAN_START.get(2025))
            ram_end   = leb_date - pd.Timedelta(days=1)
            days_to_leb = (td_dt - leb_date).days
            is_leb   = int(abs(days_to_leb) <= 3)
            is_ram   = int(ram_start <= td_dt <= ram_end)
            leb_prox = max(0, 10 - abs(days_to_leb))
            leb_sq   = leb_prox ** 2
            month, day = td_dt.month, td_dt.day
            is_nat   = int((month == 12 and day >= 24) or (month == 1 and day <= 2))

            rows.append({
                'lag_1': lag1, 'lag_7': lag7, 'lag_14': lag14,
                'ma_7': ma7, 'std_7': std7, 'std_30': std30,
                'dayofweek': dow, 'is_weekend': is_we,
                'dow_sin': dsin, 'dow_cos': dcos,
                'is_lebaran': is_leb, 'is_ramadhan': is_ram,
                'lebaran_proximity': leb_prox,
                'lebaran_proximity_sq': leb_sq,
                'is_nataru': is_nat,
            })
            tmp_feat = pd.DataFrame([rows[-1]])[feat_names]
            pred_log = float(ensemble_predict(tmp_feat)[0])
            pred_val = float(np.expm1(pred_log))
            hist.append(max(0, pred_val))

        pred_log_arr = np.array(hist[len(df_hist):])
        return pd.DataFrame(rows)[feat_names], pred_log_arr

    tab_data, tab_forecast, tab_eval = st.tabs([
        "Data Historis", "Hasil Peramalan", "Evaluasi Model",
    ])

    with tab_data:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-note">
            Input dan edit data historis permintaan/penjualan. Data ini akan digunakan
            sebagai basis fitur lag, moving average, dan standar deviasi untuk model peramalan.
        </div>""", unsafe_allow_html=True)

        with st.expander("Upload Data Baru (opsional)", expanded=False):
            st.caption("Format: Excel (.xlsx) sheet 'Black Forest', kolom: Date, Produk, Qty.")
            uploaded_file = st.file_uploader("Pilih file Excel", type=["xlsx"], key="dp_upload",
                label_visibility="collapsed")
            if uploaded_file is not None:
                try:
                    st.session_state.demand_history = load_demand_excel(uploaded_file)
                    st.success(f"Data berhasil dimuat — {len(st.session_state.demand_history):,} baris")
                    st.rerun()
                except Exception as _e:
                    st.error(f"Gagal membaca file: {_e}")
            col_reset, _ = st.columns([1, 4])
            if col_reset.button("Reset ke Default", key="dp_reset_default", width='stretch'):
                st.session_state.demand_history = load_default()
                st.rerun()

        # ── Row 1: Filter controls ─────────────────────────────────────
        fr1, fr2 = st.columns([1, 1], gap="medium")
        with fr1:
            sel_produk = st.selectbox("Filter Produk", ["Semua", "LBS BLACK FOREST"], key="dp_produk")
        with fr2:
            n_show = st.number_input("Tampilkan N hari terakhir", 7, 90, 30, key="dp_nshow")

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        # ── Row 2: Tambah data form ────────────────────────────────────
        st.markdown("**Tambah Data Baru**")
        fa1, fa2, fa3, fa4 = st.columns([2, 1, 2, 1], gap="small")
        with fa1:
            _add_date_str = st.text_input("Tanggal (yyyy-mm-dd)", key="dp_date", placeholder="2026-05-10")
            try:
                import datetime as _dt
                _add_date = _dt.date.fromisoformat(_add_date_str) if _add_date_str else _dt.date.today()
            except ValueError:
                _add_date = _dt.date.today()
        with fa2:
            _add_val = st.number_input("Permintaan", 0, 5000, 450, key="dp_val")
        with fa3:
            _add_prod = st.selectbox("Produk", ["LBS BLACK FOREST"], index=0, key="dp_addprod")
        with fa4:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Tambah", key="dp_add", type="primary", width='stretch'):
                new_row = pd.DataFrame([{'Tanggal': str(_add_date), 'Permintaan': _add_val, 'Produk': _add_prod}])
                if add_demand_row(str(_add_date), int(_add_val), _add_prod, current_user["username"]):
                    _cached_demand.clear()
                    st.success(f"Data {_add_date} ditambahkan.")
                    st.rerun()
                else:
                    st.error("Gagal menyimpan data ke database.")

        df_hist_raw = st.session_state.demand_history.copy()
        if sel_produk != "Semua":
            df_hist_show = df_hist_raw[df_hist_raw['Produk']==sel_produk].tail(n_show)
        else:
            df_hist_show = df_hist_raw.tail(n_show)

        df_hist_show = df_hist_show.copy()
        df_hist_show['Tanggal'] = pd.to_datetime(df_hist_show['Tanggal'], errors='coerce').dt.date
        df_edited = st.data_editor(
            df_hist_show,
            column_config={
                'Tanggal'    : st.column_config.DateColumn("Tanggal"),
                'Permintaan' : st.column_config.NumberColumn("Permintaan (unit)", min_value=0),
                'Produk'     : st.column_config.SelectboxColumn("Produk", options=["LBS BLACK FOREST"]),
            },
            num_rows="dynamic", hide_index=True, width=900, key="dp_editor"
        )

        col_sv, col_rs = st.columns([1, 4])
        if col_sv.button("Simpan Perubahan", type="primary", key="dp_save"):
            df_to_save = df_edited.copy()
            df_to_save['Tanggal'] = df_to_save['Tanggal'].astype(str)
            st.session_state.demand_history.update(df_to_save)
            st.success("Data tersimpan.")
        if col_rs.button("Reset ke Default", key="dp_reset"):
            del st.session_state['demand_history']
            st.rerun()

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        df_val = df_hist_raw.copy()
        df_val['Permintaan'] = pd.to_numeric(df_val['Permintaan'], errors='coerce')
        n_null = df_val['Permintaan'].isna().sum()
        n_neg  = (df_val['Permintaan'] < 0).sum()
        n_out  = (df_val['Permintaan'] > df_val['Permintaan'].mean() + 3*df_val['Permintaan'].std()).sum()

        vc1,vc2,vc3,vc4 = st.columns(4, gap="small")
        skpi(vc1, "Total Data",    f"{len(df_val)} hari")
        skpi(vc2, "Missing Value", f"{n_null}", f"{n_null} baris" if n_null else "OK", n_null==0)
        skpi(vc3, "Nilai Negatif", f"{n_neg}",  "Ada!" if n_neg else "OK", n_neg==0)
        skpi(vc4, "Outlier (3σ)",  f"{n_out}",  f"{n_out} titik" if n_out else "OK", n_out==0)

        df_chart = df_hist_raw.copy()
        df_chart['Tanggal']    = pd.to_datetime(df_chart['Tanggal'])
        df_chart['Permintaan'] = pd.to_numeric(df_chart['Permintaan'], errors='coerce')
        df_chart = df_chart.sort_values('Tanggal').dropna()

        fig_h = go.Figure()
        for prod, color in [("LBS BLACK FOREST","#10b981")]:
            dfp = df_chart[df_chart['Produk']==prod]
            if len(dfp):
                fig_h.add_trace(go.Scatter(x=dfp['Tanggal'], y=dfp['Permintaan'],
                    mode='lines+markers', name=prod,
                    line=dict(color=color, width=1.8), marker=dict(size=4)))
        lh = bl(280)
        lh['yaxis']['title'] = 'Permintaan (unit)'
        fig_h.update_layout(**lh)
        chart_card("Historis Permintaan per Produk", fig_h)

    with tab_forecast:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-note">
            Model <b>Ensemble (XGBoost 40% + LightGBM 20% + CatBoost 40%)</b>
            memprediksi permintaan harian ke depan berdasarkan fitur lag, moving average,
            dan pola musiman kalender Indonesia.
        </div>""", unsafe_allow_html=True)

        pc1, pc2, pc3 = st.columns([1,1,2], gap="small")
        with pc1:
            f_produk = st.selectbox("Produk", ["LBS BLACK FOREST"], key="fp_prod")
        with pc2:
            f_hari   = st.selectbox("Periode Forecast", [7,14,30,60,90],
                                     format_func=lambda x: f"{x} Hari", key="fp_hari")
        with pc3:
            f_conf   = st.checkbox("Tampilkan Confidence Interval (±1.5σ)", value=True, key="fp_ci")
            run_fc   = st.button("Jalankan Peramalan", type="primary", key="fp_run")

        if run_fc or "forecast_result" not in st.session_state:
            df_base = st.session_state.demand_history.copy()
            df_base = df_base[df_base['Produk'] == f_produk].copy()
            df_base['Tanggal']    = pd.to_datetime(df_base['Tanggal'])
            df_base['Permintaan'] = pd.to_numeric(df_base['Permintaan'], errors='coerce').fillna(0)
            df_base = df_base.sort_values('Tanggal').tail(90)

            if df_base.empty:
                st.warning("Data historis untuk produk ini kosong.")
                st.stop()

            future_dates = pd.date_range(
                start=df_base['Tanggal'].iloc[-1] + timedelta(days=1), periods=f_hari)

            with st.spinner("Menjalankan model ensemble..."):
                _, forecasts = build_features(df_base, future_dates)

            forecasts = np.clip(forecasts, 0, None).astype(int)
            hist_std  = df_base['Permintaan'].std()
            ci_hi = (forecasts + 1.5*hist_std).astype(int)
            ci_lo = np.clip(forecasts - 1.5*hist_std, 0, None).astype(int)

            st.session_state.forecast_result = {
                'dates': future_dates, 'forecast': forecasts,
                'ci_hi': ci_hi, 'ci_lo': ci_lo,
                'df_base': df_base, 'produk': f_produk, 'hari': f_hari,
            }

        if "forecast_result" in st.session_state:
            fr = st.session_state.forecast_result
            forecasts    = fr['forecast']
            future_dates = fr['dates']
            df_base      = fr['df_base']
            ci_hi, ci_lo = fr['ci_hi'], fr['ci_lo']

            k1,k2,k3,k4 = st.columns(4, gap="small")
            skpi(k1, "Rata-rata Forecast",  f"{int(forecasts.mean()):,} unit")
            skpi(k2, "Forecast Tertinggi",  f"{int(forecasts.max()):,} unit")
            skpi(k3, "Forecast Terendah",   f"{int(forecasts.min()):,} unit")
            skpi(k4, "Total Periode",       f"{fr['hari']} Hari")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

            fig_fc = go.Figure()
            fig_fc.add_trace(go.Scatter(
                x=df_base['Tanggal'].tail(30), y=df_base['Permintaan'].tail(30),
                line=dict(color='#374151', width=2), name='Historis (30 hari)',
                hovertemplate='%{x|%d %b}<br><b>%{y:,} unit</b><extra></extra>'
            ))
            if f_conf:
                fig_fc.add_trace(go.Scatter(
                    x=list(future_dates)+list(future_dates[::-1]),
                    y=list(ci_hi)+list(ci_lo[::-1]),
                    fill='toself', fillcolor='rgba(16,185,129,0.10)',
                    line=dict(color='rgba(0,0,0,0)'), name='CI ±1.5σ'
                ))
            fig_fc.add_trace(go.Scatter(
                x=future_dates, y=forecasts,
                line=dict(color=C['green'], width=2.5, dash='dash'),
                mode='lines+markers', marker=dict(size=5),
                name='Forecast Ensemble',
                hovertemplate='%{x|%d %b}<br><b>%{y:,} unit</b><extra></extra>'
            ))
            vx = df_base['Tanggal'].iloc[-1].timestamp()*1000
            fig_fc.add_shape(type='line', x0=vx, x1=vx, y0=0, y1=1,
                             xref='x', yref='paper',
                             line=dict(color='#9ca3af', width=1, dash='dot'))
            fig_fc.add_annotation(x=vx, y=1, xref='x', yref='paper',
                                  text='Sekarang', showarrow=False,
                                  font=dict(size=10, color='#9ca3af'), yanchor='bottom')
            lfc = bl(360)
            lfc['yaxis']['title'] = 'Permintaan (unit)'
            fig_fc.update_layout(**lfc)
            chart_card(f"Forecast {fr['hari']} Hari — {fr['produk']}", fig_fc,
                       f"Ensemble XGB·LGB·CAT · bobot {weights[0]:.0%}:{weights[1]:.0%}:{weights[2]:.0%}")

            st.markdown('<div class="sec-title">Tabel Hasil Peramalan</div>', unsafe_allow_html=True)
            tbl_n = min(30, fr['hari'])
            st.dataframe(pd.DataFrame({
                'Tanggal'         : [d.strftime('%d %b %Y') for d in future_dates[:tbl_n]],
                'Forecast (unit)' : forecasts[:tbl_n],
                'Batas Bawah'     : ci_lo[:tbl_n],
                'Batas Atas'      : ci_hi[:tbl_n],
                'Hari'            : [d.strftime('%A') for d in future_dates[:tbl_n]],
            }), width='stretch', hide_index=True)

    with tab_eval:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-note">
            Evaluasi performa model menggunakan data historis.
        </div>""", unsafe_allow_html=True)

        ev_produk = st.selectbox("Produk Evaluasi", ["LBS BLACK FOREST"], key="ev_prod")
        ev_split  = st.slider("Test set (hari terakhir)", 7, 30, 14, key="ev_split")

        df_ev = st.session_state.demand_history.copy()
        df_ev = df_ev[df_ev['Produk']==ev_produk].copy()
        df_ev['Tanggal']    = pd.to_datetime(df_ev['Tanggal'])
        df_ev['Permintaan'] = pd.to_numeric(df_ev['Permintaan'], errors='coerce').fillna(0)
        df_ev = df_ev.sort_values('Tanggal').reset_index(drop=True)

        if len(df_ev) < ev_split + 14:
            st.warning("Data tidak cukup untuk evaluasi.")
        else:
            df_train = df_ev.iloc[:-ev_split]
            df_test  = df_ev.iloc[-ev_split:]
            test_dates = df_test['Tanggal'].values
            y_actual   = df_test['Permintaan'].values.astype(float)

            with st.spinner("Mengevaluasi model..."):
                _, y_pred_raw = build_features(df_train, test_dates)

            y_pred = np.clip(y_pred_raw, 0, None)
            mae    = round(mean_absolute_error(y_actual, y_pred), 2)
            rmse   = round(np.sqrt(mean_squared_error(y_actual, y_pred)), 2)
            mape   = round(np.mean(np.abs((y_actual - y_pred) / (y_actual + 1e-9))) * 100, 2)
            r2     = round(r2_score(y_actual, y_pred), 4)

            em1,em2,em3,em4 = st.columns(4, gap="small")
            skpi(em1, "MAE",   f"{mae} unit",  f"{mae:.0f}u",  mae<50)
            skpi(em2, "MAPE",  f"{mape} %",    f"{mape:.1f}%", mape<15)
            skpi(em3, "RMSE",  f"{rmse} unit", f"{rmse:.0f}u", rmse<60)
            skpi(em4, "R²",    f"{r2}",        f"{r2:.3f}",    r2>0.7)

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            ev1, ev2 = st.columns(2, gap="medium")

            with ev1:
                fig_ev = go.Figure()
                fig_ev.add_trace(go.Scatter(x=df_test['Tanggal'], y=y_actual,
                    mode='lines+markers', name='Aktual',
                    line=dict(color='#374151', width=2), marker=dict(size=5)))
                fig_ev.add_trace(go.Scatter(x=df_test['Tanggal'], y=y_pred,
                    mode='lines+markers', name='Prediksi Ensemble',
                    line=dict(color=C['green'], width=2, dash='dot'), marker=dict(size=5)))
                le = bl(300)
                le['yaxis']['title'] = 'Permintaan (unit)'
                fig_ev.update_layout(**le)
                chart_card("Aktual vs Prediksi", fig_ev, f"MAE:{mae} · RMSE:{rmse} · MAPE:{mape}%")

            with ev2:
                residuals  = y_actual - y_pred
                res_colors = ['#ef4444' if r>0 else '#3b82f6' for r in residuals]
                fig_res = go.Figure()
                fig_res.add_hline(y=0, line_color='#e5e7eb', line_width=1.5)
                fig_res.add_trace(go.Bar(x=df_test['Tanggal'], y=residuals,
                    marker_color=res_colors, marker_line_width=0, name='Residual'))
                lr2 = bl(300)
                lr2['yaxis']['title'] = 'Residual (unit)'
                fig_res.update_layout(**lr2)
                chart_card("Residual Plot", fig_res, "Merah=over · Biru=under predict")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-title">Kontribusi Tiap Model dalam Ensemble</div>', unsafe_allow_html=True)
            X_test_feat, _ = build_features(df_train, test_dates)
            p_xgb = dem_model['xgb'].predict(X_test_feat)
            p_lgb = dem_model['lgb'].predict(X_test_feat)
            p_cat = dem_model['cat'].predict(X_test_feat)

            mc1,mc2,mc3 = st.columns(3, gap="medium")
            for (col, name, preds, color) in [
                (mc1,"XGBoost",   p_xgb, "#3b82f6"),
                (mc2,"LightGBM",  p_lgb, "#10b981"),
                (mc3,"CatBoost",  p_cat, "#f59e0b"),
            ]:
                m_mae = round(mean_absolute_error(y_actual, preds), 2)
                m_r2  = round(r2_score(y_actual, preds), 3)
                fig_m = go.Figure()
                fig_m.add_trace(go.Scatter(x=df_test['Tanggal'], y=y_actual,
                    line=dict(color='#374151',width=1.5), name='Aktual'))
                fig_m.add_trace(go.Scatter(x=df_test['Tanggal'], y=preds,
                    line=dict(color=color,width=1.8,dash='dot'), name=name))
                lm = bl(220)
                lm['yaxis']['title'] = 'unit'
                fig_m.update_layout(**lm)
                col.markdown(f"""
                <div style="background:#ffffff;border:1px solid #eaecf0;border-radius:12px;
                     padding:14px 16px 6px;margin-bottom:8px;border-top:3px solid {color};">
                    <div style="font-size:0.85rem;font-weight:600;color:#111827;margin-bottom:2px;">{name}</div>
                    <div style="font-size:0.75rem;color:#9ca3af;">
                        Bobot: {int(weights[{'XGBoost':0,'LightGBM':1,'CatBoost':2}[name]]*100)}%
                        &nbsp;·&nbsp; MAE: {m_mae} &nbsp;·&nbsp; R²: {m_r2}
                    </div>
                </div>""", unsafe_allow_html=True)
                col.plotly_chart(fig_m, width='stretch', config={'displayModeBar': False})

    st.markdown("</div>", unsafe_allow_html=True)

# 
# PAGE — PREDIKSI SUHU ZONA
# 
elif page == "Prediksi Suhu Zona":
    topbar("Prediksi Suhu Zona 1–4",
           "Prediksi suhu oven per zona berbasis model Gradient Boosting (ML)")

    if not ML_AVAILABLE:
        st.error("Install: pip install joblib scikit-learn openpyxl")
        st.stop()

    ZONA_CFG = {
        "Zona 1": {
            "model_file": "model_terbaik_zona1.pkl",
            "feat_file":  "feature_columns_zona1.pkl",
            "actual_col": "Suhu Zona 1 (°C)",
            "lb_default": 100, "ub_default": 160,
            "color": "#3b82f6",
        },
        "Zona 2": {
            "model_file": "model_terbaik_zona2.pkl",
            "feat_file":  "feature_columns_zona2.pkl",
            "actual_col": "Suhu Zona 2 (°C)",
            "lb_default": 110, "ub_default": 170,
            "color": "#10b981",
        },
        "Zona 3": {
            "model_file": "model_terbaik_zona3__1_.pkl",
            "feat_file":  "feature_columns_zona3__1_.pkl",
            "actual_col": "Suhu Zona 3 (°C)",
            "lb_default": 115, "ub_default": 175,
            "color": "#f59e0b",
        },
        "Zona 4": {
            "model_file": "model_terbaik_zona4__1_.pkl",
            "feat_file":  "feature_columns_zona4__1_.pkl",
            "actual_col": "Suhu Zona 4 (°C)",
            "lb_default": 120, "ub_default": 180,
            "color": "#8b5cf6",
        },
    }

    @st.cache_resource
    def load_zona_models():
        warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
        models = {}
        for zona, cfg in ZONA_CFG.items():
            m = joblib.load(DIR_MODELS / cfg["model_file"])
            with open(DIR_MODELS / cfg["feat_file"], "rb") as f:
                feat = joblib.load(f)
            models[zona] = {"model": m, "features": feat}
        return models

    @st.cache_data
    def load_suhu_dataset():
        df = pd.read_excel(BASE_DIR / "data" / "data_steamflow.xlsx")
        df = df.drop(columns=[c for c in df.columns if "Unnamed" in str(c)], errors="ignore")
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        for z in [1, 2, 3, 4]:
            col_kpa = f"Steam Zona {z} (kPa)"
            col_mpa = f"Steam_Zona{z}_MPa"
            if col_kpa in df.columns:
                df[col_mpa] = df[col_kpa] / 1000.0
        if "Supply Steam (kPaG)" in df.columns:
            df["Supply_MPa"]   = df["Supply Steam (kPaG)"] / 1000.0
        if "Steam (kPaG)" in df.columns:
            df["Pressure_MPa"] = df["Steam (kPaG)"] / 1000.0
        if "Jacket Steam (kPaG)" in df.columns:
            df["Jacket_MPa"]   = df["Jacket Steam (kPaG)"] / 1000.0
        if "Decomp Steam (kPaG)" in df.columns:
            df["Decomp_MPa"]   = df["Decomp Steam (kPaG)"] / 1000.0
        def t_sat(p_mpa):
            return 100 + 28.06 * (p_mpa - 0.1013) / 0.1013 if p_mpa is not None else np.nan
        for col, new_col in [
            ("Supply_MPa","T_sat"),("Steam_Zona1_MPa","T_sat_Z1"),
            ("Steam_Zona2_MPa","T_sat_Z2"),("Steam_Zona3_MPa","T_sat_Z3"),
            ("Steam_Zona4_MPa","T_sat_Z4"),("Jacket_MPa","T_sat_jacket"),
            ("Decomp_MPa","T_sat_decomp"),
        ]:
            if col in df.columns:
                df[new_col] = df[col].apply(t_sat)
        for z in [1,2,3,4]:
            s_col  = f"Suhu Zona {z} (°C)"
            sat_col = f"T_sat_Z{z}"
            if s_col in df.columns and sat_col in df.columns:
                df[f"Delta_T_Z{z}"] = df[sat_col] - df[s_col]
        if "T_sat_jacket" in df.columns:
            for z in [1,2,3,4]:
                s_col = f"Suhu Zona {z} (°C)"
                if s_col in df.columns:
                    df[f"Delta_T_jacket_Z{z}"] = df["T_sat_jacket"] - df[s_col]
        if "Supply_MPa" in df.columns:
            df["IAPWS_h"] = 2675 + 1.8 * (df["Supply_MPa"] - 0.1) * 1000
        return df.reset_index(drop=True)

    try:
        zona_models = load_zona_models()
        df_data     = load_suhu_dataset()
        N_ROWS      = len(df_data)
    except Exception as e:
        st.error(f"Error memuat model/data: {e}")
        st.stop()

    if "sz_idx" not in st.session_state:
        st.session_state.sz_idx = 0
    if "sz_running" not in st.session_state:
        st.session_state.sz_running = False
    if "sz_history" not in st.session_state:
        st.session_state.sz_history = {z: [] for z in ZONA_CFG}
    if "sz_zona" not in st.session_state:
        st.session_state.sz_zona = "Zona 1"
    for z, cfg in ZONA_CFG.items():
        if f"sz_lb_{z}" not in st.session_state:
            st.session_state[f"sz_lb_{z}"] = cfg["lb_default"]
        if f"sz_ub_{z}" not in st.session_state:
            st.session_state[f"sz_ub_{z}"] = cfg["ub_default"]

    #  Pilih zona — dengan override CSS inline 
    st.markdown("""
    <style>
    div[data-testid="stRadio"] > label,
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label > div > p,
    div[data-testid="stRadio"] label span {
        color: #111827 !important;
        -webkit-text-fill-color: #111827 !important;
        opacity: 1 !important;
        visibility: visible !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    zona_pilihan = st.radio(
        "Pilih Zona",
        list(ZONA_CFG.keys()),
        horizontal=True,
        key="sz_zona_radio",
        index=list(ZONA_CFG.keys()).index(st.session_state.sz_zona),
    )
    st.session_state.sz_zona = zona_pilihan
    cfg_aktif = ZONA_CFG[zona_pilihan]

    ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1,1,1,1,2], gap="small")
    with ctrl1:
        lb = st.number_input("Batas Bawah (°C)", 50, 300,
                             st.session_state[f"sz_lb_{zona_pilihan}"],
                             key=f"sz_lb_inp_{zona_pilihan}")
        st.session_state[f"sz_lb_{zona_pilihan}"] = lb
    with ctrl2:
        ub = st.number_input("Batas Atas (°C)", 80, 350,
                             st.session_state[f"sz_ub_{zona_pilihan}"],
                             key=f"sz_ub_inp_{zona_pilihan}")
        st.session_state[f"sz_ub_{zona_pilihan}"] = ub
    with ctrl3:
        interval = st.selectbox("Interval", [2,3,5,10], index=2,
                                format_func=lambda x: f"{x} detik", key="sz_interval")
    with ctrl4:
        max_hist = st.number_input("Maks History", 10, 200, 50, key="sz_maxhist")
    with ctrl5:
        bc1, bc2, bc3 = st.columns(3)
        start_btn = bc1.button("Start",  type="primary",  width='stretch', key="sz_start")
        stop_btn  = bc2.button("⏹ Stop",   type="primary",  width='stretch', key="sz_stop")
        reset_btn = bc3.button("↺ Reset",  type="secondary", width='stretch', key="sz_reset")
        st.markdown("""
        <script>
        (function applyStopStyle() {
            var btns = window.parent.document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].innerText.trim().includes('Stop')) {
                    btns[i].style.setProperty('background', '#dc2626', 'important');
                    btns[i].style.setProperty('color', '#ffffff', 'important');
                    btns[i].style.setProperty('border', 'none', 'important');
                }
            }
            setTimeout(applyStopStyle, 300);
            setTimeout(applyStopStyle, 800);
        })();
        </script>
        """, unsafe_allow_html=True)

    if start_btn:
        st.session_state.sz_running = True
    if stop_btn:
        st.session_state.sz_running = False
    if reset_btn:
        st.session_state.sz_idx     = 0
        st.session_state.sz_history = {z: [] for z in ZONA_CFG}
        st.session_state.sz_running = False
        load_suhu_dataset.clear()
        st.rerun()

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    idx      = st.session_state.sz_idx % N_ROWS
    row      = df_data.iloc[idx]
    features = zona_models[zona_pilihan]["features"]
    model    = zona_models[zona_pilihan]["model"]

    try:
        X_vals = []
        for f in features:
            X_vals.append(float(row[f]) if f in row.index and not pd.isna(row[f]) else 0.0)
        X_in     = pd.DataFrame([X_vals], columns=features)
        pred_val = round(float(model.predict(X_in)[0]), 2)
    except Exception as e:
        st.error(f"Prediksi gagal: {e}")
        st.stop()

    actual_col = cfg_aktif["actual_col"]
    actual_val = float(row[actual_col]) if actual_col in row.index and not pd.isna(row[actual_col]) else pred_val
    timestamp  = str(row.get("Timestamp", f"Row {idx+1}"))[:19]

    hist_zona = st.session_state.sz_history.setdefault(zona_pilihan, [])
    hist_zona.append({"idx": idx+1, "ts": timestamp, "pred": pred_val, "actual": actual_val})
    if len(hist_zona) > max_hist:
        hist_zona.pop(0)

    lb_v = st.session_state[f"sz_lb_{zona_pilihan}"]
    ub_v = st.session_state[f"sz_ub_{zona_pilihan}"]

    if pred_val < lb_v:
        status_label  = "PERINGATAN — Di Bawah Batas"
        status_color  = "#d97706"
        status_bg     = "#fffbeb"
        status_border = "#f59e0b"
        status_icon   = ""
        is_alert      = True
    elif pred_val > ub_v:
        status_label  = "PERINGATAN — Melebihi Batas Atas"
        status_color  = "#dc2626"
        status_bg     = "#fef2f2"
        status_border = "#ef4444"
        status_icon   = ""
        is_alert      = True
    else:
        status_label  = "NORMAL"
        status_color  = "#059669"
        status_bg     = "#f0fdf4"
        status_border = "#10b981"
        status_icon   = ""
        is_alert      = False

    if is_alert and st.session_state.sz_running:
        if pred_val < lb_v:
            freq_low, freq_high, sweep_dur, cycles = 300, 700, 0.6, 2
        else:
            freq_low, freq_high, sweep_dur, cycles = 500, 1100, 0.35, 3
        siren_html = f"""
        <script>
        (function() {{
            try {{
                var AudioCtx = window.AudioContext || window.webkitAudioContext;
                if (!AudioCtx) return;
                var ctx = new AudioCtx();
                function playSiren() {{
                    var osc = ctx.createOscillator();
                    var gain = ctx.createGain();
                    osc.connect(gain); gain.connect(ctx.destination);
                    osc.type = 'sawtooth';
                    var t = ctx.currentTime;
                    osc.frequency.setValueAtTime({freq_low}, t);
                    for (var i = 0; i < {cycles}; i++) {{
                        osc.frequency.linearRampToValueAtTime({freq_high}, t + {sweep_dur} * (2*i + 1));
                        osc.frequency.linearRampToValueAtTime({freq_low},  t + {sweep_dur} * (2*i + 2));
                    }}
                    var totalDur = {sweep_dur} * 2 * {cycles};
                    gain.gain.setValueAtTime(0, t);
                    gain.gain.linearRampToValueAtTime(0.4, t + 0.05);
                    gain.gain.setValueAtTime(0.4, t + totalDur - 0.15);
                    gain.gain.linearRampToValueAtTime(0, t + totalDur);
                    osc.start(t); osc.stop(t + totalDur);
                }}
                if (ctx.state === 'suspended') {{ ctx.resume().then(playSiren); }}
                else {{ playSiren(); }}
            }} catch(e) {{ console.warn('Siren error:', e); }}
        }})();
        </script>"""
        components.html(siren_html, height=0, scrolling=False)

    col_left, col_right = st.columns([3, 4], gap="medium")

    with col_left:
        pct_of_range = (pred_val - lb_v) / max(ub_v - lb_v, 1) * 100
        pct_clamped  = max(0, min(100, pct_of_range))

        st.markdown(f"""
        <div style="background:{status_bg};border:2px solid {status_border};
             border-radius:14px;padding:22px 24px 20px;margin-bottom:14px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
                <span style="font-size:1.5rem;">{status_icon}</span>
                <div>
                    <div style="font-size:0.7rem;font-weight:700;color:{status_color};
                         text-transform:uppercase;letter-spacing:0.8px;">{status_label}</div>
                    <div style="font-size:0.75rem;color:#6b7280;margin-top:1px;">
                        Batas: {lb_v} – {ub_v} °C &nbsp;·&nbsp; {zona_pilihan}
                    </div>
                </div>
            </div>
            <div style="font-size:0.68rem;font-weight:600;color:#9ca3af;
                 text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;">Prediksi Suhu</div>
            <div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;">
                <div style="font-size:2.4rem;font-weight:800;color:#111827;
                     letter-spacing:-2px;line-height:1;">{pred_val:.2f}</div>
                <div style="font-size:1rem;color:#9ca3af;font-weight:500;white-space:nowrap;">°C</div>
            </div>
            <div style="margin-top:14px;">
                <div style="display:flex;justify-content:space-between;
                     font-size:0.7rem;color:#9ca3af;margin-bottom:4px;">
                    <span>{lb_v} °C</span><span>Normal</span><span>{ub_v} °C</span>
                </div>
                <div style="height:8px;background:#e5e7eb;border-radius:4px;overflow:hidden;">
                    <div style="height:100%;width:{pct_clamped:.1f}%;
                         background:{status_color};border-radius:4px;transition:width 0.4s ease;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:#f8faff;border:2px solid #93c5fd;
             border-radius:14px;padding:18px 24px 16px;margin-bottom:14px;">
            <div style="font-size:0.68rem;font-weight:600;color:#9ca3af;
                 text-transform:uppercase;letter-spacing:0.6px;margin-bottom:4px;">
                Aktual (Data) — {zona_pilihan}
            </div>
            <div style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;">
                <div style="font-size:2rem;font-weight:800;color:#111827;
                     letter-spacing:-1.5px;line-height:1;">{actual_val:.1f}</div>
                <div style="font-size:1rem;color:#9ca3af;font-weight:500;white-space:nowrap;">°C</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for lbl, val in [
            ("Selisih Pred–Aktual", f"{pred_val-actual_val:+.2f} °C"),
            ("Baris Data",          f"{idx+1} / {N_ROWS}"),
            ("Timestamp",           timestamp),
            ("Mode", "Running" if st.session_state.sz_running else "⏸ Paused"),
        ]:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:8px 12px;background:#fff;border:1px solid #f3f4f6;
                 border-radius:8px;margin-bottom:5px;">
                <span style="font-size:0.78rem;color:#6b7280;">{lbl}</span>
                <span style="font-size:0.82rem;font-weight:600;color:#111827;">{val}</span>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        hist = st.session_state.sz_history.get(zona_pilihan, [])
        if len(hist) >= 2:
            h_pred  = [h["pred"]   for h in hist]
            h_act   = [h["actual"] for h in hist]
            h_ts    = [h["ts"]     for h in hist]
            h_clr   = [status_border if p < lb_v or p > ub_v else "#10b981" for p in h_pred]
            z_color = cfg_aktif["color"]

            fig = go.Figure()
            fig.add_hrect(y0=lb_v, y1=ub_v, fillcolor="rgba(16,185,129,0.07)", line_width=0,
                          annotation_text=f"Zona Normal ({lb_v}–{ub_v} °C)",
                          annotation_position="top left",
                          annotation_font=dict(color="#059669", size=10))
            fig.add_hline(y=ub_v, line_dash="dash", line_color="#ef4444", line_width=1.2,
                          annotation_text=f"Batas Atas {ub_v} °C", annotation_position="top right",
                          annotation_font=dict(color="#ef4444", size=10))
            fig.add_hline(y=lb_v, line_dash="dash", line_color="#f59e0b", line_width=1.2,
                          annotation_text=f"Batas Bawah {lb_v} °C", annotation_position="bottom right",
                          annotation_font=dict(color="#f59e0b", size=10))
            fig.add_trace(go.Scatter(x=h_ts, y=h_act, mode="lines", name="Aktual",
                line=dict(color="#94a3b8", width=1.5, dash="dot"),
                hovertemplate="%{x}<br>Aktual: <b>%{y:.1f} °C</b><extra></extra>"))
            fig.add_trace(go.Scatter(x=h_ts, y=h_pred, mode="lines", fill="tozeroy",
                fillcolor="rgba(59,130,246,0.05)", line=dict(color=z_color, width=2.5),
                name="Prediksi",
                hovertemplate="%{x}<br>Prediksi: <b>%{y:.2f} °C</b><extra></extra>"))
            fig.add_trace(go.Scatter(x=h_ts, y=h_pred, mode="markers", name="Status",
                marker=dict(color=h_clr, size=9, line=dict(color="white", width=1.5)),
                hovertemplate="%{x}<br><b>%{y:.2f} °C</b><extra></extra>"))
            fig.add_trace(go.Scatter(x=[h_ts[-1]], y=[h_pred[-1]], mode="markers", name="Terbaru",
                marker=dict(color=status_color, size=14, symbol="diamond",
                            line=dict(color="white", width=2)), showlegend=True))

            all_vals = h_pred + h_act
            y_min = max(0, min(all_vals + [lb_v]) - 10)
            y_max = max(all_vals + [ub_v]) + 10

            lay = bl(420)
            lay["xaxis"]["title"]     = "Timestamp"
            lay["xaxis"]["tickangle"] = -30
            lay["xaxis"]["nticks"]    = 8
            lay["yaxis"]["title"]     = f"Suhu {zona_pilihan} (°C)"
            lay["yaxis"]["range"]     = [y_min, y_max]
            fig.update_layout(**lay)

            st.markdown(f"""
            <div style="background:#fff;border:1px solid #eaecf0;border-radius:12px;
                 padding:14px 18px 6px;margin-bottom:4px;border-top:3px solid {z_color};">
                <div style="font-size:0.88rem;font-weight:600;color:#111827;">
                    Tren Prediksi Suhu — {zona_pilihan} (Real-time)
                </div>
                <div style="font-size:0.72rem;color:#9ca3af;margin-top:2px;">
                     Prediksi &nbsp;·&nbsp;  Aktual &nbsp;·&nbsp;
                     Normal &nbsp;·&nbsp;  Peringatan
                </div>
            </div>""", unsafe_allow_html=True)
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        else:
            st.markdown("""
            <div style="text-align:center;padding:60px;color:#9ca3af;">
                <div style="font-size:2rem;margin-bottom:10px;"></div>
                <div style="font-size:0.9rem;">Tekan <b> Start</b> untuk memulai prediksi real-time</div>
            </div>""", unsafe_allow_html=True)

    hist = st.session_state.sz_history.get(zona_pilihan, [])
    if len(hist) >= 2:
        arr     = np.array([h["pred"] for h in hist])
        n_alert = sum(1 for v in arr if v < lb_v or v > ub_v)
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        mk1, mk2, mk3, mk4 = st.columns(4, gap="small")
        skpi(mk1, f"Prediksi Terakhir ({zona_pilihan})", f"{arr[-1]:.2f} °C")
        skpi(mk2, "Rata-rata",   f"{arr.mean():.2f} °C")
        skpi(mk3, "Min / Maks",  f"{arr.min():.1f} / {arr.max():.1f} °C")
        skpi(mk4, "Total Alert", f"{n_alert} titik",
             f"{n_alert/len(arr)*100:.0f}%", n_alert==0)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size:0.78rem;font-weight:600;color:#374151;margin-bottom:10px;'>"
                f"Fitur Input Model — {zona_pilihan}</div>", unsafe_allow_html=True)
    tbl_rows = []
    for f in features:
        if f in row.index:
            try:
                tbl_rows.append({"Fitur": f, "Nilai": round(float(row[f]), 4)})
            except Exception:
                pass
    if tbl_rows:
        df_horiz = pd.DataFrame(tbl_rows).set_index("Fitur").T.reset_index(drop=True)
        st.dataframe(df_horiz, hide_index=True, width="stretch")

    if st.session_state.sz_running:
        if AUTOREFRESH_AVAILABLE:
            count = st_autorefresh(interval=interval * 1000, key="sz_autorefresh")
            if count > 0:
                st.session_state.sz_idx += 1
        else:
            st.warning("Install `streamlit-autorefresh`: `pip install streamlit-autorefresh`")
            time.sleep(interval)
            st.session_state.sz_idx += 1
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# 
# PAGE — PENGENDALIAN MUTU
# 
elif page == "Pengendalian Mutu":
    topbar("Pengendalian Mutu",
           "Statistical Process Control (SPC) dan kerangka kerja DMAIC")

    st.markdown("""
    <div class="dmaic-wrap">
        <div class="dmaic-cell" style="background:#0a1a10;color:#fff;">D <small>Define</small></div>
        <div class="dmaic-cell" style="background:#166534;color:#fff;">M <small>Measure</small></div>
        <div class="dmaic-cell" style="background:#16a34a;color:#fff;">A <small>Analyze</small></div>
        <div class="dmaic-cell" style="background:#4ade80;color:#0a1a10;">I <small>Improve</small></div>
        <div class="dmaic-cell" style="background:#f0fdf4;color:#0a1a10;border-left:1px solid #e4ebe6;">C <small>Control</small></div>
    </div>
    """, unsafe_allow_html=True)

    # Shared data
    pareto_data = {
        "Jenis Defect": [
            "Tinggi kurang dari 4 cm", "Basah", "Belah",
            "Permukaan kue Kering", "Warna kurang sesuai",
            "Tekstur Crumbling", "Bantet"
        ],
        "Frekuensi": [62, 45, 15, 11, 11, 5, 0],
    }
    df_pareto = pd.DataFrame(pareto_data)
    df_pareto = df_pareto.sort_values("Frekuensi", ascending=False).reset_index(drop=True)
    total_freq = df_pareto["Frekuensi"].sum()
    df_pareto["%"] = (df_pareto["Frekuensi"] / total_freq * 100).round(2)
    df_pareto["% Kumulatif"] = df_pareto["%"].cumsum().round(2)

    sigma_rows = [
        {"No.": 1, "Tanggal": "5/4/2026",  "Jumlah Produksi": 871,  "Jumlah Defect": 28, "CTQ": 2, "DPU": "3.21%", "TOP": 1742, "DPO": 0.01607347876, "DPMO": 16073.47876, "Sigma": 3.642578517},
        {"No.": 2, "Tanggal": "5/5/2026",  "Jumlah Produksi": 1248, "Jumlah Defect": 47, "CTQ": 2, "DPU": "3.77%", "TOP": 2496, "DPO": 0.01883012821, "DPMO": 18830.12821, "Sigma": 3.578533414},
        {"No.": 3, "Tanggal": "5/6/2026",  "Jumlah Produksi": 1716, "Jumlah Defect": 26, "CTQ": 2, "DPU": "1.52%", "TOP": 3432, "DPO": 0.00757575757, "DPMO": 7575.757576,  "Sigma": 3.928737089},
        {"No.": 4, "Tanggal": "5/6/2026",  "Jumlah Produksi": 1131, "Jumlah Defect": 32, "CTQ": 2, "DPU": "2.83%", "TOP": 2262, "DPO": 0.01414677277, "DPMO": 14146.77277, "Sigma": 3.693192042},
        {"No.": 5, "Tanggal": "5/7/2026",  "Jumlah Produksi": 1378, "Jumlah Defect": 34, "CTQ": 2, "DPU": "2.47%", "TOP": 2756, "DPO": 0.01233671988, "DPMO": 12336.71988, "Sigma": 3.746477489},
        {"No.": 6, "Tanggal": "5/7/2026",  "Jumlah Produksi": 1664, "Jumlah Defect": 30, "CTQ": 2, "DPU": "1.80%", "TOP": 3328, "DPO": 0.00901442307, "DPMO": 9014.423077,  "Sigma": 3.865025159},
        {"No.": 7, "Tanggal": "5/8/2026",  "Jumlah Produksi": 1781, "Jumlah Defect": 35, "CTQ": 2, "DPU": "1.97%", "TOP": 3562, "DPO": 0.00982594048, "DPMO": 9825.940483,  "Sigma": 3.83292883},
    ]
    df_sigma = pd.DataFrame(sigma_rows)

    tab_d, tab_m, tab_a, tab_i, tab_c = st.tabs([
        "Define", "Measure", "Analyze", "Improve", "Control"
    ])

    # TAB DEFINE
    with tab_d:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Tabel & Diagram Pareto — Jenis Defect</div>', unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.8rem;color:#6b7280;margin-bottom:10px;'>Edit kolom <b>Frekuensi</b> atau <b>Jenis Defect</b> — grafik akan otomatis diperbarui.</div>", unsafe_allow_html=True)

        # ── Upload Excel ────────────────────────────────────────────
        up_col, reset_col = st.columns([3, 1], gap="small")
        with up_col:
            uploaded_pareto = st.file_uploader(
                "Upload Excel (kolom: Jenis Defect, Frekuensi)",
                type=["xlsx", "xls"], key="pareto_upload",
                label_visibility="collapsed",
            )
        with reset_col:
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            if st.button("Reset Default", key="pareto_reset", width='stretch'):
                st.session_state.pareto_df = pd.DataFrame(pareto_data)
                st.rerun()

        if uploaded_pareto:
            try:
                _df_up = pd.read_excel(uploaded_pareto)
                _miss = {"Jenis Defect", "Frekuensi"} - set(_df_up.columns)
                if _miss:
                    st.error(f"Kolom tidak ditemukan: {', '.join(_miss)}. Wajib ada kolom: Jenis Defect, Frekuensi")
                else:
                    _df_up = _df_up[["Jenis Defect", "Frekuensi"]].dropna(subset=["Jenis Defect"]).reset_index(drop=True)
                    _df_up["Frekuensi"] = pd.to_numeric(_df_up["Frekuensi"], errors="coerce").fillna(0).astype(int)
                    st.session_state.pareto_df = _df_up
                    st.success(f"{len(_df_up)} jenis defect dimuat dari Excel.")
            except Exception as _e:
                st.error(f"Gagal membaca file: {_e}")

        # Editable table — simpan di session_state agar reaktif
        if "pareto_df" not in st.session_state:
            _db_defect = get_defect_data()
            if _db_defect:
                st.session_state.pareto_df = pd.DataFrame([
                    {"Jenis Defect": r["jenis_defect"], "Frekuensi": r["frekuensi"]}
                    for r in _db_defect
                ])
            else:
                st.session_state.pareto_df = pd.DataFrame(pareto_data)

        col_tabel, col_pareto = st.columns([2, 3], gap="medium")

        with col_tabel:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown('<div class="chart-card-title">Tabel Frekuensi Defect</div>', unsafe_allow_html=True)

            # Hitung % dan % Kumulatif untuk ditampilkan di tabel
            _pre = st.session_state.pareto_df[["Jenis Defect","Frekuensi"]].copy()
            _pre["Frekuensi"] = pd.to_numeric(_pre["Frekuensi"], errors="coerce").fillna(0).astype(int)
            _pre_clean = _pre[_pre["Jenis Defect"].notna() & (_pre["Jenis Defect"].astype(str).str.strip() != "")].sort_values("Frekuensi", ascending=False).reset_index(drop=True)
            _pre_total = _pre_clean["Frekuensi"].sum()
            if _pre_total > 0:
                _pre_clean["%"] = (_pre_clean["Frekuensi"] / _pre_total * 100).round(2)
                _pre_clean["% Kumulatif"] = _pre_clean["%"].cumsum().round(2)
            else:
                _pre_clean["%"] = 0.0
                _pre_clean["% Kumulatif"] = 0.0

            df_edited = st.data_editor(
                _pre_clean[["Jenis Defect", "Frekuensi", "%", "% Kumulatif"]],
                column_config={
                    "Jenis Defect": st.column_config.TextColumn("Jenis Defect", width="medium"),
                    "Frekuensi": st.column_config.NumberColumn("Frekuensi", min_value=0, step=1),
                    "%": st.column_config.NumberColumn("% ", format="%.2f%%", disabled=True),
                    "% Kumulatif": st.column_config.NumberColumn("% Kumulatif", format="%.2f%%", disabled=True),
                },
                num_rows="dynamic",
                hide_index=True,
                width='stretch',
                height=310,
                key="pareto_editor",
            )
            # Simpan hanya kolom yang bisa diedit
            st.session_state.pareto_df = df_edited[["Jenis Defect","Frekuensi"]].copy()
            _rows_to_save = [{"Jenis Defect": str(r["Jenis Defect"]), "Frekuensi": int(r["Frekuensi"])}
                             for _, r in df_edited.iterrows()
                             if str(r.get("Jenis Defect","")).strip()]
            if _rows_to_save:
                save_defect_data(_rows_to_save, updated_by=current_user["username"])

            # Hitung ulang % dan kumulatif dari data yang diedit
            _df_p = df_edited.dropna(subset=["Jenis Defect","Frekuensi"]).copy()
            _df_p["Frekuensi"] = pd.to_numeric(_df_p["Frekuensi"], errors="coerce").fillna(0).astype(int)
            _df_p = _df_p[_df_p["Jenis Defect"].str.strip() != ""].sort_values("Frekuensi", ascending=False).reset_index(drop=True)
            _total = _df_p["Frekuensi"].sum()
            if _total > 0:
                _df_p["%"] = (_df_p["Frekuensi"] / _total * 100).round(2)
                _df_p["% Kumulatif"] = _df_p["%"].cumsum().round(2)
            else:
                _df_p["%"] = 0.0
                _df_p["% Kumulatif"] = 0.0

            if _total > 0:
                vital_few = _df_p[_df_p["% Kumulatif"] <= 80.0]
                if len(vital_few) == 0:
                    vital_few = _df_p.iloc[:1]
                names_vital = ", ".join(f"<b>{n}</b>" for n in vital_few["Jenis Defect"].tolist())
                pct_vital   = vital_few["Frekuensi"].sum() / _total * 100
                st.markdown(
                    f'<div class="info-note" style="margin-top:10px;">Vital Few: '
                    f'{names_vital} menyumbang <b>{pct_vital:.1f}%</b> dari total defect.</div>',
                    unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_pareto:
            if _total > 0 and len(_df_p) > 0:
                fig_pareto = go.Figure()
                fig_pareto.add_trace(go.Bar(
                    x=_df_p["Jenis Defect"], y=_df_p["Frekuensi"],
                    name="Frekuensi", marker_color=C["green"], yaxis="y1",
                    text=_df_p["Frekuensi"], textposition="outside",
                    textfont=dict(size=11, color="#111827"),
                ))
                fig_pareto.add_trace(go.Scatter(
                    x=_df_p["Jenis Defect"], y=_df_p["% Kumulatif"],
                    name="% Kumulatif", mode="lines+markers+text",
                    line=dict(color=C["red"], width=2.5),
                    marker=dict(color=C["red"], size=7),
                    text=[f"{v:.2f}%" for v in _df_p["% Kumulatif"]],
                    textposition="top center",
                    textfont=dict(size=10, color=C["red"]),
                    yaxis="y2",
                ))
                fig_pareto.add_hline(
                    y=80, line_dash="dot", line_color=C["amber"],
                    annotation_text="80%", annotation_position="top right",
                    annotation_font=dict(size=10, color=C["amber"]),
                    yref="y2",
                )
                layout_p = bl(400)
                layout_p["yaxis"].update(
                    title="Frekuensi", gridcolor=C["grid"],
                    range=[0, max(_df_p["Frekuensi"].max() * 1.3, 1)],
                    tickfont=dict(size=11, color="#374151"),
                )
                layout_p["xaxis"].update(tickangle=-25, tickfont=dict(size=9, color="#374151"))
                layout_p["font"] = dict(family="system-ui", color="#374151", size=11)
                layout_p["legend"] = dict(orientation="h", y=1.1, x=0.5, xanchor="center",
                                          font=dict(size=11, color="#374151"))
                layout_p["bargap"] = 0.3
                layout_p["yaxis2"] = dict(
                    title="% Kumulatif", overlaying="y", side="right",
                    range=[0, 125], tickformat=".0f", ticksuffix="%",
                    showgrid=False, tickfont=dict(size=11, color="#374151"),
                )
                fig_pareto.update_layout(**layout_p)
                chart_card("Diagram Pareto — Jenis Defect", fig_pareto, "Grafik otomatis diperbarui saat tabel diedit")
            else:
                st.info("Masukkan data frekuensi di tabel untuk menampilkan diagram Pareto.")

    # TAB MEASURE
    with tab_m:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Pengukuran Sigma Level Proses</div>', unsafe_allow_html=True)

        avg_sigma   = df_sigma["Sigma"].mean()
        min_sigma   = df_sigma["Sigma"].min()
        max_sigma   = df_sigma["Sigma"].max()
        avg_dpmo    = df_sigma["DPMO"].mean()
        avg_dpu_num = df_sigma["Jumlah Defect"].sum() / df_sigma["Jumlah Produksi"].sum() * 100

        km1, km2, km3, km4 = st.columns(4)
        skpi(km1, "Rata-rata Sigma",  f"{avg_sigma:.4f} σ", "Target >= 4σ",    avg_sigma >= 4.0)
        skpi(km2, "Sigma Terendah",   f"{min_sigma:.4f} σ", "Min periode ini",  False)
        skpi(km3, "Sigma Tertinggi",  f"{max_sigma:.4f} σ", "Max periode ini",  True)
        skpi(km4, "Rata-rata DPMO",   f"{avg_dpmo:,.0f}",   f"DPU {avg_dpu_num:.2f}%", avg_dpmo < 10000)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown('<div class="chart-card-title">Tabel Perhitungan Sigma Level</div>', unsafe_allow_html=True)

        df_sigma_disp = df_sigma.copy().astype(str)
        df_sigma_disp["DPO"]   = df_sigma["DPO"].apply(lambda v: f"{v:.11f}")
        df_sigma_disp["DPMO"]  = df_sigma["DPMO"].apply(lambda v: f"{v:,.5f}")
        df_sigma_disp["Sigma"] = df_sigma["Sigma"].apply(lambda v: f"{v:.9f}")
        df_sigma_disp["DPU"]   = df_sigma["DPU"]
        total_sigma_row = pd.DataFrame([{
            "No.": "-", "Tanggal": "Total",
            "Jumlah Produksi": str(df_sigma["Jumlah Produksi"].sum()),
            "Jumlah Defect":   str(df_sigma["Jumlah Defect"].sum()),
            "CTQ": "-",
            "DPU": f"{avg_dpu_num:.2f}%",
            "TOP": f"{df_sigma['TOP'].mean():,.2f}",
            "DPO": f"{df_sigma['DPO'].mean():.11f}",
            "DPMO": f"{avg_dpmo:,.5f}",
            "Sigma": f"{avg_sigma:.8f}",
        }])
        df_sigma_disp = pd.concat([df_sigma_disp, total_sigma_row], ignore_index=True)
        st.dataframe(df_sigma_disp, hide_index=True, width='stretch', height=320)

        idx_min   = df_sigma["Sigma"].idxmin()
        idx_max   = df_sigma["Sigma"].idxmax()
        date_min  = df_sigma.loc[idx_min, "Tanggal"]
        date_max  = df_sigma.loc[idx_max, "Tanggal"]
        st.markdown(
            f'<div class="info-note" style="margin-top:12px;display:flex;gap:32px;">'
            f'<span>Sigma terendah: {min_sigma:.4f}σ pada {date_min}</span>'
            f'<span>Sigma tertinggi: {max_sigma:.4f}σ pada {date_max}</span>'
            f'</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        col_sc, col_dpmo = st.columns(2, gap="medium")
        with col_sc:
            fig_sigma = go.Figure()
            fig_sigma.add_hline(y=4.0, line_dash="dot", line_color=C["amber"],
                                annotation_text="Target 4σ",
                                annotation_font=dict(size=10, color=C["amber"]))
            colors_s = [C["red"] if v < 4.0 else C["green"] for v in df_sigma["Sigma"]]
            fig_sigma.add_trace(go.Scatter(
                x=df_sigma["Tanggal"], y=df_sigma["Sigma"],
                mode="lines+markers",
                line=dict(color="#374151", width=1.8),
                marker=dict(color=colors_s, size=8, line=dict(color="white", width=1.5)),
                name="Sigma Level",
            ))
            _bl_s = bl(300)
            _bl_s["yaxis"].update(title="Sigma Level (σ)", range=[3.4, 4.2], gridcolor=C["grid"])
            fig_sigma.update_layout(**_bl_s)
            chart_card("Tren Sigma Level", fig_sigma, "Per sesi pengecekan")

        with col_dpmo:
            fig_dpmo = go.Figure()
            fig_dpmo.add_trace(go.Bar(
                x=df_sigma["Tanggal"], y=df_sigma["DPMO"],
                marker_color=[C["red"] if v > 10000 else C["green"] for v in df_sigma["DPMO"]],
                text=[f"{v:,.0f}" for v in df_sigma["DPMO"]],
                textposition="outside", textfont=dict(size=10), name="DPMO",
            ))
            fig_dpmo.add_hline(y=10000, line_dash="dot", line_color=C["amber"],
                               annotation_text="10.000 DPMO",
                               annotation_font=dict(size=10, color=C["amber"]))
            _bl_d = bl(300)
            _bl_d["yaxis"].update(title="DPMO", gridcolor=C["grid"])
            fig_dpmo.update_layout(**_bl_d)
            chart_card("DPMO per Sesi", fig_dpmo, "Defects Per Million Opportunities")

    # TAB ANALYZE
    with tab_a:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:1.1rem;font-weight:600;color:#374151;margin-bottom:8px;">Tahap Analyze</div>
            <div style="font-size:0.85rem;color:#9ca3af;">Konten akan ditambahkan.</div>
        </div>
        """, unsafe_allow_html=True)

    # TAB IMPROVE
    with tab_i:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:1.1rem;font-weight:600;color:#374151;margin-bottom:8px;">Tahap Improve</div>
            <div style="font-size:0.85rem;color:#9ca3af;">Konten akan ditambahkan.</div>
        </div>
        """, unsafe_allow_html=True)

    # TAB CONTROL
    with tab_c:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
            <div style="font-size:1.1rem;font-weight:600;color:#374151;margin-bottom:8px;">Tahap Control</div>
            <div style="font-size:0.85rem;color:#9ca3af;">Konten akan ditambahkan.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# 
# PAGE — OPTIMASI DISTRIBUSI
# 
elif page == "Optimasi Distribusi":
    topbar("Optimasi Distribusi",
           "Decision Support System — CVRP dengan MILP (PuLP CBC) & OSRM Real Road Distance")

    DEPOT_NAME = "Pabrik"
    DEPOT_LAT  = -6.513258
    DEPOT_LON  = 106.856054
    TRUCK_COLORS = ["#16a34a","#d97706","#2563eb","#9333ea","#dc2626","#0891b2","#ca8a04","#15803d"]
    DEFAULT_DATA = [
        {"Destination": "Stasiun",    "Lat": -6.593965, "Lon": 106.790939, "Demand": 374},
        {"Destination": "Cicurug",    "Lat": -6.758351, "Lon": 106.799291, "Demand": 92},
        {"Destination": "Cibadak",    "Lat": -6.893705, "Lon": 106.785562, "Demand": 97},
        {"Destination": "Puncak",     "Lat": -6.654124, "Lon": 106.864429, "Demand": 235},
        {"Destination": "Pajajaran",  "Lat": -6.616239, "Lon": 106.814225, "Demand": 285},
        {"Destination": "Sudirman",   "Lat": -6.587387, "Lon": 106.797201, "Demand": 169},
        {"Destination": "Sentul",     "Lat": -6.512885, "Lon": 106.855652, "Demand": 79},
        {"Destination": "Cibinong",   "Lat": -6.482988, "Lon": 106.843517, "Demand": 337},
        {"Destination": "BojongGede", "Lat": -6.495576, "Lon": 106.794553, "Demand": 148},
        {"Destination": "Cilebut",    "Lat": -6.530530, "Lon": 106.800521, "Demand": 120},
        {"Destination": "Dramaga",    "Lat": -6.572362, "Lon": 106.748861, "Demand": 166},
        {"Destination": "Leuwiliang", "Lat": -6.576214, "Lon": 106.487030, "Demand": 120},
        {"Destination": "Jalan Baru", "Lat": -6.561689, "Lon": 106.794388, "Demand": 311},
    ]

    st.markdown("""
    <style>
    .dss-info { background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:10px 14px;font-size:.82rem;color:#166534;margin-bottom:12px; }
    .dss-warn { background:#fefce8;border:1px solid #fde047;border-radius:8px;padding:10px 14px;font-size:.82rem;color:#854d0e;margin-bottom:12px; }
    .dss-err  { background:#fef2f2;border:1px solid #fca5a5;border-radius:8px;padding:10px 14px;font-size:.82rem;color:#991b1b;margin-bottom:12px; }
    </style>""", unsafe_allow_html=True)

    # Import backend optimizer
    import sys
    sys.path.insert(0, str(BASE_DIR))
    from optimizer import (
        build_distance_matrix as _build_matrix,
        run_cvrp_milp as _run_milp,
        compute_route_stats as _compute_stats,
    )

    for _k, _v in {
        "vrp_df_cust":None,"vrp_routes_idx":None,"vrp_routes_name":None,
        "vrp_status":None,"vrp_dist_mat":None,"vrp_df_nodes":None,
        "vrp_elapsed":None,"vrp_params":None,"vrp_log":None,
    }.items():
        if _k not in st.session_state:
            st.session_state[_k] = _v
    # Load destinasi dari MySQL jika belum ada di session
    if st.session_state.vrp_df_cust is None:
        _dest_db = get_destinasi()
        if _dest_db:
            st.session_state.vrp_df_cust = pd.DataFrame([
                {"Destination": r["nama"], "Demand": r["demand"],
                 "Lat": r["latitude"], "Lon": r["longitude"]}
                for r in _dest_db
            ])

    st.markdown("<div class='page-body'>", unsafe_allow_html=True)
    tab_input, tab_result = st.tabs(["  Input & Parameter", "  Hasil Optimasi MILP"])

    with tab_input:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Upload Data Destinasi (Excel)</div>', unsafe_allow_html=True)
        st.markdown("""<div class="dss-info">Kolom wajib: <b>Destination · Lat · Lon · Demand</b>.</div>""",
                    unsafe_allow_html=True)

        uploaded = st.file_uploader("Upload .xlsx", type=["xlsx"], key="vrp_up",
                                    label_visibility="collapsed")
        if uploaded:
            try:
                df_up = pd.read_excel(uploaded)
                miss  = {"Destination","Lat","Lon","Demand"} - set(df_up.columns)
                if miss:
                    st.error(f"Kolom tidak ditemukan: {', '.join(miss)}")
                    df_cust = pd.DataFrame(DEFAULT_DATA)
                else:
                    df_cust = df_up[["Destination","Lat","Lon","Demand"]].dropna().reset_index(drop=True)
                    df_cust["Demand"] = df_cust["Demand"].astype(int)
                    save_destinasi(df_cust.to_dict("records"), updated_by=current_user["username"])
                    st.success(f" {len(df_cust)} destinasi dimuat dan disimpan.")
            except Exception as e:
                st.error(f"Gagal baca file: {e}")
                df_cust = pd.DataFrame(DEFAULT_DATA)
        else:
            _p = DIR_DATA / "data_demand.xlsx"
            df_cust = pd.read_excel(_p)[["Destination","Lat","Lon","Demand"]].dropna().reset_index(drop=True) \
                      if _p.exists() else pd.DataFrame(DEFAULT_DATA)
            df_cust["Demand"] = df_cust["Demand"].astype(int)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Data Destinasi</div>', unsafe_allow_html=True)
        df_edit = st.data_editor(
            df_cust,
            column_config={
                "Destination": st.column_config.TextColumn("Destinasi", disabled=True, width="medium"),
                "Lat":  st.column_config.NumberColumn("Latitude",  disabled=True, format="%.5f"),
                "Lon":  st.column_config.NumberColumn("Longitude", disabled=True, format="%.5f"),
                "Demand": st.column_config.NumberColumn("Demand (unit)", min_value=0),
            },
            num_rows="fixed", hide_index=True, width='stretch', key="vrp_tbl",
        )
        st.session_state.vrp_df_cust = df_edit.copy()

        tot_dem = int(df_edit["Demand"].sum())
        n_act   = len(df_edit[df_edit["Demand"] > 0])
        st.markdown(f"<div class='dss-info'>Destinasi aktif: <b>{n_act}</b> &nbsp;|&nbsp; "
                    f"Total demand: <b>{tot_dem:,} unit</b></div>", unsafe_allow_html=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-title">Parameter Kendaraan & Solver</div>', unsafe_allow_html=True)
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1:
            p_veh = st.number_input("Jumlah Kendaraan", 1, 8, 4, key="p_veh")
        with c2:
            p_cap = st.number_input("Kapasitas (unit)", 100, 9999, 2700, 100, key="p_cap")
        with c3:
            p_stop = st.number_input("Maks Stop/Kendaraan", 2, 15, 4, key="p_stop")
        with c4:
            p_tl = st.number_input("Time Limit CBC (s)", 30, 600, 180, 10, key="p_tl")
        with c5:
            p_spd = st.number_input("Kecepatan (km/h)", 20, 100, 40, key="p_spd")

        tot_cap = p_veh * p_cap
        ok_cap  = tot_cap >= tot_dem
        st.markdown(
            f"<div class='dss-info'>Kapasitas armada: <b>{tot_cap:,}</b> &nbsp;|&nbsp; "
            f"Demand: <b>{tot_dem:,}</b> &nbsp;|&nbsp; "
            f"{'<span style=\"color:#15803d\"> Cukup</span>' if ok_cap else '<span style=\"color:#dc2626\"> Kurang</span>'}"
            f"</div>", unsafe_allow_html=True)

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        use_osrm = st.toggle("Gunakan OSRM (jarak jalan nyata)", value=False, key="p_osrm")
        if use_osrm:
            st.markdown("<div class='dss-warn'>OSRM membutuhkan internet dan lebih lama.</div>",
                        unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        run_btn = st.button("  Jalankan Optimasi MILP", type="primary",
                            width='stretch', key="vrp_run")

        if run_btn:
            df_active = st.session_state.vrp_df_cust[
                st.session_state.vrp_df_cust["Demand"] > 0].reset_index(drop=True)
            if len(df_active) == 0:
                st.error("Tidak ada destinasi dengan demand > 0.")
                st.stop()
            depot_row = pd.DataFrame([{"Destination":DEPOT_NAME,"Lat":DEPOT_LAT,"Lon":DEPOT_LON,"Demand":0}])
            df_nodes  = pd.concat([depot_row, df_active], ignore_index=True)

            st.markdown("**Step 1/2 — Membangun matriks jarak...**")
            pb = st.progress(0.0)
            t0 = time.time()
            dist_mat = _build_matrix(df_nodes, use_osrm=use_osrm, progress_callback=pb.progress)
            pb.progress(1.0)
            st.session_state.vrp_dist_mat = dist_mat
            st.session_state.vrp_df_nodes = df_nodes
            st.success(f"Matriks {len(df_nodes)}×{len(df_nodes)} selesai ({round(time.time()-t0,1)}s)")

            st.markdown("**Step 2/2 — Solver MILP (CBC)...**")
            with st.spinner(f"Menyelesaikan model MILP (maks {p_tl}s)..."):
                t1 = time.time()
                result = _run_milp(df_nodes, dist_mat, p_veh, p_cap, p_stop, p_tl)
                r_idx   = result["routes_idx"]
                r_name  = result["routes_name"]
                status  = result["status"]
                log     = result["solver_log"]
                elapsed = round(time.time()-t1, 2)

            st.session_state.vrp_routes_idx  = r_idx
            st.session_state.vrp_routes_name = r_name
            st.session_state.vrp_status      = status
            st.session_state.vrp_elapsed     = elapsed
            st.session_state.vrp_log         = log
            st.session_state.vrp_params      = {
                "vehicles":p_veh,"capacity":p_cap,"maxstops":p_stop,"speed":p_spd,"osrm":use_osrm}
            # Simpan hasil ke MySQL
            save_hasil_rute(
                run_by=current_user["username"],
                n_vehicles=p_veh, capacity=p_cap,
                total_dist=result.get("objective", 0),
                status=status,
                routes=[{"idx": ri, "name": rn} for ri, rn in zip(r_idx, r_name)],
                params={"vehicles":p_veh,"capacity":p_cap,"maxstops":p_stop,"speed":p_spd},
            )

            if r_idx:
                st.success(f" {len(r_idx)} rute terbentuk · status: **{status}** · {elapsed}s")
            else:
                st.error(f"Tidak ada rute. Status solver: **{status}**")
            with st.expander("Log solver"):
                st.code(log)

    with tab_result:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        r_idx    = st.session_state.vrp_routes_idx
        r_name   = st.session_state.vrp_routes_name
        dist_mat = st.session_state.vrp_dist_mat
        df_nodes = st.session_state.vrp_df_nodes
        params   = st.session_state.vrp_params
        status   = st.session_state.vrp_status
        elapsed  = st.session_state.vrp_elapsed
        log      = st.session_state.vrp_log

        if r_idx is None:
            st.info("Jalankan optimasi di tab **Input & Parameter** terlebih dahulu.")
        elif not r_idx:
            st.markdown(f"<div class='dss-err'>Solver selesai (status: <b>{status}</b>) "
                        f"namun tidak menghasilkan rute valid.</div>", unsafe_allow_html=True)
            if log:
                with st.expander("Log solver"):
                    st.code(log)
        else:
            speed    = params["speed"]
            capacity = params["capacity"]
            dist_lbl = "OSRM" if params["osrm"] else "Geodesic"

            stats = _compute_stats(
                r_idx, r_name, df_nodes, dist_mat,
                capacity, TRUCK_COLORS, avg_speed_kmh=float(speed)
            )

            total_dist = round(sum(s["distance_km"] for s in stats), 2)
            avg_util   = round(sum(s["util_pct"] for s in stats)/len(stats), 1)
            total_stop = sum(s["stops"] for s in stats)

            st.markdown(f"<div class='dss-info'>Solver: <b>PuLP CBC</b> · Status: <b>{status}</b>"
                        f" · Waktu: <b>{elapsed}s</b> · Jarak: <b>{dist_lbl}</b></div>",
                        unsafe_allow_html=True)

            k1,k2,k3,k4 = st.columns(4)
            skpi(k1,"Total Jarak",     f"{total_dist} km")
            skpi(k2,"Rata² Utilisasi", f"{avg_util} %")
            skpi(k3,"Total Stop",      f"{total_stop} destinasi")
            skpi(k4,"Kendaraan Aktif", f"{len(stats)}")

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-title">Rute per Kendaraan</div>', unsafe_allow_html=True)

            for row_pair in [stats[i:i+2] for i in range(0, len(stats), 2)]:
                col_left, col_right = st.columns(2)
                for col, s in zip([col_left, col_right], row_pair):
                    with col:
                        chips = ""
                        for i, stop in enumerate(s["route_name"]):
                            is_depot = (stop == DEPOT_NAME)
                            bg  = "#dcfce7" if is_depot else "#f3f8f4"
                            clr = "#166534" if is_depot else "#374151"
                            bdr = "" if is_depot else "border:1px solid #d1fae5;"
                            lbl = f" {stop}" if is_depot else stop
                            chips += (f'<span style="display:inline-block;background:{bg};color:{clr};'
                                      f'{bdr}border-radius:4px;padding:2px 8px;font-size:.73rem;'
                                      f'font-weight:{"700" if is_depot else "400"};margin:2px 1px;">'
                                      f'{lbl}</span>')
                            if i < len(s["route_name"])-1:
                                chips += '<span style="color:#9ca3af;font-size:.7rem;margin:0 1px;">→</span>'
                        badge_cls = "bg" if s["util_pct"]>=85 else "bw" if s["util_pct"]>=60 else "bc"
                        st.markdown(f"""
                        <div style="background:white;border:1px solid #e4ebe6;border-radius:10px;
                             border-top:4px solid {s['color']};padding:16px 18px;margin-bottom:14px;">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
                                <span style="font-size:.68rem;font-weight:700;text-transform:uppercase;
                                      letter-spacing:.8px;color:#7a9a82;">Kendaraan {s['vehicle']}</span>
                                <span class="badge {badge_cls}">{s['util_pct']}% muatan</span>
                            </div>
                            <div style="display:flex;gap:24px;align-items:baseline;margin-bottom:12px;">
                                <div>
                                    <div style="font-size:1.55rem;font-weight:700;color:#0a1a10;line-height:1.1;">{s['distance_km']} km</div>
                                    <div style="font-size:.75rem;color:#5a7a63;margin-top:2px;">~{s['est_min']} menit</div>
                                </div>
                                <div style="border-left:1px solid #e4ebe6;padding-left:24px;">
                                    <div style="font-size:1.15rem;font-weight:600;color:#0a1a10;line-height:1.1;">{s['stops']} stop</div>
                                    <div style="font-size:.75rem;color:#5a7a63;margin-top:2px;">{s['load']:,} unit</div>
                                </div>
                            </div>
                            <div style="background:#f8fdf9;border:1px solid #d1fae5;border-radius:6px;padding:8px 10px;line-height:2.2;">
                                {chips}
                            </div>
                        </div>""", unsafe_allow_html=True)

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            col_map, col_tbl = st.columns([3, 2])
            with col_map:
                st.markdown('<div class="chart-card-title"> Peta Rute Distribusi</div>', unsafe_allow_html=True)
                if FOLIUM_AVAILABLE:
                    ldict = {DEPOT_NAME: (DEPOT_LAT, DEPOT_LON)}
                    for _, row in df_nodes.iterrows():
                        ldict[row["Destination"]] = (row["Lat"], row["Lon"])
                    fmap = folium.Map([DEPOT_LAT, DEPOT_LON], zoom_start=11, tiles="CartoDB positron")
                    folium.Marker([DEPOT_LAT, DEPOT_LON], tooltip=f" {DEPOT_NAME}",
                        icon=folium.Icon(color="darkgreen", icon="industry", prefix="fa")).add_to(fmap)
                    for s in stats:
                        coords = [(ldict[n][0], ldict[n][1]) for n in s["route_name"] if n in ldict]
                        # Try to get actual road geometry from OSRM
                    try:
                        if params.get("osrm") and len(coords) >= 2:
                            _wps = ";".join(f"{c[1]},{c[0]}" for c in coords)
                            _url = f"http://router.project-osrm.org/route/v1/driving/{_wps}?overview=full&geometries=geojson"
                            _resp = requests.get(_url, timeout=10).json()
                            if "routes" in _resp and _resp["routes"]:
                                _geo = _resp["routes"][0]["geometry"]["coordinates"]
                                _road_coords = [(p[1], p[0]) for p in _geo]
                                folium.PolyLine(_road_coords, color=s["color"], weight=4, opacity=0.85).add_to(fmap)
                            else:
                                folium.PolyLine(coords, color=s["color"], weight=4, opacity=0.8).add_to(fmap)
                        else:
                            folium.PolyLine(coords, color=s["color"], weight=4, opacity=0.8).add_to(fmap)
                    except Exception:
                        folium.PolyLine(coords, color=s["color"], weight=4, opacity=0.8).add_to(fmap)
                        for seq, stop in enumerate(s["route_name"]):
                            if stop == DEPOT_NAME or stop not in ldict:
                                continue
                            slat, slon = ldict[stop]
                            dem = int(df_nodes[df_nodes["Destination"]==stop]["Demand"].values[0])
                            folium.CircleMarker([slat,slon], radius=9, color=s["color"],
                                fill=True, fill_opacity=0.85, fill_color=s["color"],
                                popup=folium.Popup(f"<b>{stop}</b><br>K{s['vehicle']}·Stop-{seq}<br>{dem:,} unit", max_width=200),
                                tooltip=f"{stop}|K{s['vehicle']}").add_to(fmap)
                            folium.Marker([slat,slon], icon=folium.DivIcon(
                                html=(f'<div style="font-size:9px;font-weight:700;color:white;'
                                      f'background:{s["color"]};border-radius:50%;width:18px;height:18px;'
                                      f'display:flex;align-items:center;justify-content:center;'
                                      f'border:2px solid white;">{seq}</div>'),
                                icon_size=(18,18), icon_anchor=(9,9))).add_to(fmap)
                    st_folium(fmap, height=460, width=None, returned_objects=[])
                else:
                    st.warning("Install: pip install folium streamlit-folium")

            with col_tbl:
                st.markdown('<div class="chart-card-title"> Detail Rute</div>', unsafe_allow_html=True)
                rows = []
                for s in stats:
                    for seq, stop in enumerate(s["route_name"]):
                        if stop == DEPOT_NAME:
                            continue
                        dem = int(df_nodes[df_nodes["Destination"]==stop]["Demand"].values[0]) \
                              if stop in df_nodes["Destination"].values else 0
                        rows.append({"Kendaraan":f"K-{s['vehicle']}","Stop ke":seq,
                                     "Destinasi":stop,"Demand (unit)":dem})
                if rows:
                    st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch')

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-title">Visualisasi Performa</div>', unsafe_allow_html=True)
            gc1, gc2 = st.columns(2)
            with gc1:
                fig_u = go.Figure(go.Bar(
                    x=[f"K-{s['vehicle']}" for s in stats], y=[s["util_pct"] for s in stats],
                    marker_color=[s["color"] for s in stats],
                    text=[f"{s['util_pct']}%" for s in stats], textposition="outside"))
                fig_u.add_hline(y=85, line_dash="dash", line_color=C["green"],
                                annotation_text="Target 85%", annotation_font=dict(size=9, color=C["green"]))
                _l = bl(300)
                _l.pop("legend", None)
                _l.pop("yaxis", None)
                fig_u.update_layout(**_l, yaxis=dict(range=[0,115],title="Utilisasi (%)",gridcolor=C["grid"]),
                                    xaxis_title="Kendaraan")
                chart_card("Utilisasi Muatan per Kendaraan", fig_u)
            with gc2:
                fig_d = go.Figure(go.Bar(
                    x=[f"K-{s['vehicle']}" for s in stats], y=[s["distance_km"] for s in stats],
                    marker_color=[s["color"] for s in stats],
                    text=[f"{s['distance_km']} km" for s in stats], textposition="outside"))
                _l2 = bl(300)
                _l2.pop("legend",None)
                fig_d.update_layout(**_l2, yaxis_title="Jarak (km)", xaxis_title="Kendaraan")
                chart_card("Jarak Tempuh per Kendaraan", fig_d)

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            dl_rows = [{"Kendaraan":s["vehicle"],"Rute":" → ".join(s["route_name"]),
                        "Jumlah Stop":s["stops"],"Demand (unit)":s["load"],
                        "Jarak (km)":s["distance_km"],"Utilisasi (%)":s["util_pct"],
                        "Est. Waktu (mnt)":s["est_min"],"Status Solver":status,
                        "Jenis Jarak":dist_lbl} for s in stats]
            st.download_button("  Download Hasil MILP (CSV)",
                data=pd.DataFrame(dl_rows).to_csv(index=False).encode("utf-8"),
                file_name="hasil_optimasi_milp.csv", mime="text/csv", key="dl_milp")

            with st.expander("Metodologi MILP-CVRP", expanded=False):
                st.markdown(f"""
**Formulasi MILP CVRP dengan MTZ Subtour Elimination**

- `x[i][j][k] ∈ {{0,1}}` — kendaraan *k* melewati arc *i→j*
- `u[i] ∈ ℝ` — posisi kunjungan node *i* (MTZ auxiliary)

**Fungsi Objektif**: `min Σᵢ Σ Σₖ d(i,j) · x[i][j][k]` *(jarak: {dist_lbl})*

**Solver**: COIN-OR CBC via PuLP · Time limit: {p_tl}s · Status: {status}
                """)
            if log:
                with st.expander("Log solver CBC"):
                    st.code(log)

    st.markdown("</div>", unsafe_allow_html=True)
