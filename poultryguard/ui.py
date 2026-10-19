"""Bespoke UI theming for PoultryGuard — light/dark themes, RTL (Arabic) support,
and a translated header. Hides the default Streamlit chrome so the app does not
read as a stock Streamlit template.
"""
from __future__ import annotations
import streamlit as st

# ------------------------------------------------------------------ base CSS
_BASE = """
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Inter:wght@400;500;600&family=Cairo:wght@400;600;700&display=swap');

:root{
  --brand:#1f9d61; --brand-2:#13784a; --brand-ink:#0c3d27;
  --ink:#15241c; --muted:#5f7067; --line:#e2e7e1;
  --bg:#eef1ec; --card:#ffffff; --accent:#f59e0b; --danger:#e11d48; --ok:#1f9d61;
  --app-grad: radial-gradient(1200px 400px at 80% -10%, #dff0e6 0%, rgba(223,240,230,0) 60%);
}

#MainMenu, footer, header[data-testid="stHeader"]{display:none !important;}
[data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"]{display:none !important;}
.stDeployButton, [data-testid="stAppDeployButton"]{display:none !important;}

html, body, [class*="css"], .stApp{font-family:'Inter',system-ui,sans-serif; color:var(--ink);}
.stApp{background:var(--app-grad), var(--bg);}
h1,h2,h3,h4{font-family:'Sora','Inter',sans-serif; letter-spacing:-.01em; color:var(--ink);}
.block-container{padding-top:1.0rem; padding-bottom:3rem; max-width:1340px;}

.pg-header{display:flex; align-items:center; gap:.9rem;
  background:linear-gradient(100deg,var(--brand-2) 0%, var(--brand) 55%, #27b473 100%);
  color:#fff; padding:16px 22px; border-radius:16px; margin-bottom:14px;
  box-shadow:0 10px 30px -12px rgba(19,120,74,.55);}
.pg-badge{font-size:26px; line-height:1; background:rgba(255,255,255,.16);
  width:46px; height:46px; display:flex; align-items:center; justify-content:center; border-radius:12px;}
.pg-title{font-family:'Sora',sans-serif; font-weight:700; font-size:1.28rem; margin:0; color:#fff;}
.pg-sub{font-size:.82rem; opacity:.9; margin:0; color:#fff;}
.pg-spacer{flex:1}
.pg-pill{background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.28);
  padding:5px 12px; border-radius:999px; font-size:.76rem; font-weight:600;}

[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f2e20 0%, #123a28 100%); border-right:1px solid #0b241a;}
[data-testid="stSidebar"] *{color:#e8f2ec !important;}
[data-testid="stSidebar"] label{color:#bcd6c8 !important; font-weight:500;}
/* inputs in the (dark) sidebar keep a light field + dark text so values are readable */
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="select"] div[role="button"]{color:#15241c !important;}
[data-testid="stSidebar"] input::placeholder{color:#6b7a72 !important;}
[data-testid="stSidebar"] [data-testid="stExpander"]{border:1px solid rgba(255,255,255,.08);
  border-radius:12px; background:rgba(255,255,255,.03);}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.12);}

.stTabs [data-baseweb="tab-list"]{gap:6px; background:var(--card); padding:6px;
  border-radius:14px; border:1px solid var(--line); box-shadow:0 1px 2px rgba(0,0,0,.03); flex-wrap:wrap;}
.stTabs [data-baseweb="tab"]{height:40px; border-radius:10px; padding:0 14px; font-weight:600; color:var(--muted); background:transparent;}
.stTabs [aria-selected="true"]{background:linear-gradient(100deg,var(--brand-2),var(--brand)) !important; color:#fff !important;}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{display:none;}

[data-testid="stMetric"]{background:var(--card); border:1px solid var(--line);
  padding:14px 16px; border-radius:14px; box-shadow:0 1px 2px rgba(0,0,0,.04);}
[data-testid="stMetricValue"]{font-family:'Sora',sans-serif; color:var(--brand-2);}
[data-testid="stMetricLabel"]{color:var(--muted); font-weight:600;}
[data-testid="stDataFrame"]{border:1px solid var(--line); border-radius:12px; overflow:hidden;}

.stButton>button{border-radius:10px; font-weight:600; border:1px solid var(--line);
  transition:transform .05s ease, box-shadow .2s ease; background:var(--card); color:var(--ink);}
.stButton>button:hover{transform:translateY(-1px); box-shadow:0 6px 16px -8px rgba(0,0,0,.35);}
[data-testid="stSidebar"] .stButton>button{background:var(--brand); color:#fff !important; border:none;}
[data-testid="stSidebar"] .stButton>button:hover{background:#25b06f;}

.pg-card{background:var(--card); border:1px solid var(--line); border-radius:16px;
  padding:18px 20px; box-shadow:0 1px 2px rgba(0,0,0,.04);}
.pg-chip{display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border-radius:999px; font-size:.75rem; font-weight:600;}
.pg-chip.ok{background:#e7f6ee; color:#13784a;} .pg-chip.warn{background:#fdf0dc; color:#b06a06;} .pg-chip.bad{background:#fde7ec; color:#b11236;}
.pg-caption{color:var(--muted); font-size:.85rem;}
.stAlert{border-radius:12px;}

/* login */
.pg-login{max-width:430px; margin:4vh auto 0; }
.pg-login .pg-card{padding:26px 28px;}
.pg-login-brand{display:flex; align-items:center; gap:12px; margin-bottom:6px;}
.pg-login-brand .pg-badge{background:var(--brand); color:#fff;}
.pg-demo{font-size:.78rem; color:var(--muted); background:rgba(31,157,97,.07);
  border:1px dashed rgba(31,157,97,.4); border-radius:10px; padding:8px 12px; margin-top:6px;}
"""

