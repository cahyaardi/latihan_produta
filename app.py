import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random, base64
from pathlib import Path
from PIL import Image as _PILImage

try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False

# ── helpers ──────────────────────────────────────────────────────────────────
def get_logo_b64():
    p = Path(__file__).parent / "logo.png"
    if p.exists():
        with open(p, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

_logo_path = Path(__file__).parent / "logo.png"
_favicon   = _PILImage.open(_logo_path) if _logo_path.exists() else "🌿"

st.set_page_config(
    page_title="Agrinesia — Supply Chain Dashboard",
    page_icon=_favicon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
    box-sizing: border-box;
}
#MainMenu, footer { visibility: hidden !important; }
header, [data-testid="stHeader"], .stAppToolbar { display: none !important; }
.stMainBlockContainer, .block-container { padding-top: 0 !important; margin-top: 0 !important; }
div[data-testid="stSidebarNav"] { display: none !important; }
/* Hide sidebar collapse/expand controls and icon leakage */
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarCollapsedControl"] { display: none !important; }
/* Hide the "keyboard_double_arrow_right" material icon text */
section[data-testid="stSidebar"] > div > div:first-child > div[data-testid] { display: none !important; }
.st-emotion-cache-1cypcdb, [class*="sidebarHeader"], [class*="sidebarCollapse"] { display: none !important; }
/* Any span that contains only icon text at top of sidebar */
section[data-testid="stSidebar"] > div > div > div:first-child > button { display: none !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }

/* ══════════════════════════════════════════════════
   SIDEBAR — dark
══════════════════════════════════════════════════ */
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
/* Hide Streamlit's default collapse arrow icon text */
section[data-testid="stSidebar"] [data-testid="collapsedControl"] { display: none !important; }
button[data-testid="collapsedControl"] { display: none !important; }
/* Hide ALL icon fonts / material symbols text that leaks in */
section[data-testid="stSidebar"] span.material-symbols-rounded,
section[data-testid="stSidebar"] i.material-icons { display: none !important; }
/* Hide radio component entirely if it somehow still exists */
section[data-testid="stSidebar"] .stRadio { display: none !important; }
/* ── Nav Buttons ── */
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
/* Button text (Streamlit wraps in <p>) */
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

/* ══════════════════════════════════════════════════
   APP + MAIN CONTENT
══════════════════════════════════════════════════ */
.stApp, .stApp > div { background: #f5f6fa !important; }
.main .block-container { padding: 0 !important; max-width: 100% !important; }
.main > div { padding: 0 !important; }

/* ── Topbar ── */
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

/* ── KPI Cards — using custom HTML, metric-container hidden ── */
[data-testid="metric-container"] { display: none !important; }

/* ── Chart Cards ── */
.chart-card { background: #ffffff; border: 1px solid #eaecf0; border-radius: 12px; padding: 18px 20px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); margin-bottom: 16px; }
.chart-card-title { font-size: 0.9rem; font-weight: 600; color: #111827; }
.chart-card-sub   { font-size: 0.75rem; color: #9ca3af; margin-top: 2px; }
.sec-title { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; color: #9ca3af; margin: 0 0 12px; padding-bottom: 8px; border-bottom: 1px solid #f3f4f6; }
.divider { border: none; height: 1px; background: #f3f4f6; margin: 18px 0; }

/* ── Badges ── */
.badge { display: inline-flex; align-items: center; padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; }
.bg  { background: #dcfce7; color: #15803d; }
.bw  { background: #fef9c3; color: #854d0e; }
.bc  { background: #fee2e2; color: #991b1b; }

/* ── Info note ── */
.info-note { background: #f0fdf4; border-left: 3px solid #22c55e; padding: 10px 14px; border-radius: 0 8px 8px 0; font-size: 0.83rem; color: #166534; margin-bottom: 16px; line-height: 1.6; }

/* ── Param panel ── */
.param-panel { background: #f9fafb; border: 1px solid #eaecf0; border-radius: 10px; padding: 16px 18px; }
.param-title { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: #9ca3af; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #eaecf0; }

/* ── Status card ── */
.status-card { background: #fff; border: 1px solid #eaecf0; border-radius: 12px; padding: 16px; text-align: center; }
.status-card-label { font-size: 0.7rem; font-weight: 500; color: #9ca3af; margin-bottom: 8px; }
.status-card-value { font-size: 1.8rem; font-weight: 700; color: #111827; margin-bottom: 8px; letter-spacing: -0.6px; }

/* ── Pred card ── */
.pred-card  { background: #fff; border: 1px solid #eaecf0; border-radius: 12px; padding: 22px 18px; text-align: center; }
.pred-label { font-size: 0.7rem; font-weight: 500; color: #9ca3af; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.4px; }
.pred-value { font-size: 2.8rem; font-weight: 700; color: #111827; letter-spacing: -1.5px; line-height: 1; margin-bottom: 10px; }
.pred-rec   { font-size: 0.8rem; color: #6b7280; margin-top: 10px; padding-top: 10px; border-top: 1px solid #f3f4f6; line-height: 1.5; }

/* ── Route card ── */
.route-card { background: #fff; border: 1px solid #eaecf0; border-radius: 8px; padding: 11px 14px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }
.route-card:hover { border-color: #d1fae5; }
.route-city   { font-size: 0.875rem; font-weight: 600; color: #111827; }
.route-detail { font-size: 0.75rem; color: #9ca3af; margin-top: 2px; }

/* ── DMAIC ── */
.dmaic-wrap { display: flex; border-radius: 10px; overflow: hidden; border: 1px solid #eaecf0; margin-bottom: 20px; }
.dmaic-cell { flex: 1; padding: 12px 6px; text-align: center; font-size: 0.95rem; font-weight: 700; }
.dmaic-cell small { display: block; font-size: 0.6rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.8px; margin-top: 2px; opacity: 0.7; }

/* ══════════════════════════════════════════════════
   INPUTS — light mode, all labels dark & visible
══════════════════════════════════════════════════ */

/* Universal label fix — all input labels dark */
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

/* Number input — clean layout */
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
[data-testid="stNumberInput"] input:focus {
    outline: none !important;
    box-shadow: none !important;
}
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

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 8px !important;
    color: #111827 !important;
    min-height: 40px !important;
}
[data-testid="stSelectbox"] > div > div > div { color: #111827 !important; -webkit-text-fill-color: #111827 !important; }

/* Slider */
[data-testid="stSlider"] [role="slider"] { background: #10b981 !important; }
[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid] { background: #10b981 !important; }

/* Text input / textarea */
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

/* Data editor */
[data-testid="stDataFrame"] { border-radius: 10px !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 0; background: #f5f6fa; border-radius: 10px; padding: 3px; border: 1px solid #eaecf0; width: fit-content; margin-bottom: 16px; }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; color: #6b7280; font-size: 0.83rem; font-weight: 500; padding: 7px 16px; border: none; }
.stTabs [aria-selected="true"] { background: #ffffff !important; color: #111827 !important; font-weight: 600 !important; box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* ── Buttons ── */
.stButton > button[kind="primary"] { background: #16a34a !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; font-size: 0.83rem !important; padding: 8px 16px !important; }
.stButton > button[kind="primary"]:hover { background: #15803d !important; }
.stButton > button[kind="secondary"] { background: #ffffff !important; color: #374151 !important; border: 1px solid #d1d5db !important; border-radius: 8px !important; font-weight: 500 !important; font-size: 0.83rem !important; }
.stButton > button[kind="secondary"]:hover { background: #f9fafb !important; }

/* ── Warning / info boxes ── */
[data-testid="stAlert"] { border-radius: 8px !important; }

</style>
""", unsafe_allow_html=True)

# ── SEED ─────────────────────────────────────────────────────────────────────
np.random.seed(42); random.seed(42)

# ── DATA ─────────────────────────────────────────────────────────────────────
def gen_demand(days=90):
    dates  = pd.date_range(end=datetime.today(), periods=days, freq='D')
    trend  = np.linspace(800, 1100, days)
    seas   = 150 * np.sin(np.linspace(0, 3*np.pi, days))
    noise  = np.random.normal(0, 60, days)
    return pd.DataFrame({'Tanggal': dates, 'Permintaan': (trend+seas+noise).clip(300).astype(int)})

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

# ── COLORS ───────────────────────────────────────────────────────────────────
C = {'green':'#10b981','dark':'#0f172a','amber':'#f59e0b',
     'red':'#ef4444','grid':'#f8fafc','muted':'#94a3b8','blue':'#3b82f6'}

def bl(h=320, title=""):
    """base plotly layout"""
    return dict(
        height=h, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#64748b', size=11),
        margin=dict(l=4, r=8, t=8, b=4),
        xaxis=dict(gridcolor='#f8fafc', showgrid=True, zeroline=False,
                   linecolor='#f1f5f9', tickfont=dict(size=11, color='#94a3b8')),
        yaxis=dict(gridcolor='#f8fafc', showgrid=True, zeroline=False,
                   linecolor='#f1f5f9', tickfont=dict(size=11, color='#94a3b8')),
        legend=dict(bgcolor='rgba(0,0,0,0)', borderwidth=0,
                    font=dict(size=11, color='#64748b'), orientation='h',
                    y=1.08, x=0),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='white', bordercolor='#f1f5f9',
                        font=dict(family='Inter', size=12)),
    )

# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

_NAV = [
    ("Dashboard",            "Dashboard"),
    ("Peramalan Permintaan", "Peramalan Permintaan"),
    ("Prediksi Suhu",        "Prediksi Suhu"),
    ("Pengendalian Mutu",    "Pengendalian Mutu"),
    ("Optimasi Distribusi",  "Optimasi Distribusi"),
]

with st.sidebar:
    _b64 = get_logo_b64()
    _img = (f'<img src="data:image/png;base64,{_b64}" '
            f'style="height:36px;object-fit:contain;display:block;">') if _b64 else ""

    # ── Brand ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="padding:20px 16px 14px;border-bottom:1px solid #2d3548;
         margin-bottom:6px;">
        {_img}
        <div style="margin-top:10px;font-size:0.9rem;font-weight:700;
             color:#f9fafb;">Agrinesia</div>
        <div style="font-size:0.72rem;color:#6b7280;margin-top:2px;">
            Supply Chain System</div>
    </div>
    <div style="padding:10px 16px 6px;font-size:0.6rem;font-weight:700;
         letter-spacing:1px;text-transform:uppercase;color:#4b5563;">
        Menu
    </div>
    """, unsafe_allow_html=True)

    # ── Nav buttons ───────────────────────────────────────────────────────────
    for _key, _label in _NAV:
        _is_active = st.session_state.page == _key
        if st.button(_label, key=f"nav_{_key}", use_container_width=True):
            st.session_state.page = _key
            st.rerun()

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-top:20px;padding:12px 16px;border-top:1px solid #2d3548;">
        <div style="font-size:0.68rem;color:#4b5563;line-height:1.9;">
            PT Agrinesia Raya · Tugas Akhir<br>
            {datetime.now().strftime("%d %B %Y")}
        </div>
    </div>
    """, unsafe_allow_html=True)

page = st.session_state.page

# Inject active nav highlight based on current page
_active_map = {
    "Dashboard":            1,
    "Peramalan Permintaan": 2,
    "Prediksi Suhu":        3,
    "Pengendalian Mutu":    4,
    "Optimasi Distribusi":  5,
}
_ai = _active_map.get(page, 1)
st.markdown(f"""
<style>
section[data-testid="stSidebar"] .stButton:nth-of-type({_ai}) > button {{
    background: #252b3b !important;
    border-left: 3px solid #10b981 !important;
    padding-left: 11px !important;
    color: #10b981 !important;
}}
section[data-testid="stSidebar"] .stButton:nth-of-type({_ai}) > button p,
section[data-testid="stSidebar"] .stButton:nth-of-type({_ai}) > button span {{
    color: #10b981 !important;
    font-weight: 600 !important;
}}
</style>
""", unsafe_allow_html=True)

# ── TOPBAR helper ─────────────────────────────────────────────────────────────
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
    """Render a titled chart card. Title/subtitle above, plotly chart below."""
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


# ── Reusable simple KPI card ──────────────────────────────────────────────────
def skpi(col, label, value, delta=None, up=True):
    """Simple KPI card — no icon, compact, for sub-pages."""
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
        <div style="font-size:0.77rem;font-weight:600;color:#374151;
             margin-bottom:6px;">{label}</div>
        <div style="font-size:1.55rem;font-weight:700;color:#111827;
             letter-spacing:-0.5px;line-height:1;">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# PAGE — DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    topbar("Dashboard",
           "Ringkasan kinerja operasional supply chain PT Agrinesia Raya")

    # ── KPI Cards (custom HTML, immune to Streamlit color issues) ─────────────
    def kpi_card(col, icon, label, value, delta, delta_up=True, accent="#10b981"):
        delta_color = "#10b981" if delta_up else "#ef4444"
        delta_bg    = "#f0fdf4" if delta_up else "#fef2f2"
        arrow       = "↑" if delta_up else "↓"
        col.markdown(f"""
        <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:14px;
             padding:18px 20px 16px;box-shadow:0 1px 4px rgba(0,0,0,0.05);
             position:relative;overflow:hidden;">
            <div style="position:absolute;top:0;left:0;right:0;height:3px;
                 background:{accent};border-radius:14px 14px 0 0;"></div>
            <div style="display:flex;align-items:center;justify-content:space-between;
                 margin-bottom:12px;">
                <div style="font-size:0.8rem;font-weight:600;color:#374151;">
                    {label}
                </div>
                <div style="font-size:1.1rem;">{icon}</div>
            </div>
            <div style="font-size:1.8rem;font-weight:700;color:#111827;
                 letter-spacing:-0.8px;line-height:1;margin-bottom:10px;">
                {value}
            </div>
            <div style="display:inline-flex;align-items:center;gap:4px;
                 background:{delta_bg};color:{delta_color};
                 font-size:0.75rem;font-weight:600;
                 padding:3px 8px;border-radius:20px;">
                {arrow} {delta}
            </div>
        </div>
        """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4, gap="small")
    kpi_card(c1, "📦", "Permintaan Bulan Ini",   "32.450 unit", "+5.2%",   True,  "#10b981")
    kpi_card(c2, "🌡️", "Avg. Suhu Steam Tunnel", "87.3 °C",    "−0.8 °C", False, "#f59e0b")
    kpi_card(c3, "✅", "Order Fulfillment Rate", "93.6 %",     "+1.4%",   True,  "#3b82f6")
    kpi_card(c4, "⚠️", "Defect Rate",            "2.8 %",      "−0.3%",   True,  "#ef4444")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        df = gen_demand(90)
        df['MA7'] = df['Permintaan'].rolling(7).mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['Tanggal'], y=df['Permintaan'],
            fill='tozeroy', fillcolor='rgba(16,185,129,0.07)',
            line=dict(color=C['green'], width=2), name='Permintaan',
            hovertemplate='%{x|%d %b %Y}<br>%{y:,} unit<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=df['Tanggal'], y=df['MA7'],
            line=dict(color=C['amber'], width=1.5, dash='dot'), name='MA 7 Hari'
        ))
        fig.update_layout(**bl(295))
        chart_card("Tren Permintaan", fig, "90 hari terakhir · MA 7 hari")

    with col2:
        df_t = gen_temp(60)
        fig2 = go.Figure()
        fig2.add_hrect(y0=83, y1=90, fillcolor='rgba(22,163,74,0.06)', line_width=0,
                       annotation_text="Zona Aman", annotation_position="top left",
                       annotation_font=dict(color='#15803d', size=11))
        fig2.add_trace(go.Scatter(
            x=df_t['Tanggal'], y=df_t['Suhu'],
            line=dict(color=C['amber'], width=1.8),
            fill='tozeroy', fillcolor='rgba(245,158,11,0.06)',
            name='Suhu (°C)',
            hovertemplate='%{x|%d %b %Y}<br>%{y} °C<extra></extra>'
        ))
        fig2.update_layout(**bl(295))
        chart_card("Suhu Steam Tunnel", fig2, "60 hari terakhir · zona aman 83–90°C")

    col3, col4 = st.columns(2, gap="medium")

    with col3:
        df_o = gen_orders()
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(x=df_o['Bulan'], y=df_o['Terpenuhi'],
                              name='Terpenuhi', marker_color=C['green'],
                              marker_line_width=0))
        fig3.add_trace(go.Bar(x=df_o['Bulan'], y=df_o['Tidak Terpenuhi'],
                              name='Tidak Terpenuhi', marker_color='#fca5a5',
                              marker_line_width=0))
        fig3.update_layout(**bl(295), barmode='stack')
        chart_card("Order Fulfillment", fig3, "Terpenuhi vs tidak terpenuhi per bulan")

    with col4:
        df_d = gen_defect(24)
        fig4 = go.Figure()
        fig4.add_hline(y=5.0, line_dash='dash', line_color=C['red'],
                       annotation_text="Kritis (5%)", annotation_position="top right",
                       annotation_font=dict(size=10, color=C['red']))
        fig4.add_hline(y=3.0, line_dash='dot', line_color=C['amber'],
                       annotation_text="Warning (3%)", annotation_position="bottom right",
                       annotation_font=dict(size=10, color=C['amber']))
        fig4.add_trace(go.Scatter(
            x=df_d['Minggu'], y=df_d['Defect'],
            mode='lines+markers',
            line=dict(color=C['red'], width=2),
            marker=dict(size=5, color=C['red']),
            fill='tozeroy', fillcolor='rgba(239,68,68,0.05)',
            hovertemplate='%{x|%d %b}<br>Defect: %{y}%<extra></extra>'
        ))
        fig4.update_layout(**bl(295))
        chart_card("Defect Rate", fig4, "Per minggu · batas warning 3% · kritis 5%")

    st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE — PERAMALAN PERMINTAAN
# ════════════════════════════════════════════════════════════════════════════
elif page == "Peramalan Permintaan":
    topbar("Peramalan Permintaan",
           "Prediksi permintaan produk menggunakan model dekomposisi trend dan seasonality")

    st.markdown("""
    <div class="info-note">
        Model menggunakan <strong>dekomposisi trend + seasonality</strong> dari data historis
        untuk menghasilkan prediksi beserta confidence interval 95%.
    </div>
    """, unsafe_allow_html=True)

    col_p, col_c = st.columns([1, 2.5], gap="large")

    with col_p:
        st.markdown('<div class="param-panel">', unsafe_allow_html=True)
        st.markdown('<div class="param-title">Parameter</div>', unsafe_allow_html=True)
        periode = st.selectbox("Periode Peramalan", ["7 Hari","14 Hari","30 Hari","60 Hari","90 Hari"])
        produk  = st.selectbox("Produk", ["Lapis Ketan Wangi","Lapis Blackforest","Lapis Chocovilla Oreo"])
        metode  = st.selectbox("Metode", ["Trend + Seasonality","Moving Average","Exponential Smoothing"])
        st.markdown('</div>', unsafe_allow_html=True)

    n      = int(periode.split()[0])
    df_h   = gen_demand(60)
    lv     = df_h['Permintaan'].iloc[-1]
    fd     = pd.date_range(start=df_h['Tanggal'].iloc[-1]+timedelta(days=1), periods=n)
    fcast  = (np.linspace(lv, lv*1.08, n) + 80*np.sin(np.linspace(0,2*np.pi,n)) + np.random.normal(0,30,n)).clip(200).astype(int)
    ci_hi  = fcast + np.random.randint(60,120,n)
    ci_lo  = (fcast - np.random.randint(60,120,n)).clip(100)

    with col_c:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_h['Tanggal'], y=df_h['Permintaan'],
            line=dict(color='#374151', width=1.8), name='Historis'
        ))
        fig.add_trace(go.Scatter(
            x=list(fd)+list(fd[::-1]), y=list(ci_hi)+list(ci_lo[::-1]),
            fill='toself', fillcolor='rgba(22,163,74,0.09)',
            line=dict(color='rgba(0,0,0,0)'), name='CI 95%'
        ))
        fig.add_trace(go.Scatter(
            x=fd, y=fcast, line=dict(color=C['green'], width=2, dash='dash'),
            name='Forecast',
            hovertemplate='%{x|%d %b}<br>%{y:,} unit<extra></extra>'
        ))
        vx = df_h['Tanggal'].iloc[-1].timestamp()*1000
        fig.add_shape(type='line', x0=vx, x1=vx, y0=0, y1=1, xref='x', yref='paper',
                      line=dict(color='#9ca3af', width=1, dash='dot'))
        fig.add_annotation(x=vx, y=1, xref='x', yref='paper',
                           text='Sekarang', showarrow=False,
                           font=dict(size=10, color='#9ca3af'), yanchor='bottom')
        fig.update_layout(**bl(360))
        chart_card(f"Forecast {periode} — {produk}", fig)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    skpi(s1, "Rata-rata Forecast",  f"{int(fcast.mean()):,} unit")
    skpi(s2, "Nilai Tertinggi",     f"{int(fcast.max()):,} unit")
    skpi(s3, "Nilai Terendah",      f"{int(fcast.min()):,} unit")
    skpi(s4, "Total Hari Prediksi", f"{n} Hari")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Tabel Hasil Peramalan</div>', unsafe_allow_html=True)
    n_s = min(14, n)
    st.dataframe(pd.DataFrame({
        'Tanggal'         : [d.strftime('%d %b %Y') for d in fd[:n_s]],
        'Forecast (unit)' : fcast[:n_s],
        'Batas Bawah'     : ci_lo[:n_s],
        'Batas Atas'      : ci_hi[:n_s],
    }), width='stretch', hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE — PREDIKSI SUHU
# ════════════════════════════════════════════════════════════════════════════
elif page == "Prediksi Suhu":
    topbar("Prediksi Suhu Steam Tunnel",
           "Model regresi kuadratik: laju aliran steam terhadap suhu proses produksi")

    # ── Parameter ─────────────────────────────────────────────────────────────
    row_top = st.columns([1, 1, 1, 1, 1], gap="small")
    with row_top[0]:
        sf  = st.slider("Steamflow (kg/jam)", 50, 300, 150, 5)
    with row_top[1]:
        tek = st.slider("Tekanan Uap (bar)", 1.0, 5.0, 2.5, 0.1)
    with row_top[2]:
        dur = st.number_input("Durasi Proses (menit)", 1, 60, 20)
    with row_top[3]:
        batas_bawah = st.number_input("Batas Bawah Suhu (°C)", 50, 100, 83)
    with row_top[4]:
        batas_atas  = st.number_input("Batas Atas Suhu (°C)",  50, 150, 90)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # ── Model ─────────────────────────────────────────────────────────────────
    a, b, c  = -0.0004, 0.28, 45.0
    pt       = round(a*sf**2 + b*sf + c + tek*1.2, 1)
    deviasi  = round(pt - (batas_bawah + batas_atas)/2, 1)
    maks_dev = round((batas_atas - batas_bawah)/2, 1)

    # ── Status & notifikasi ───────────────────────────────────────────────────
    if pt < batas_bawah:
        status      = "DI BAWAH BATAS"
        status_color= "#d97706"
        status_bg   = "#fffbeb"
        status_border="#f59e0b"
        notif_icon  = "⚠️"
        notif_msg   = f"Suhu prediksi <b>{pt}°C</b> berada <b>di bawah batas minimum {batas_bawah}°C</b>. Deviasi: <b>{abs(pt-batas_bawah):.1f}°C</b>. Segera tingkatkan steamflow atau tekanan uap."
        badge_cls   = "bw"
    elif pt > batas_atas:
        status      = "DI ATAS BATAS"
        status_color= "#dc2626"
        status_bg   = "#fef2f2"
        status_border="#ef4444"
        notif_icon  = "🚨"
        notif_msg   = f"Suhu prediksi <b>{pt}°C</b> melebihi batas maksimum <b>{batas_atas}°C</b>. Deviasi: <b>+{pt-batas_atas:.1f}°C</b>. Kurangi steamflow segera untuk mencegah kerusakan produk."
        badge_cls   = "bc"
    else:
        status      = "DALAM BATAS"
        status_color= "#059669"
        status_bg   = "#f0fdf4"
        status_border="#10b981"
        notif_icon  = "✅"
        notif_msg   = f"Suhu prediksi <b>{pt}°C</b> berada dalam rentang optimal <b>{batas_bawah}°C – {batas_atas}°C</b>. Parameter produksi aman."
        badge_cls   = "bg"

    # ── Notifikasi banner ─────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{status_bg};border:1.5px solid {status_border};border-radius:10px;
         padding:14px 18px;margin-bottom:18px;display:flex;align-items:flex-start;gap:12px;">
        <div style="font-size:1.3rem;margin-top:1px;">{notif_icon}</div>
        <div>
            <div style="font-size:0.78rem;font-weight:700;color:{status_color};
                 letter-spacing:0.5px;text-transform:uppercase;margin-bottom:3px;">
                Status Suhu: {status}
            </div>
            <div style="font-size:0.85rem;color:#374151;line-height:1.6;">
                {notif_msg}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ───────────────────────────────────────────────────────────────
    kc1, kc2, kc3, kc4 = st.columns(4, gap="small")
    skpi(kc1, "Prediksi Suhu",    f"{pt} °C")
    skpi(kc2, "Batas Bawah",      f"{batas_bawah} °C")
    skpi(kc3, "Batas Atas",       f"{batas_atas} °C")
    skpi(kc4, "Deviasi dari Tengah", f"{deviasi:+.1f} °C", f"{abs(deviasi):.1f}°C", abs(deviasi)<=maks_dev)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 2], gap="medium")

    with col_l:
        # ── Grafik 1: Kurva Steamflow vs Suhu ────────────────────────────────
        sfr   = np.linspace(50, 300, 200)
        tc    = a*sfr**2 + b*sfr + c + tek*1.2
        sf_ob = np.random.uniform(60, 280, 40)
        t_ob  = a*sf_ob**2 + b*sf_ob + c + tek*1.2 + np.random.normal(0,1.5,40)

        fig = go.Figure()
        # Zona optimal (user-defined)
        fig.add_hrect(y0=batas_bawah, y1=batas_atas,
                      fillcolor='rgba(16,185,129,0.08)', line_width=0,
                      annotation_text=f"Zona Aman ({batas_bawah}–{batas_atas}°C)",
                      annotation_position="top left",
                      annotation_font=dict(color='#059669', size=11))
        # Garis batas
        fig.add_hline(y=batas_atas, line_dash='dash', line_color='#ef4444', line_width=1.5,
                      annotation_text=f"Batas Atas {batas_atas}°C",
                      annotation_position="top right",
                      annotation_font=dict(color='#ef4444', size=10))
        fig.add_hline(y=batas_bawah, line_dash='dash', line_color='#f59e0b', line_width=1.5,
                      annotation_text=f"Batas Bawah {batas_bawah}°C",
                      annotation_position="bottom right",
                      annotation_font=dict(color='#f59e0b', size=10))
        fig.add_trace(go.Scatter(x=sfr, y=tc,
                                 line=dict(color=C['green'], width=2.5),
                                 name='Kurva Model'))
        fig.add_trace(go.Scatter(x=sf_ob, y=t_ob,
                                 mode='markers', name='Data Observasi',
                                 marker=dict(color='#94a3b8', size=5, opacity=0.55)))
        fig.add_trace(go.Scatter(x=[sf], y=[pt], mode='markers',
                                 name='Input Saat Ini',
                                 marker=dict(color=status_color, size=13, symbol='diamond',
                                             line=dict(color='white', width=2))))
        lay = bl(320)
        lay['xaxis']['title'] = 'Steamflow (kg/jam)'
        lay['yaxis']['title'] = 'Suhu (°C)'
        fig.update_layout(**lay)
        chart_card("Kurva Hubungan Steamflow → Suhu", fig,
                   "Titik berlian = input saat ini")

        # ── Grafik 2: Fluktuasi suhu selama proses (line chart) ───────────────
        tr       = np.linspace(0, dur, int(dur*5)+1)
        # Simulasi: warmup + noise + drift kecil
        warmup   = batas_bawah + (pt - batas_bawah) * (1 - np.exp(-tr / (dur*0.15+0.1)))
        noise    = np.random.normal(0, 0.4, len(tr))
        drift    = np.linspace(0, np.random.uniform(-0.8, 0.8), len(tr))
        tpr      = (warmup + noise + drift).round(2)

        # Tandai titik di luar batas
        out_above = tpr > batas_atas
        out_below = tpr < batas_bawah

        fig3 = go.Figure()
        # Zona aman
        fig3.add_hrect(y0=batas_bawah, y1=batas_atas,
                       fillcolor='rgba(16,185,129,0.07)', line_width=0)
        # Garis batas atas & bawah
        fig3.add_hline(y=batas_atas, line_dash='dash', line_color='#ef4444', line_width=1.2,
                       annotation_text=f"Batas Atas ({batas_atas}°C)",
                       annotation_position="top right",
                       annotation_font=dict(color='#ef4444', size=10))
        fig3.add_hline(y=batas_bawah, line_dash='dash', line_color='#f59e0b', line_width=1.2,
                       annotation_text=f"Batas Bawah ({batas_bawah}°C)",
                       annotation_position="bottom right",
                       annotation_font=dict(color='#f59e0b', size=10))
        # Garis suhu utama
        fig3.add_trace(go.Scatter(
            x=tr, y=tpr,
            mode='lines',
            line=dict(color=C['amber'], width=2),
            name='Suhu Prediksi',
            hovertemplate='%{x:.1f} menit<br><b>%{y:.1f}°C</b><extra></extra>'
        ))
        # Titik merah = di atas batas
        if out_above.any():
            fig3.add_trace(go.Scatter(
                x=tr[out_above], y=tpr[out_above],
                mode='markers', name='Melebihi Batas Atas',
                marker=dict(color='#ef4444', size=7, symbol='circle')
            ))
        # Titik oranye = di bawah batas
        if out_below.any():
            fig3.add_trace(go.Scatter(
                x=tr[out_below], y=tpr[out_below],
                mode='markers', name='Di Bawah Batas Bawah',
                marker=dict(color='#f59e0b', size=7, symbol='circle')
            ))
        lay3 = bl(280)
        lay3['xaxis']['title'] = 'Waktu (menit)'
        lay3['yaxis']['title'] = 'Suhu (°C)'
        lay3['hovermode']       = 'x unified'
        fig3.update_layout(**lay3)
        chart_card(f"Fluktuasi Suhu Prediksi Selama {dur} Menit", fig3,
                   "Titik merah/oranye = suhu di luar batas")

    with col_r:
        # ── Tabel statistik proses ────────────────────────────────────────────
        st.markdown("""
        <div style="font-size:0.78rem;font-weight:600;color:#374151;
             margin-bottom:12px;">Statistik Profil Suhu</div>
        """, unsafe_allow_html=True)

        stats = [
            ("Suhu Prediksi",        f"{pt} °C",                         status_color),
            ("Batas Bawah",          f"{batas_bawah} °C",                 "#f59e0b"),
            ("Batas Atas",           f"{batas_atas} °C",                  "#ef4444"),
            ("Rentang Aman",         f"{batas_atas - batas_bawah} °C",    "#374151"),
            ("Suhu Min Profil",      f"{tpr.min():.1f} °C",               "#374151"),
            ("Suhu Maks Profil",     f"{tpr.max():.1f} °C",               "#374151"),
            ("Rata-rata Profil",     f"{tpr.mean():.1f} °C",              "#374151"),
            ("Std Dev Profil",       f"{tpr.std():.2f} °C",               "#374151"),
            ("Titik di Luar Batas",  f"{int(out_above.sum()+out_below.sum())} titik", "#ef4444" if (out_above|out_below).any() else "#10b981"),
        ]
        for label, val, col_clr in stats:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                 padding:9px 12px;background:#ffffff;border:1px solid #f3f4f6;
                 border-radius:8px;margin-bottom:5px;">
                <span style="font-size:0.8rem;color:#6b7280;">{label}</span>
                <span style="font-size:0.85rem;font-weight:700;color:{col_clr};">{val}</span>
            </div>
            """, unsafe_allow_html=True)

        # ── Peringatan detail ─────────────────────────────────────────────────
        n_above = int(out_above.sum())
        n_below = int(out_below.sum())
        if n_above > 0 or n_below > 0:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div style="font-size:0.78rem;font-weight:600;color:#374151;margin-bottom:8px;">
                Detail Peringatan
            </div>""", unsafe_allow_html=True)
            if n_above > 0:
                pct_a = round(n_above/len(tpr)*100, 1)
                st.markdown(f"""
                <div style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;
                     padding:10px 12px;margin-bottom:6px;">
                    <div style="font-size:0.78rem;font-weight:700;color:#dc2626;margin-bottom:2px;">
                        🚨 Suhu Melebihi Batas Atas
                    </div>
                    <div style="font-size:0.78rem;color:#374151;">
                        {n_above} titik ({pct_a}%) melebihi {batas_atas}°C.
                        Periksa valve dan tekanan uap.
                    </div>
                </div>""", unsafe_allow_html=True)
            if n_below > 0:
                pct_b = round(n_below/len(tpr)*100, 1)
                st.markdown(f"""
                <div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
                     padding:10px 12px;margin-bottom:6px;">
                    <div style="font-size:0.78rem;font-weight:700;color:#d97706;margin-bottom:2px;">
                        ⚠️ Suhu Di Bawah Batas Minimum
                    </div>
                    <div style="font-size:0.78rem;color:#374151;">
                        {n_below} titik ({pct_b}%) di bawah {batas_bawah}°C.
                        Tingkatkan steamflow untuk menjaga suhu optimal.
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
                 padding:10px 12px;margin-top:10px;">
                <div style="font-size:0.78rem;font-weight:700;color:#059669;margin-bottom:2px;">
                    ✅ Semua Titik Dalam Batas
                </div>
                <div style="font-size:0.78rem;color:#374151;">
                    Seluruh {len(tpr)} titik profil suhu berada dalam rentang
                    {batas_bawah}°C – {batas_atas}°C.
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE — PENGENDALIAN MUTU
# ════════════════════════════════════════════════════════════════════════════
elif page == "Pengendalian Mutu":
    topbar("Pengendalian Mutu",
           "Statistical Process Control (SPC) dan kerangka kerja DMAIC")

    st.markdown("""
    <div class="dmaic-wrap">
        <div class="dmaic-cell" style="background:#0a1a10;color:#fff;">
            D <small>Define</small>
        </div>
        <div class="dmaic-cell" style="background:#166534;color:#fff;">
            M <small>Measure</small>
        </div>
        <div class="dmaic-cell" style="background:#16a34a;color:#fff;">
            A <small>Analyze</small>
        </div>
        <div class="dmaic-cell" style="background:#4ade80;color:#0a1a10;">
            I <small>Improve</small>
        </div>
        <div class="dmaic-cell" style="background:#f0fdf4;color:#0a1a10; border-left:1px solid #e4ebe6;">
            C <small>Control</small>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df_d   = gen_defect(24)
    avg_d  = df_d['Defect'].mean()
    last_d = df_d['Defect'].iloc[-1]
    std_d  = df_d['Defect'].std()
    ucl    = avg_d + 3*std_d
    lcl    = max(0, avg_d - 3*std_d)

    k1, k2, k3, k4 = st.columns(4)
    skpi(k1, "Avg Defect Rate",         f"{avg_d:.2f} %",   f"{avg_d-3.0:+.2f}% vs target", avg_d<=3.0)
    skpi(k2, "Defect Rate Minggu Ini",  f"{last_d:.2f} %")
    skpi(k3, "Process Capability (Cp)", "1.32",              "+0.05", True)
    skpi(k4, "Sigma Level",             "3.8 σ",             "+0.1σ", True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2, gap="medium")

    with col_a:
        fig = go.Figure()
        fig.add_hline(y=ucl, line_dash='dash', line_color=C['red'],
                      annotation_text=f"UCL = {ucl:.2f}",
                      annotation_position="top right",
                      annotation_font=dict(size=10, color=C['red']))
        fig.add_hline(y=avg_d, line_color=C['green'], line_width=1.5,
                      annotation_text=f"CL = {avg_d:.2f}",
                      annotation_position="top right",
                      annotation_font=dict(size=10, color=C['green']))
        fig.add_hline(y=lcl, line_dash='dash', line_color=C['red'],
                      annotation_text=f"LCL = {lcl:.2f}",
                      annotation_position="bottom right",
                      annotation_font=dict(size=10, color=C['red']))
        pt_c = [C['red'] if (v>ucl or v<lcl) else C['green'] for v in df_d['Defect']]
        fig.add_trace(go.Scatter(
            x=df_d['Minggu'], y=df_d['Defect'],
            mode='lines+markers',
            line=dict(color='#374151', width=1.5),
            marker=dict(color=pt_c, size=7, line=dict(color='white', width=1)),
            name='Defect Rate (%)'
        ))
        fig.update_layout(**bl(320), yaxis_title="Defect Rate (%)")
        chart_card("Control Chart — Defect Rate", fig)

    with col_b:
        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(
            x=df_d['Defect'], nbinsx=10,
            marker_color=C['green'], opacity=0.72, name='Frekuensi',
            marker_line=dict(color='white', width=1)
        ))
        fig2.add_vline(x=avg_d, line_dash='dash', line_color=C['dark'],
                       annotation_text=f"Mean = {avg_d:.2f}%",
                       annotation_font=dict(size=10))
        fig2.add_vline(x=3.0, line_dash='dot', line_color=C['amber'],
                       annotation_text="Target = 3%",
                       annotation_font=dict(size=10, color=C['amber']))
        fig2.update_layout(**bl(320),
                           xaxis_title="Defect Rate (%)", yaxis_title="Frekuensi")
        chart_card("Distribusi Defect Rate", fig2)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Penilaian Status Kualitas</div>', unsafe_allow_html=True)

    for col, (label, val, wt, ct) in zip(
        st.columns(3),
        [("Defect Rate Rata-rata", avg_d,  3.0, 5.0),
         ("Defect Rate Terakhir",  last_d, 3.0, 5.0),
         ("Variabilitas (Std Dev)",std_d,  1.0, 1.5)]
    ):
        if val < wt:   b = '<span class="badge bg">Good</span>'
        elif val < ct: b = '<span class="badge bw">Warning</span>'
        else:          b = '<span class="badge bc">Critical</span>'
        col.markdown(f"""
        <div class="status-card">
            <div class="status-card-label">{label}</div>
            <div class="status-card-value">{val:.2f}</div>
            {b}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# PAGE — OPTIMASI DISTRIBUSI
# ════════════════════════════════════════════════════════════════════════════
elif page == "Optimasi Distribusi":
    topbar("Optimasi Distribusi",
           "Perencanaan rute pengiriman harian dan oncall berbasis algoritma optimasi")

    # ══ Shared algorithm helpers ═════════════════════════════════════════════
    from math import radians, sin, cos, sqrt, atan2, asin

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dlat = radians(lat2-lat1); dlon = radians(lon2-lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))

    # ── Sweep + NN (tab harian) ───────────────────────────────────────────────
    def sweep_cluster(df_s, dlat, dlon, cap, maxs, ntruck):
        df = df_s.copy()
        df["angle"] = df.apply(lambda r: atan2(r["Lat"]-dlat, r["Lon"]-dlon), axis=1)
        df = df.sort_values("angle").reset_index(drop=True)
        clusters, cur, load = [], [], 0
        for _, row in df.iterrows():
            d = row["Demand"]
            if load+d <= cap and len(cur) < maxs:
                cur.append(row["Destination"]); load += d
            else:
                clusters.append({"route":cur,"total_demand":load})
                cur, load = [row["Destination"]], d
        if cur: clusters.append({"route":cur,"total_demand":load})
        while len(clusters) > ntruck:
            last = clusters.pop()
            clusters[-1]["route"] += last["route"]
            clusters[-1]["total_demand"] += last["total_demand"]
        while len(clusters) < ntruck:
            lg = max(clusters, key=lambda x: x["total_demand"]); clusters.remove(lg)
            mid = len(lg["route"])//2
            clusters.append({"route":lg["route"][:mid],
                "total_demand":df[df["Destination"].isin(lg["route"][:mid])]["Demand"].sum()})
            clusters.append({"route":lg["route"][mid:],
                "total_demand":df[df["Destination"].isin(lg["route"][mid:])]["Demand"].sum()})
        return clusters

    def nn_route(stops, ldict):
        depot="Pabrik"; cur=depot; rem=list(stops); route=[depot]
        while rem:
            nxt=min(rem,key=lambda x:haversine(ldict[cur][0],ldict[cur][1],ldict[x][0],ldict[x][1]))
            route.append(nxt); cur=nxt; rem.remove(nxt)
        route.append(depot); return route

    def route_dist(route, ldict):
        return sum(haversine(ldict[route[i]][0],ldict[route[i]][1],
                             ldict[route[i+1]][0],ldict[route[i+1]][1])
                   for i in range(len(route)-1))

    # ── OR-Tools CVRP (tab oncall) ────────────────────────────────────────────
    def run_ortools(locations, names, demands_list, fleet, time_limit_s=20):
        try:
            from ortools.constraint_solver import pywrapcp, routing_enums_pb2
        except ImportError:
            return None, "ortools tidak tersedia. Install: pip install ortools"

        N = len(locations)
        dist_matrix = [[haversine(locations[i][0],locations[i][1],
                                  locations[j][0],locations[j][1])
                        for j in range(N)] for i in range(N)]

        num_v = len(fleet)
        manager = pywrapcp.RoutingIndexManager(N, num_v, 0)
        routing = pywrapcp.RoutingModel(manager)

        time_cbs = []
        for v in range(num_v):
            spd = fleet[v]["speed"]
            def tc(fi, ti, s=spd):
                fn=manager.IndexToNode(fi); tn=manager.IndexToNode(ti)
                return int(dist_matrix[fn][tn]/s*60)
            cb = routing.RegisterTransitCallback(tc)
            routing.SetArcCostEvaluatorOfVehicle(cb, v)
            time_cbs.append(cb)

        def dem_cb(fi):
            return demands_list[manager.IndexToNode(fi)]
        dc = routing.RegisterUnaryTransitCallback(dem_cb)
        routing.AddDimensionWithVehicleCapacity(dc, 0,
            [x["capacity"] for x in fleet], True, "Capacity")

        routing.AddDimensionWithVehicleTransits(time_cbs, 0, 10000, True, "Time")
        td = routing.GetDimensionOrDie("Time")
        td.SetGlobalSpanCostCoefficient(100)

        for node in range(1, N):
            routing.AddDisjunction([manager.NodeToIndex(node)], 100000)

        sp = pywrapcp.DefaultRoutingSearchParameters()
        sp.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
        sp.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        sp.time_limit.seconds = time_limit_s

        sol = routing.SolveWithParameters(sp)
        if not sol:
            return None, "Solver tidak menemukan solusi."

        results = []
        for v in range(num_v):
            idx = routing.Start(v)
            route_nodes, load = [], 0
            while not routing.IsEnd(idx):
                node = manager.IndexToNode(idx)
                route_nodes.append(node)
                load += demands_list[node]
                idx = sol.Value(routing.NextVar(idx))
            route_nodes.append(0)
            if len(route_nodes) <= 2: continue
            route_names = [names[n] for n in route_nodes]
            rt = sol.Value(td.CumulVar(routing.End(v)))
            stops = len(route_nodes)-2
            dist  = route_dist(route_names, {names[i]:locations[i] for i in range(N)})
            results.append({
                "kendaraan"   : v+1,
                "tipe"        : fleet[v]["type"],
                "route"       : route_names,
                "route_nodes" : route_nodes,
                "load"        : load,
                "stops"       : stops,
                "distance_km" : round(dist, 2),
                "waktu_menit" : rt,
                "util_pct"    : round(load/fleet[v]["capacity"]*100,1),
                "color"       : TRUCK_COLORS[v % len(TRUCK_COLORS)],
            })
        return results, None

    # ══ Constants ════════════════════════════════════════════════════════════
    STOP_MIN = 15
    TRUCK_COLORS = ["#16a34a","#d97706","#2563eb","#9333ea",
                    "#dc2626","#0891b2","#ca8a04","#15803d"]

    DEPOT = {"name":"Pabrik","lat":-6.513258,"lon":106.856054}

    MASTER_STORES = [
        {"Destination":"Stasiun",    "Lat":-6.593965,"Lon":106.790939,"Demand":374},
        {"Destination":"Cicurug",    "Lat":-6.758351,"Lon":106.799291,"Demand":92},
        {"Destination":"Cibadak",    "Lat":-6.893705,"Lon":106.785562,"Demand":97},
        {"Destination":"Puncak",     "Lat":-6.654124,"Lon":106.864429,"Demand":235},
        {"Destination":"Pajajaran",  "Lat":-6.616239,"Lon":106.814225,"Demand":285},
        {"Destination":"Sudirman",   "Lat":-6.587387,"Lon":106.797201,"Demand":169},
        {"Destination":"Sentul",     "Lat":-6.512885,"Lon":106.855652,"Demand":79},
        {"Destination":"Cibinong",   "Lat":-6.482988,"Lon":106.843517,"Demand":337},
        {"Destination":"BojongGede", "Lat":-6.495576,"Lon":106.794553,"Demand":148},
        {"Destination":"Cilebut",    "Lat":-6.530530,"Lon":106.800521,"Demand":120},
        {"Destination":"Dramaga",    "Lat":-6.572362,"Lon":106.748861,"Demand":166},
        {"Destination":"Leuwiliang", "Lat":-6.576214,"Lon":106.487030,"Demand":120},
        {"Destination":"Jalan Baru", "Lat":-6.561689,"Lon":106.794388,"Demand":311},
    ]
    DEFAULT_DEMAND = {r["Destination"]: r["Demand"] for r in MASTER_STORES}

    # ══ Session state ════════════════════════════════════════════════════════
    for k,v in [("daily_demand", DEFAULT_DEMAND.copy()),
                ("dist_result",  None),
                ("oncall_result", None),
                ("oncall_demand", DEFAULT_DEMAND.copy())]:
        if k not in st.session_state:
            st.session_state[k] = v

    # ══ TABS ═════════════════════════════════════════════════════════════════
    tab_h, tab_oc = st.tabs(["Pengiriman Harian", "Pengiriman Oncall"])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — PENGIRIMAN HARIAN (Sweep + NN)
    # ════════════════════════════════════════════════════════════════════════
    with tab_h:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        # Parameter
        st.markdown('<div class="sec-title">Parameter Kendaraan</div>', unsafe_allow_html=True)
        hc1, hc2, hc3, hc4 = st.columns(4)
        with hc1: h_trucks   = st.number_input("Jumlah Truk",          1,  8,  4, key="h_trucks")
        with hc2: h_cap      = st.number_input("Kapasitas/Truk (unit)", 500, 5000, 2700, 100, key="h_cap")
        with hc3: h_maxstops = st.number_input("Maks Stop/Truk",        2,  10,  4, key="h_maxs")
        with hc4: h_speed    = st.number_input("Kecepatan (km/h)",      20, 80,  40, key="h_spd")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # Demand editor
        st.markdown('<div class="sec-title">Rencana Pengiriman Harian</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-note">
            Data toko bersumber dari <b>Data Demand.xlsx</b>.
            Ubah kolom <b>Demand Hari Ini</b> sesuai kebutuhan, lalu klik <b>Jalankan Optimasi</b>.
        </div>""", unsafe_allow_html=True)

        df_h_disp = pd.DataFrame([{
            "Toko"            : r["Destination"],
            "Demand Hari Ini" : st.session_state.daily_demand.get(r["Destination"], r["Demand"]),
            "Demand Default"  : r["Demand"],
            "Lat": r["Lat"], "Lon": r["Lon"],
        } for r in MASTER_STORES])

        tc1, tc2 = st.columns([4,1])
        with tc1:
            df_h_edit = st.data_editor(df_h_disp,
                column_config={
                    "Toko"           : st.column_config.TextColumn("Toko", disabled=True, width="medium"),
                    "Demand Hari Ini": st.column_config.NumberColumn("Demand Hari Ini", min_value=0, max_value=9999),
                    "Demand Default" : st.column_config.NumberColumn("Demand Default",  disabled=True),
                    "Lat"            : st.column_config.NumberColumn("Latitude",  disabled=True, format="%.5f"),
                    "Lon"            : st.column_config.NumberColumn("Longitude", disabled=True, format="%.5f"),
                },
                num_rows="fixed", width=860, hide_index=True, key="h_demand_editor")
        with tc2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            h_run   = st.button("Jalankan Optimasi", type="primary", use_container_width=True, key="h_run")
            h_reset = st.button("Reset Demand",      use_container_width=True, key="h_reset")
            if h_reset:
                st.session_state.daily_demand = DEFAULT_DEMAND.copy()
                st.session_state.dist_result  = None
                st.rerun()

        for _, row in df_h_edit.iterrows():
            st.session_state.daily_demand[row["Toko"]] = int(row["Demand Hari Ini"])

        # Run Sweep + NN
        if h_run:
            daily = {row["Toko"]:int(row["Demand Hari Ini"]) for _,row in df_h_edit.iterrows()}
            df_stores = pd.DataFrame([
                {"Destination":r["Destination"],"Lat":r["Lat"],"Lon":r["Lon"],
                 "Demand":daily.get(r["Destination"],r["Demand"])}
                for r in MASTER_STORES if daily.get(r["Destination"],r["Demand"])>0])
            if len(df_stores)==0:
                st.error("Semua demand 0. Isi minimal satu toko.")
            else:
                ldict={DEPOT["name"]:(DEPOT["lat"],DEPOT["lon"])}
                for _,r in df_stores.iterrows(): ldict[r["Destination"]]=(r["Lat"],r["Lon"])
                clusters = sweep_cluster(df_stores,DEPOT["lat"],DEPOT["lon"],
                                         h_cap,h_maxstops,h_trucks)
                res=[]
                for k,c in enumerate(clusters):
                    route  = nn_route(c["route"],ldict)
                    dist   = route_dist(route,ldict)
                    stops  = len(c["route"])
                    travel = dist/h_speed*60
                    total  = travel + stops*STOP_MIN
                    res.append({"truk":k+1,"route":route,"stops":stops,
                        "total_demand":c["total_demand"],"distance_km":round(dist,2),
                        "total_min":round(total,0),"color":TRUCK_COLORS[k%len(TRUCK_COLORS)],
                        "util_pct":round(c["total_demand"]/h_cap*100,1)})
                st.session_state.dist_result  = res
                st.session_state.daily_demand = daily

        # ── Results ──────────────────────────────────────────────────────────
        if st.session_state.dist_result:
            res = st.session_state.dist_result
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-title">Hasil Optimasi — Sweep + Nearest Neighbor</div>', unsafe_allow_html=True)

            m1,m2,m3,m4 = st.columns(4)
            skpi(m1, "Total Jarak",   f"{sum(r['distance_km'] for r in res):.1f} km")
            skpi(m2, "Total Stop",    f"{sum(r['stops'] for r in res)} toko")
            skpi(m3, "Avg Utilisasi", f"{sum(r['util_pct'] for r in res)/len(res):.1f} %")
            skpi(m4, "Waktu Terlama", f"{int(max(r['total_min'] for r in res))} menit")

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            tcols = st.columns(min(len(res),4))
            for idx,r in enumerate(res):
                with tcols[idx%4]:
                    rstr = " → ".join(r["route"])
                    th,tm = int(r["total_min"])//60, int(r["total_min"])%60
                    sc = "bg" if r["util_pct"]>=85 else "bw" if r["util_pct"]>=60 else "bc"
                    st.markdown(f"""
                    <div style="background:white;border:1px solid #e4ebe6;border-radius:8px;
                         border-top:3px solid {r['color']};padding:16px;margin-bottom:12px;">
                        <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                             letter-spacing:0.8px;color:#7a9a82;margin-bottom:6px;">Truk {r['truk']}</div>
                        <div style="font-size:1.4rem;font-weight:700;color:#0a1a10;margin-bottom:4px;">
                            {r['distance_km']} km</div>
                        <div style="font-size:0.8rem;color:#5a7a63;margin-bottom:8px;">
                            {r['stops']} stop &nbsp;·&nbsp; {th}j {tm}m &nbsp;·&nbsp; {int(r['total_demand'])} unit</div>
                        <div style="font-size:0.73rem;color:#374151;background:#f3f8f4;
                             padding:6px 8px;border-radius:4px;line-height:1.6;word-break:break-word;">
                            {rstr}</div>
                        <div style="margin-top:8px;"><span class="badge {sc}">{r['util_pct']}% muatan</span></div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            cmap, cri = st.columns([3,2], gap="medium")

            with cmap:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown('<div class="chart-card-title">Peta Rute Distribusi Harian</div>', unsafe_allow_html=True)
                if not FOLIUM_AVAILABLE:
                    st.warning("pip install folium streamlit-folium")
                else:
                    ldict_m={DEPOT["name"]:(DEPOT["lat"],DEPOT["lon"])}
                    for r in MASTER_STORES: ldict_m[r["Destination"]]=(r["Lat"],r["Lon"])
                    m = folium.Map(location=[DEPOT["lat"],DEPOT["lon"]],zoom_start=11,tiles="CartoDB positron")
                    folium.Marker([DEPOT["lat"],DEPOT["lon"]],
                        popup=folium.Popup("<b>Pabrik (Depot)</b>",max_width=150),
                        tooltip="Pabrik",
                        icon=folium.Icon(color="darkgreen",icon="industry",prefix="fa")).add_to(m)
                    for r in res:
                        coords=[(ldict_m[s][0],ldict_m[s][1]) for s in r["route"] if s in ldict_m]
                        folium.PolyLine(coords,color=r["color"],weight=3,opacity=0.75,
                            tooltip=f"Truk {r['truk']} — {r['distance_km']} km").add_to(m)
                        for seq,stop in enumerate(r["route"]):
                            if stop==DEPOT["name"] or stop not in ldict_m: continue
                            slat,slon=ldict_m[stop]
                            dem=st.session_state.daily_demand.get(stop,0)
                            folium.CircleMarker([slat,slon],radius=8,color=r["color"],
                                fill=True,fill_opacity=0.85,fill_color=r["color"],
                                popup=folium.Popup(
                                    f"<b>{stop}</b><br>Truk {r['truk']} — Stop {seq}<br>Demand: {dem} unit",
                                    max_width=200),
                                tooltip=f"{stop} | Truk {r['truk']}").add_to(m)
                            folium.Marker([slat,slon],icon=folium.DivIcon(
                                html=f'<div style="font-size:9px;font-weight:700;color:white;background:{r["color"]};border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;border:2px solid white;">{seq}</div>',
                                icon_size=(18,18),icon_anchor=(9,9))).add_to(m)
                    st_folium(m,height=480,width=None)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.markdown('<div class="sec-title">Detail Rute</div>', unsafe_allow_html=True)
                tbl=[]
                for r in res:
                    for seq,stop in enumerate(r["route"]):
                        if stop==DEPOT["name"]: continue
                        tbl.append({"Truk":f"Truk {r['truk']}","Stop":seq,"Toko":stop,
                                    "Demand":st.session_state.daily_demand.get(stop,0)})
                if tbl: st.dataframe(pd.DataFrame(tbl),width="stretch",hide_index=True)

            with cri:
                fd=go.Figure(); fd.add_trace(go.Bar(
                    x=[f"Truk {r['truk']}" for r in res],y=[r["distance_km"] for r in res],
                    marker_color=[r["color"] for r in res],marker_line_width=0,
                    text=[f"{r['distance_km']} km" for r in res],textposition="outside"))
                bld=bl(215); bld.pop("legend",None)
                fd.update_layout(**bld,yaxis_title="Jarak (km)")
                chart_card("Jarak per Truk",fd)

                fu=go.Figure(); fu.add_trace(go.Bar(
                    x=[f"Truk {r['truk']}" for r in res],y=[r["util_pct"] for r in res],
                    marker_color=["#dc2626" if r["util_pct"]<60 else "#d97706" if r["util_pct"]<85 else "#16a34a" for r in res],
                    marker_line_width=0,text=[f"{r['util_pct']}%" for r in res],textposition="outside"))
                fu.add_hline(y=85,line_dash="dash",line_color=C["green"],
                    annotation_text="Target 85%",annotation_font=dict(size=10,color=C["green"]))
                blu=bl(215); blu.pop("legend",None); blu.pop("yaxis",None)
                fu.update_layout(**blu,yaxis=dict(range=[0,115],gridcolor=C["grid"]),yaxis_title="Utilisasi (%)")
                chart_card("Utilisasi Muatan",fu)

                ft=go.Figure(); ft.add_trace(go.Bar(
                    x=[f"Truk {r['truk']}" for r in res],y=[r["total_min"] for r in res],
                    marker_color=[r["color"] for r in res],marker_line_width=0,
                    text=[f"{int(r['total_min'])} min" for r in res],textposition="outside"))
                blt=bl(215); blt.pop("legend",None)
                ft.update_layout(**blt,yaxis_title="Waktu (menit)")
                chart_card("Estimasi Waktu",ft)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — ONCALL (OR-Tools CVRP)
    # ════════════════════════════════════════════════════════════════════════
    with tab_oc:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-note">
            Tab ini menggunakan algoritma <b>OR-Tools CVRP</b> dengan optimasi berbasis waktu
            (minimize max time). Armada campuran Truk + CDE dengan kapasitas berbeda.
            Pastikan <code>ortools</code> sudah terinstall: <code>pip install ortools</code>
        </div>""", unsafe_allow_html=True)

        # ── Armada config ─────────────────────────────────────────────────────
        st.markdown('<div class="sec-title">Konfigurasi Armada</div>', unsafe_allow_html=True)
        oc1, oc2 = st.columns(2, gap="large")

        with oc1:
            st.markdown("**Truk**")
            oc_truck_n   = st.number_input("Jumlah Truk",          0, 8, 4, key="oc_tn")
            oc_truck_cap = st.number_input("Kapasitas Truk (unit)", 100, 5000, 2700, 100, key="oc_tc")
            oc_truck_spd = st.number_input("Kecepatan Truk (km/h)",20, 80, 40, key="oc_ts")
        with oc2:
            st.markdown("**CDE**")
            oc_cde_n   = st.number_input("Jumlah CDE",          0, 8, 4, key="oc_cn")
            oc_cde_cap = st.number_input("Kapasitas CDE (unit)",100, 3000, 1000, 100, key="oc_cc")
            oc_cde_spd = st.number_input("Kecepatan CDE (km/h)",20, 100, 60, key="oc_cs")

        oc_total_stock = st.number_input("Total Stok Tersedia (unit)", 1000, 50000, 8500, 100,
                                          key="oc_stock")
        oc_timelimit   = st.number_input("Batas Waktu Solver (detik)",  5, 120, 20, key="oc_tl")

        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # ── Demand editor oncall ──────────────────────────────────────────────
        st.markdown('<div class="sec-title">Demand Pengiriman Oncall</div>', unsafe_allow_html=True)

        df_oc_disp = pd.DataFrame([{
            "Toko"   : r["Destination"],
            "Demand" : st.session_state.oncall_demand.get(r["Destination"], r["Demand"]),
            "Default": r["Demand"],
            "Lat"    : r["Lat"], "Lon": r["Lon"],
        } for r in MASTER_STORES])

        oc_tc1, oc_tc2 = st.columns([4,1])
        with oc_tc1:
            df_oc_edit = st.data_editor(df_oc_disp,
                column_config={
                    "Toko"   : st.column_config.TextColumn("Toko",    disabled=True, width="medium"),
                    "Demand" : st.column_config.NumberColumn("Demand Oncall", min_value=0, max_value=9999),
                    "Default": st.column_config.NumberColumn("Default",       disabled=True),
                    "Lat"    : st.column_config.NumberColumn("Latitude",  disabled=True, format="%.5f"),
                    "Lon"    : st.column_config.NumberColumn("Longitude", disabled=True, format="%.5f"),
                },
                num_rows="fixed", width=860, hide_index=True, key="oc_demand_editor")
        with oc_tc2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            oc_run   = st.button("Jalankan Optimasi", type="primary", use_container_width=True, key="oc_run")
            oc_reset = st.button("Reset Demand",      use_container_width=True, key="oc_reset")
            if oc_reset:
                st.session_state.oncall_demand  = DEFAULT_DEMAND.copy()
                st.session_state.oncall_result  = None
                st.rerun()

        for _, row in df_oc_edit.iterrows():
            st.session_state.oncall_demand[row["Toko"]] = int(row["Demand"])

        # ── Run OR-Tools ──────────────────────────────────────────────────────
        if oc_run:
            oc_demand = {row["Toko"]:int(row["Demand"]) for _,row in df_oc_edit.iterrows()}
            active = [r for r in MASTER_STORES if oc_demand.get(r["Destination"],0)>0]

            if not active:
                st.error("Semua demand 0.")
            else:
                # Scale demand if exceeds stock
                total_dem = sum(oc_demand[r["Destination"]] for r in active)
                if total_dem > oc_total_stock:
                    ratio = oc_total_stock / total_dem
                    oc_demand = {k: round(v*ratio) for k,v in oc_demand.items()}
                    st.warning(f"Total demand ({total_dem}) melebihi stok ({oc_total_stock}). "
                               f"Demand di-scale dengan rasio {ratio:.2f}.")

                locations_oc = [(DEPOT["lat"],DEPOT["lon"])]
                names_oc     = [DEPOT["name"]]
                demands_oc   = [0]
                for r in active:
                    locations_oc.append((r["Lat"],r["Lon"]))
                    names_oc.append(r["Destination"])
                    demands_oc.append(int(oc_demand[r["Destination"]]))

                fleet = ([{"type":"TRUCK","capacity":oc_truck_cap,"speed":oc_truck_spd}]*oc_truck_n +
                         [{"type":"CDE",  "capacity":oc_cde_cap,  "speed":oc_cde_spd }]*oc_cde_n)

                if not fleet:
                    st.error("Tambahkan minimal 1 kendaraan.")
                else:
                    with st.spinner("Menjalankan OR-Tools CVRP..."):
                        oc_res, err = run_ortools(locations_oc, names_oc, demands_oc,
                                                   fleet, oc_timelimit)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.oncall_result  = oc_res
                        st.session_state.oncall_demand  = oc_demand

        # ── Show oncall results ───────────────────────────────────────────────
        if st.session_state.oncall_result:
            oc_res = st.session_state.oncall_result
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown('<div class="sec-title">Hasil Optimasi — OR-Tools CVRP (Minimize Max Time)</div>', unsafe_allow_html=True)

            total_dist_oc  = sum(r["distance_km"]  for r in oc_res)
            total_stops_oc = sum(r["stops"]         for r in oc_res)
            max_time_oc    = max(r["waktu_menit"]   for r in oc_res)
            avg_util_oc    = sum(r["util_pct"]      for r in oc_res)/len(oc_res)

            o1,o2,o3,o4 = st.columns(4)
            skpi(o1, "Total Jarak",   f"{total_dist_oc:.1f} km")
            skpi(o2, "Total Stop",    f"{total_stops_oc} toko")
            skpi(o3, "Max Waktu",     f"{max_time_oc} menit")
            skpi(o4, "Avg Utilisasi", f"{avg_util_oc:.1f} %")

            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            oc_cols = st.columns(min(len(oc_res),4))
            for idx,r in enumerate(oc_res):
                with oc_cols[idx%4]:
                    rstr = " → ".join(r["route"])
                    th,tm = r["waktu_menit"]//60, r["waktu_menit"]%60
                    sc = "bg" if r["util_pct"]>=85 else "bw" if r["util_pct"]>=60 else "bc"
                    tipe_color = "#2563eb" if r["tipe"]=="CDE" else "#16a34a"
                    st.markdown(f"""
                    <div style="background:white;border:1px solid #e4ebe6;border-radius:8px;
                         border-top:3px solid {r['color']};padding:16px;margin-bottom:12px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                            <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                                 letter-spacing:0.8px;color:#7a9a82;">Kendaraan {r['kendaraan']}</div>
                            <span style="font-size:0.68rem;font-weight:700;background:{tipe_color}20;
                                 color:{tipe_color};padding:2px 7px;border-radius:3px;">{r['tipe']}</span>
                        </div>
                        <div style="font-size:1.4rem;font-weight:700;color:#0a1a10;margin-bottom:4px;">
                            {r['distance_km']} km</div>
                        <div style="font-size:0.8rem;color:#5a7a63;margin-bottom:8px;">
                            {r['stops']} stop &nbsp;·&nbsp; {th}j {tm}m &nbsp;·&nbsp; {int(r['load'])} unit</div>
                        <div style="font-size:0.73rem;color:#374151;background:#f3f8f4;
                             padding:6px 8px;border-radius:4px;line-height:1.6;word-break:break-word;">
                            {rstr}</div>
                        <div style="margin-top:8px;"><span class="badge {sc}">{r['util_pct']}% muatan</span></div>
                    </div>""", unsafe_allow_html=True)

            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            oc_map_col, oc_chart_col = st.columns([3,2], gap="medium")

            with oc_map_col:
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.markdown('<div class="chart-card-title">Peta Rute Distribusi Oncall</div>', unsafe_allow_html=True)
                if not FOLIUM_AVAILABLE:
                    st.warning("pip install folium streamlit-folium")
                else:
                    ldict_oc={DEPOT["name"]:(DEPOT["lat"],DEPOT["lon"])}
                    for r in MASTER_STORES: ldict_oc[r["Destination"]]=(r["Lat"],r["Lon"])

                    m2 = folium.Map(location=[DEPOT["lat"],DEPOT["lon"]],
                                    zoom_start=11,tiles="CartoDB positron")
                    folium.Marker([DEPOT["lat"],DEPOT["lon"]],
                        popup=folium.Popup("<b>Pabrik (Depot)</b>",max_width=150),
                        tooltip="Pabrik",
                        icon=folium.Icon(color="darkgreen",icon="industry",prefix="fa")).add_to(m2)

                    for r in oc_res:
                        coords=[(ldict_oc[s][0],ldict_oc[s][1]) for s in r["route"] if s in ldict_oc]
                        folium.PolyLine(coords,color=r["color"],weight=3,opacity=0.75,
                            tooltip=f"Kendaraan {r['kendaraan']} ({r['tipe']}) — {r['distance_km']} km").add_to(m2)
                        for seq,stop in enumerate(r["route"]):
                            if stop==DEPOT["name"] or stop not in ldict_oc: continue
                            slat,slon=ldict_oc[stop]
                            dem=st.session_state.oncall_demand.get(stop,0)
                            icon_color="blue" if r["tipe"]=="CDE" else "green"
                            folium.CircleMarker([slat,slon],radius=8,color=r["color"],
                                fill=True,fill_opacity=0.85,fill_color=r["color"],
                                popup=folium.Popup(
                                    f"<b>{stop}</b><br>Kendaraan {r['kendaraan']} ({r['tipe']})"
                                    f"<br>Stop ke-{seq}<br>Demand: {dem} unit",max_width=220),
                                tooltip=f"{stop} | {r['tipe']} {r['kendaraan']}").add_to(m2)
                            folium.Marker([slat,slon],icon=folium.DivIcon(
                                html=f'<div style="font-size:9px;font-weight:700;color:white;background:{r["color"]};border-radius:50%;width:18px;height:18px;display:flex;align-items:center;justify-content:center;border:2px solid white;">{seq}</div>',
                                icon_size=(18,18),icon_anchor=(9,9))).add_to(m2)
                    st_folium(m2,height=480,width=None)
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                st.markdown('<div class="sec-title">Detail Rute Oncall</div>', unsafe_allow_html=True)
                oc_tbl=[]
                for r in oc_res:
                    for seq,stop in enumerate(r["route"]):
                        if stop==DEPOT["name"]: continue
                        oc_tbl.append({"Kendaraan":f"{r['tipe']} {r['kendaraan']}",
                            "Stop":seq,"Toko":stop,
                            "Demand":st.session_state.oncall_demand.get(stop,0)})
                if oc_tbl: st.dataframe(pd.DataFrame(oc_tbl),width="stretch",hide_index=True)

            with oc_chart_col:
                # Jarak per kendaraan
                fod=go.Figure(); fod.add_trace(go.Bar(
                    x=[f"{r['tipe']} {r['kendaraan']}" for r in oc_res],
                    y=[r["distance_km"] for r in oc_res],
                    marker_color=[r["color"] for r in oc_res],marker_line_width=0,
                    text=[f"{r['distance_km']} km" for r in oc_res],textposition="outside"))
                bod=bl(215); bod.pop("legend",None)
                fod.update_layout(**bod,yaxis_title="Jarak (km)")
                chart_card("Jarak per Kendaraan",fod)

                # Waktu per kendaraan
                fot=go.Figure(); fot.add_trace(go.Bar(
                    x=[f"{r['tipe']} {r['kendaraan']}" for r in oc_res],
                    y=[r["waktu_menit"] for r in oc_res],
                    marker_color=[r["color"] for r in oc_res],marker_line_width=0,
                    text=[f"{r['waktu_menit']} min" for r in oc_res],textposition="outside"))
                bot=bl(215); bot.pop("legend",None)
                fot.update_layout(**bot,yaxis_title="Waktu (menit)")
                chart_card("Waktu per Kendaraan",fot)

                # Utilisasi
                fou=go.Figure(); fou.add_trace(go.Bar(
                    x=[f"{r['tipe']} {r['kendaraan']}" for r in oc_res],
                    y=[r["util_pct"] for r in oc_res],
                    marker_color=["#dc2626" if r["util_pct"]<60 else "#d97706" if r["util_pct"]<85 else "#16a34a"
                                   for r in oc_res],
                    marker_line_width=0,
                    text=[f"{r['util_pct']}%" for r in oc_res],textposition="outside"))
                fou.add_hline(y=85,line_dash="dash",line_color=C["green"],
                    annotation_text="Target 85%",annotation_font=dict(size=10,color=C["green"]))
                bou=bl(215); bou.pop("legend",None); bou.pop("yaxis",None)
                fou.update_layout(**bou,yaxis=dict(range=[0,115],gridcolor=C["grid"]),yaxis_title="Utilisasi (%)")
                chart_card("Utilisasi per Kendaraan",fou)

    st.markdown("</div>", unsafe_allow_html=True)