# ------------------------------------------------------------------ dark theme
_DARK = """
:root{
  --ink:#e9f1ec; --muted:#9db3a8; --line:#243a30;
  --bg:#0e1712; --card:#16241d;
  --app-grad: radial-gradient(1200px 400px at 80% -10%, #16352479 0%, rgba(14,23,18,0) 60%);
}
.stApp, .stApp p, .stApp li, .stApp span, .stApp label, .stApp h1,.stApp h2,.stApp h3,.stApp h4{color:var(--ink);}
.stTextInput input, .stNumberInput input, .stTextArea textarea,
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"]>div{
  background:#13201a !important; color:#e9f1ec !important; border-color:#243a30 !important;}
.stButton>button{background:var(--card); color:var(--ink);}
[data-testid="stMetricValue"]{color:#39c483;}
.pg-chip.ok{background:#12301f; color:#49c98a;} .pg-chip.warn{background:#352610; color:#e0a94c;}
.pg-chip.bad{background:#3a1420; color:#f0748f;}
.pg-demo{background:#13231b; color:#9db3a8;}
"""

# ------------------------------------------------------------------ RTL (Arabic)
_RTL = """
.stApp, [data-testid="stSidebar"]{direction:rtl;}
html, body, [class*="css"], .stApp, [data-testid="stSidebar"] *{font-family:'Cairo','Inter',sans-serif;}
.pg-header{direction:rtl;} .block-container{text-align:right;}
[data-testid="stSidebar"] label, .stApp p, .stApp label{text-align:right;}
.stTabs [data-baseweb="tab-list"]{direction:rtl;}
"""


def inject(theme: str = "light", lang: str = "en"):
    css = _BASE
    if theme == "dark":
        css += _DARK
    if lang == "ar":
        css += _RTL
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def header(detector_label: str, farm: str, house: str, age: int, t):
    st.markdown(f"""
<div class="pg-header">
  <div class="pg-badge">🐔</div>
  <div>
    <p class="pg-title">{t('app_title')}</p>
    <p class="pg-sub">{t('app_sub')}</p>
  </div>
  <div class="pg-spacer"></div>
  <div class="pg-pill">🎥 {detector_label}</div>
  <div class="pg-pill">🏠 {farm} / {house}</div>
  <div class="pg-pill">📅 {age} {('يوم' if t('language')=='اللغة' else 'd')}</div>
</div>
""", unsafe_allow_html=True)


def chip(text: str, kind: str = "ok") -> str:
    return f'<span class="pg-chip {kind}">{text}</span>'
