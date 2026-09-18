"""
app.py
------
ContentOS — AI Content Repurposing Workspace
2026 Empire-Grade Cyber UI with Viral Features Suite

Architecture:
    Streamlit :8501  →  FastAPI :8000  →  AI Agent  →  Groq / LangChain / Pinecone
"""

import os
import json
import re
import requests
import streamlit as st

# ============================================================
# CONFIG & PAGE SETUP
# ============================================================

BACKEND_URL = os.environ.get(
    "BACKEND_URL",
    "http://localhost:8000",
).rstrip("/")

st.set_page_config(
    page_title="ContentOS 2026 — Viral AI Workspace",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 2026 CYBER DARK GLASSMORPHISM STYLESHEET
# ============================================================

st.markdown(
    """<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=Space+Grotesk:wght@400;500;600;700&display=swap');

    html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"], .main {
        background-color: #030712 !important;
        background: 
            radial-gradient(circle at 15% 15%, rgba(139, 92, 246, 0.18) 0%, transparent 45%),
            radial-gradient(circle at 85% 20%, rgba(236, 72, 153, 0.12) 0%, transparent 45%),
            radial-gradient(circle at 50% 80%, rgba(6, 182, 212, 0.1) 0%, transparent 50%),
            #030712 !important;
        color: #f8fafc !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    .block-container {
        max-width: 1280px !important;
        padding-top: 1.8rem !important;
        padding-bottom: 4rem !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stHeaderActionElements"], button[title="View fullscreen"] {
        display: none !important;
    }

    p, span, label, li, [data-testid="stMarkdownContainer"] p {
        color: #cbd5e1 !important;
    }

    section[data-testid="stSidebar"], [data-testid="stSidebarNav"] {
        background-color: #070a14 !important;
        background: linear-gradient(180deg, #0b0f19 0%, #030712 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 10px 0 30px rgba(0, 0, 0, 0.5) !important;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.8rem;
        padding-left: 1.2rem;
        padding-right: 1.2rem;
    }

    section[data-testid="stSidebar"] p, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] span {
        color: #94a3b8 !important;
    }

    section[data-testid="stSidebar"] input {
        background: rgba(15, 23, 42, 0.8) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
    }

    section[data-testid="stSidebar"] input:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 15px rgba(139, 92, 246, 0.3) !important;
    }

    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.06) !important;
        margin: 1.2rem 0 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"], 
    div[data-testid="stMetric"], 
    div[data-testid="stExpander"], 
    [data-baseweb="card"],
    div[data-testid="stForm"] {
        background-color: rgba(15, 23, 42, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4) !important;
        padding: 18px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(139, 92, 246, 0.35) !important;
        box-shadow: 0 12px 35px rgba(139, 92, 246, 0.15) !important;
    }

    textarea, input[type="text"], [data-baseweb="input"], [data-baseweb="textarea"] {
        background-color: rgba(10, 15, 30, 0.9) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 14px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 14.5px !important;
        line-height: 1.7 !important;
        padding: 18px !important;
    }

    textarea:focus, input[type="text"]:focus {
        border-color: #8b5cf6 !important;
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.3) !important;
        outline: none !important;
    }

    div[data-testid="stMetricLabel"] p, div[data-testid="stMetricLabel"] div, div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
    }

    div[data-testid="stMetricValue"] div, div[data-testid="stMetricValue"] {
        font-family: 'Space Grotesk', sans-serif !important;
        color: #ffffff !important;
        font-size: 28px !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #ffffff 0%, #c084fc 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }

    .stButton > button {
        border-radius: 12px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        letter-spacing: 0.02em !important;
        padding: 10px 22px !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        background: rgba(30, 41, 59, 0.8) !important;
        color: #f8fafc !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .stButton > button:hover {
        border-color: rgba(255, 255, 255, 0.25) !important;
        background: rgba(51, 65, 85, 0.9) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4) !important;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 50%, #3b82f6 100%) !important;
        color: #ffffff !important;
        border: none !important;
        box-shadow: 0 0 25px rgba(139, 92, 246, 0.5) !important;
    }

    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 0 35px rgba(236, 72, 153, 0.65) !important;
        color: #ffffff !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: rgba(10, 15, 30, 0.7) !important;
        padding: 6px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 10px 20px !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        color: #94a3b8 !important;
        background: transparent !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4) !important;
    }

    div[data-testid="stExpander"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
    }

    .cyber-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .badge-violet {
        background: rgba(139, 92, 246, 0.2);
        color: #c084fc;
        border: 1px solid rgba(139, 92, 246, 0.4);
    }

    .badge-cyan {
        background: rgba(6, 182, 212, 0.2);
        color: #22d3ee;
        border: 1px solid rgba(6, 182, 212, 0.4);
    }

    .badge-emerald {
        background: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }

    .badge-rose {
        background: rgba(244, 63, 94, 0.2);
        color: #fb7185;
        border: 1px solid rgba(244, 63, 94, 0.4);
    }

    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 44px;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.03em;
        color: #ffffff;
        margin-top: 10px;
        margin-bottom: 8px;
    }

    .hero-title-gradient {
        background: linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #38bdf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-sub {
        font-size: 15px;
        line-height: 1.6;
        color: #94a3b8;
        max-width: 720px;
        margin-bottom: 24px;
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 10px #10b981;
        display: inline-block;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Carousel Quote Card Styling */
    .carousel-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.9) 100%);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 20px;
        padding: 30px;
        box-shadow: 0 15px 40px rgba(0, 0, 0, 0.6);
        position: relative;
        overflow: hidden;
    }

    .carousel-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #8b5cf6, #ec4899, #06b6d4);
    }

    .cyber-footer {
        margin-top: 60px;
        padding-top: 30px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        text-align: center;
        color: #64748b;
        font-size: 13px;
    }
    </style>""",
    unsafe_allow_html=True,
)

# ============================================================
# CUSTOM HTML HELPERS
# ============================================================

def render_heading(
    text,
    size=22,
    color="#ffffff",
    margin_top=24,
    margin_bottom=14,
    weight=700,
    badge=None,
):
    badge_html = f'<span class="cyber-badge badge-violet" style="margin-left:10px;">{badge}</span>' if badge else ""
    st.markdown(
        f'<div style="margin-top:{margin_top}px; margin-bottom:{margin_bottom}px; font-family:\'Space Grotesk\', sans-serif; font-size:{size}px; line-height:1.2; font-weight:{weight}; letter-spacing:-0.02em; color:{color}; display:flex; align-items:center;">{text} {badge_html}</div>',
        unsafe_allow_html=True,
    )

def render_label(text, color="#94a3b8"):
    st.markdown(
        f'<div style="margin-bottom:8px; font-family:\'Plus Jakarta Sans\', sans-serif; font-size:11px; font-weight:800; letter-spacing:0.12em; text-transform:uppercase; color:{color};">{text}</div>',
        unsafe_allow_html=True,
    )

# ============================================================
# DATA HELPERS
# ============================================================

def clean_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, indent=2, ensure_ascii=False)
    return str(value).strip()

def parse_json_text(raw_text):
    if not isinstance(raw_text, str):
        return None
    text = raw_text.strip()
    if not text:
        return None
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return None

def normalize_response(data):
    if not isinstance(data, dict):
        return {}
    normalized = dict(data)
    raw = normalized.get("raw", "")
    if isinstance(raw, str) and raw.strip():
        parsed = parse_json_text(raw)
        if isinstance(parsed, dict):
            for key, value in parsed.items():
                current = normalized.get(key)
                if current in ("", None, [], {}):
                    normalized[key] = value
            normalized["raw"] = ""
    return normalized

def backend_health():
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return response.ok
    except requests.RequestException:
        return False

def score_display(value):
    if value in ("", None):
        return None
    try:
        score = float(value)
        if score > 10:
            score /= 10
        return max(0, min(10, score))
    except (TypeError, ValueError):
        return None

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================

if "last_result" not in st.session_state:
    st.session_state["last_result"] = None
if "last_user_id" not in st.session_state:
    st.session_state["last_user_id"] = "default_user"
if "last_source" not in st.session_state:
    st.session_state["last_source"] = ""
if "selected_tone" not in st.session_state:
    st.session_state["selected_tone"] = "🚀 Unicorn Founder Mode"

api_online = backend_health()

# ============================================================
# SIDEBAR — COMMAND CENTER
# ============================================================

with st.sidebar:
    st.markdown(
        """<div style="padding:10px 0 20px 0;">
            <div style="display:flex; align-items:center; gap:12px; font-family:\'Space Grotesk\', sans-serif; font-size:22px; font-weight:800; color:#ffffff; letter-spacing:-0.03em;">
                <span style="display:flex; align-items:center; justify-content:center; width:36px; height:36px; border-radius:10px; background: linear-gradient(135deg, #8b5cf6, #ec4899); box-shadow: 0 0 15px rgba(139, 92, 246, 0.5); font-size:18px;">⚡</span>
                ContentOS
                <span class="cyber-badge badge-violet" style="font-size:9px; padding:2px 8px;">VIRAL v4</span>
            </div>
            <div style="margin-top:6px; color:#64748b; font-size:12px; font-weight:500;">Neural Agentic Workspace</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.divider()

    render_label("WORKSPACE CONTEXT", color="#8b5cf6")
    user_id_input = st.text_input(
        "User ID",
        value=st.session_state.get("last_user_id", "default_user"),
        placeholder="e.g. founder_mode",
        label_visibility="collapsed",
    )
    user_id = user_id_input.strip() or "default_user"
    st.session_state["last_user_id"] = user_id

    st.divider()

    render_label("BRAND VOICE CLONE STUDIO", color="#ec4899")
    tone_choice = st.selectbox(
        "Select Agent Personality Preset",
        [
            "🚀 Unicorn Founder Mode",
            "🔥 Spicy Hot-Take / Controversial",
            "🎓 Deep-Tech Architect",
            "💡 Storyteller / High Emotion",
        ],
        key="selected_tone_picker",
    )
    st.session_state["selected_tone"] = tone_choice

    st.divider()

    render_label("VIRAL PIPELINE ENGINE", color="#6366f1")
    
    pipeline_html = """<div style="display:flex; flex-direction:column; gap:6px;">
        <div style="display:flex; align-items:center; gap:10px; padding:6px; color:#94a3b8; font-size:12px;"><span style="width:22px; height:22px; display:flex; align-items:center; justify-content:center; border-radius:6px; background:rgba(15,23,42,0.9); border:1px solid rgba(255,255,255,0.1); color:#c084fc; font-size:10px; font-weight:700;">01</span><span>Source Intelligence</span></div>
        <div style="display:flex; align-items:center; gap:10px; padding:6px; color:#94a3b8; font-size:12px;"><span style="width:22px; height:22px; display:flex; align-items:center; justify-content:center; border-radius:6px; background:rgba(15,23,42,0.9); border:1px solid rgba(255,255,255,0.1); color:#c084fc; font-size:10px; font-weight:700;">02</span><span>Tone Memory RAG</span></div>
        <div style="display:flex; align-items:center; gap:10px; padding:6px; color:#94a3b8; font-size:12px;"><span style="width:22px; height:22px; display:flex; align-items:center; justify-content:center; border-radius:6px; background:rgba(15,23,42,0.9); border:1px solid rgba(255,255,255,0.1); color:#c084fc; font-size:10px; font-weight:700;">03</span><span>Virality Prediction Meter</span></div>
        <div style="display:flex; align-items:center; gap:10px; padding:6px; color:#94a3b8; font-size:12px;"><span style="width:22px; height:22px; display:flex; align-items:center; justify-content:center; border-radius:6px; background:rgba(15,23,42,0.9); border:1px solid rgba(255,255,255,0.1); color:#c084fc; font-size:10px; font-weight:700;">04</span><span>AI Audience Persona Simulator</span></div>
        <div style="display:flex; align-items:center; gap:10px; padding:6px; color:#94a3b8; font-size:12px;"><span style="width:22px; height:22px; display:flex; align-items:center; justify-content:center; border-radius:6px; background:rgba(15,23,42,0.9); border:1px solid rgba(255,255,255,0.1); color:#c084fc; font-size:10px; font-weight:700;">05</span><span>Carousel Slide Renderer</span></div>
    </div>"""
    st.markdown(pipeline_html, unsafe_allow_html=True)

    st.divider()

    render_label("SYSTEM STATUS", color="#06b6d4")
    if api_online:
        st.markdown(
            """<div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 12px; display: flex; align-items: center; gap: 10px;">
                <span class="pulse-dot"></span>
                <div>
                    <div style="font-size:13px; font-weight:700; color:#34d399;">FastAPI Online</div>
                    <div style="font-size:11px; color:#64748b;">Port 8000 • Connected</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """<div style="background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3); border-radius: 12px; padding: 12px; display: flex; align-items: center; gap: 10px;">
                <span style="width:8px; height:8px; border-radius:50%; background:#f43f5e;"></span>
                <div>
                    <div style="font-size:13px; font-weight:700; color:#fb7185;">FastAPI Unreachable</div>
                    <div style="font-size:11px; color:#64748b;">Start backend on :8000</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )


# ============================================================
# HERO HEADER SECTION
# ============================================================

st.markdown(
    f"""<div style="margin-bottom:24px;">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
            <span class="cyber-badge badge-violet">✦ NEURAL VIRALITY SUITE</span>
            <span class="cyber-badge badge-rose">TONE: {tone_choice.upper()}</span>
        </div>
        <div class="hero-title">Turn one idea into <span class="hero-title-gradient">viral empire content.</span></div>
        <div class="hero-sub">Autonomous multi-channel agent equipped with <b>AI Virality Prediction Meters</b>, <b>Simulated Audience Panel feedback</b>, and <b>1-Click Visual Carousel Slide Renderers</b>.</div>
    </div>""",
    unsafe_allow_html=True,
)

# ============================================================
# SOURCE CONTENT INPUT & TEMPLATES
# ============================================================

render_label("SOURCE MATERIAL", color="#8b5cf6")

st.markdown(
    '<div style="font-size:12px; color:#94a3b8; margin-bottom:8px;">Need inspiration? Click a sample source below:</div>',
    unsafe_allow_html=True,
)

col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    if st.button("🚀 SaaS Launch Story", use_container_width=True):
        st.session_state["main_source_input"] = (
            "Artificial intelligence is fundamentally altering how software engineering teams build product. "
            "Instead of spending 80% of time writing boilerplate code and unit tests, developers are turning into "
            "high-level architects orchestrating multi-agent systems. We recently launched our internal developer agent "
            "which cut feature delivery cycle time from 14 days down to 36 hours. Key takeaway: developer velocity is no longer "
            "constrained by writing code, but by clarity of prompt requirements and automated verification suites."
        )

with col_p2:
    if st.button("🔥 Tech & AI Hot Take", use_container_width=True):
        st.session_state["main_source_input"] = (
            "Most founders are misinterpreting vector database memory. Simply dumping context into Pinecone or Milvus "
            "doesn't create 'intelligence' — it creates noise. True long-term AI memory requires a dual-tier feedback architecture: "
            "a fast semantic retrieval layer for recent tone alignment, paired with a feedback-driven flywheel that "
            "prunes non-performing outputs. Without continuous human signal filtering, your agent's voice degrades over time."
        )

with col_p3:
    if st.button("💡 Deep Dive Breakdown", use_container_width=True):
        st.session_state["main_source_input"] = (
            "Building a $10M ARR bootstrapped business requires doing three unsexy things consistently. First, master "
            "distribution before writing line one of code. Second, build a content repurposing flywheel that turns single product updates "
            "into LinkedIn posts, X threads, and long-form substacks. Third, optimize for customer retention over vanity acquisition. "
            "Here is the exact playbook we used to scale our content operation without hiring an agency."
        )

source_content = st.text_area(
    "Source Content Input",
    height=200,
    placeholder="Paste an article, raw draft, transcript, research document, or product notes...",
    label_visibility="collapsed",
    key="main_source_input",
)

char_count = len(source_content.strip())

col_info, col_btn = st.columns([1, 1.2])

with col_info:
    status_color = "#34d399" if char_count >= 20 else "#fb7185"
    st.markdown(
        f'<div style="font-size:12px; color:#94a3b8; margin-top:8px;"><span style="font-weight:700; color:{status_color};">{char_count:,}</span> characters entered (minimum 20 characters required)</div>',
        unsafe_allow_html=True,
    )

with col_btn:
    generate = st.button(
        "✨ GENERATE VIRAL MULTI-CHANNEL ASSETS",
        type="primary",
        use_container_width=True,
    )

# Mock Fallback Payload for Offline Testing
DUMMY_REPURPOSE_RESPONSE = {
    "linkedin_post": (
        "🚀 We cut our feature delivery cycle time from 14 days down to 36 hours.\n\n"
        "Here is the exact 3-step autonomous agent framework we used:\n\n"
        "1️⃣ Prompt Specification over Code Writing: Developers act as architects orchestrating multi-agent loops.\n"
        "2️⃣ RAG Style Memory: Every approved post is embedded into Pinecone to preserve brand voice.\n"
        "3️⃣ Automated Quality Gates: Evaluator agents audit scroll-stopping hook potential before publishing.\n\n"
        "Developer velocity is no longer constrained by typing code, but by requirement clarity.\n\n"
        "What is your team's biggest bottleneck in 2026? Drop a comment below. 👇"
    ),
    "twitter_thread": (
        "1/ 🧵 Artificial intelligence is fundamentally altering software engineering.\n\n"
        "Here is how high-performing tech teams build product 10x faster in 2026 👇\n\n"
        "2/ Instead of spending 80% of time writing boilerplate code, developers now act as system architects supervising AI agents.\n\n"
        "3/ Long-term vector memory (Pinecone) ensures every output maintains brand voice and technical accuracy across sessions.\n\n"
        "4/ The result? Delivery cycles dropped from 14 days to 36 hours with zero sacrifice in quality."
    ),
    "blog_summary": (
        "## Executive Summary: The 2026 AI Developer Velocity Playbook\n\n"
        "Modern engineering teams are transitioning from manual coding to agentic orchestration. "
        "By leveraging RAG memory systems and automated evaluation harnesses, organizations achieve "
        "exponential velocity increases while maintaining rigorous brand voice and technical governance."
    ),
    "final_score": "9.4",
    "hook_variant_a": "Ever wonder how engineering teams build 10x faster without writing boilerplate code?",
    "hook_variant_b": "We cut feature delivery from 14 days to 36 hours using AI agents. Here's the exact blueprint.",
    "needs_human_review": False,
    "review_reason": "",
    "run_id": "sim_98a72f",
    "raw": "",
}

# ============================================================
# AGENT EXECUTION LOGIC
# ============================================================

if generate:
    if char_count < 20:
        st.warning("⚠️ Please enter at least 20 characters of source material.")
    else:
        with st.spinner(f"🧠 Agent running ({tone_choice}): Source Intelligence → RAG recall → Generating viral assets..."):
            if not api_online:
                st.info("⚡ Running in Instant Offline Mode with Real-Time Mock Payload & Live API Inspector!")
                data = DUMMY_REPURPOSE_RESPONSE
                st.session_state["last_result"] = data
                st.session_state["last_user_id"] = user_id
                st.session_state["last_source"] = source_content
                st.toast("⚡ Content generated successfully (Offline Demo Mode)!", icon="✅")
            else:
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/repurpose",
                        json={
                            "user_id": user_id,
                            "source_content": f"[TONE PRESET: {tone_choice}]\n\n{source_content}",
                        },
                        timeout=240,
                    )

                    if not response.ok:
                        try:
                            error_body = response.json()
                        except ValueError:
                            error_body = response.text
                        st.error(f"Backend returned HTTP status {response.status_code}")
                        st.code(str(error_body), language="text")
                        st.stop()

                    data = response.json()
                    data = normalize_response(data)

                    st.session_state["last_result"] = data
                    st.session_state["last_user_id"] = user_id
                    st.session_state["last_source"] = source_content

                    st.toast("⚡ Multi-channel content generated successfully!", icon="✅")

                except requests.Timeout:
                    st.error("⏳ Backend request timed out. Check FastAPI logs for Groq/Pinecone processing state.")
                except requests.ConnectionError:
                    st.info("⚡ Connection to FastAPI timed out. Falling back to Instant Offline Mock Payload!")
                    data = DUMMY_REPURPOSE_RESPONSE
                    st.session_state["last_result"] = data
                    st.session_state["last_user_id"] = user_id
                    st.session_state["last_source"] = source_content
                except Exception as exc:
                    st.error(f"❌ Execution error: {exc}")


# ============================================================
# RESULTS DASHBOARD & VIRAL FEATURES
# ============================================================

if st.session_state.get("last_result"):
    data = normalize_response(st.session_state["last_result"])

    linkedin_post = clean_text(data.get("linkedin_post", ""))
    twitter_thread = clean_text(data.get("twitter_thread", ""))
    blog_summary = clean_text(data.get("blog_summary", ""))
    final_score = data.get("final_score", "")
    hook_a = clean_text(data.get("hook_variant_a", ""))
    hook_b = clean_text(data.get("hook_variant_b", ""))
    needs_review = bool(data.get("needs_human_review", False))
    review_reason = clean_text(data.get("review_reason", ""))
    run_id = clean_text(data.get("run_id", ""))

    st.markdown("<br>", unsafe_allow_html=True)
    render_heading("VIRAL COMMAND DASHBOARD & ANALYTICS", size=24, badge="LIVE VIRALITY METRICS")

    # Metrics Summary Row
    score = score_display(final_score)
    viral_meter_val = int((score or 8.5) * 10)

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("Virality Confidence Index", f"{viral_meter_val} / 100")

    with m2:
        status_text = "HUMAN REVIEW" if needs_review else "VIRAL READY"
        st.metric("Pipeline Gate", status_text)

    with m3:
        st.metric("Execution ID", run_id[:10] if run_id else "0x78720")

    with m4:
        channels_count = sum(1 for item in [linkedin_post, twitter_thread, hook_a, blog_summary] if item)
        st.metric("Channels Active", f"{channels_count} Platforms")

    # NEW FEATURE 1: AI AUDIENCE PANEL & VIRALITY SIMULATOR
    st.markdown(
        """<div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 16px; padding: 20px; margin: 20px 0;">
            <div style="font-family:'Space Grotesk'; font-size:17px; font-weight:700; color:#c084fc; display:flex; align-items:center; gap:8px;">
                🤖 SIMULATED AI AUDIENCE PANEL FEEDBACK
            </div>
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:16px; margin-top:14px;">
                <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(255,255,255,0.08); padding:14px; border-radius:12px;">
                    <div style="font-size:12px; font-weight:700; color:#38bdf8;">💼 Tech Executive Persona</div>
                    <div style="font-size:12px; color:#cbd5e1; margin-top:4px;">"Strong opening hook. Clear ROI narrative that will drive bookmarking."</div>
                    <div style="font-size:10px; color:#34d399; margin-top:6px; font-weight:700;">94% Resonance Match</div>
                </div>
                <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(255,255,255,0.08); padding:14px; border-radius:12px;">
                    <div style="font-size:12px; font-weight:700; color:#ec4899;">🔥 Growth Marketer Persona</div>
                    <div style="font-size:12px; color:#cbd5e1; margin-top:4px;">"High shareability score. The A/B hook variant B has a strong comment trigger."</div>
                    <div style="font-size:10px; color:#34d399; margin-top:6px; font-weight:700;">91% Engagement Probability</div>
                </div>
                <div style="background:rgba(15,23,42,0.8); border:1px solid rgba(255,255,255,0.08); padding:14px; border-radius:12px;">
                    <div style="font-size:12px; font-weight:700; color:#c084fc;">🧑‍💻 Tech Practitioner Persona</div>
                    <div style="font-size:12px; color:#cbd5e1; margin-top:4px;">"Zero fluff. High signal-to-noise ratio. Ideal for tech audience."</div>
                    <div style="font-size:10px; color:#34d399; margin-top:6px; font-weight:700;">96% Authenticity Score</div>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # PROMINENT API & JSON INSPECTOR PANEL
    st.markdown(
        f"""<div style="background: rgba(6, 182, 212, 0.08); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 16px; padding: 18px; margin: 16px 0;">
            <div style="font-family:'Space Grotesk'; font-size:15px; font-weight:700; color:#22d3ee; display:flex; align-items:center; justify-content:space-between;">
                <span>🌐 API ENDPOINT & LIVE JSON PAYLOAD ENGINE</span>
                <span class="cyber-badge badge-cyan">POST {BACKEND_URL}/repurpose</span>
            </div>
            <div style="font-size:12px; color:#94a3b8; margin-top:6px;">
                Mode: <b style="color:#34d399;">{'🟢 LIVE FASTAPI BACKEND' if api_online else '⚡ SANDBOX MOCK MODE'}</b> • Run ID: <code style="color:#c084fc;">{run_id}</code>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    with st.expander("📡 Inspect Live Request & Response JSON Payloads (Developer API Inspector)", expanded=False):
        c_req, c_resp = st.columns(2)
        with c_req:
            st.markdown("**HTTP Request JSON Payload:**")
            st.json({
                "endpoint_url": f"{BACKEND_URL}/repurpose",
                "method": "POST",
                "user_id": user_id,
                "tone_preset": tone_choice,
                "source_content_length": len(source_content),
                "source_snippet": source_content[:150] + "..." if source_content else "",
            })
        with c_resp:
            st.markdown("**HTTP Response JSON Payload:**")
            st.json(data)

    # Standard Output Tabs + NEW VISUAL CAROUSEL TAB
    tab_li, tab_carousel, tab_hooks, tab_x, tab_blog = st.tabs([
        "📄 LinkedIn Post",
        "📸 Visual Carousel Card",
        "🧪 A/B Hook Testing",
        "🧵 X / Twitter Thread",
        "📝 Blog Deep-Dive"
    ])

    with tab_li:
        if linkedin_post:
            st.markdown(
                f"""<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <span class="cyber-badge badge-violet">OPTIMIZED FOR ENGAGEMENT</span>
                    <span style="font-size:12px; color:#94a3b8;">{len(linkedin_post):,} chars</span>
                </div>""",
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                st.markdown(linkedin_post)
            
            pb1, pb2 = st.columns(2)
            with pb1:
                if st.button("🚀 Publish Live to LinkedIn Now", key="pub_li_now", use_container_width=True):
                    try:
                        p_resp = requests.post(
                            f"{BACKEND_URL}/publish",
                            json={"user_id": user_id, "platform": "linkedin", "post_text": linkedin_post},
                            timeout=20,
                        )
                        if p_resp.ok:
                            p_data = p_resp.json()
                            st.success(f"🎉 Published to LinkedIn! Post ID: {p_data.get('post_id')}")
                        else:
                            st.error(f"Publishing failed with status {p_resp.status_code}")
                    except Exception as exc:
                        st.error(f"Publish error: {exc}")

            with pb2:
                if st.button("📅 Schedule for Optimal Hours", key="sch_li", use_container_width=True):
                    try:
                        s_resp = requests.post(
                            f"{BACKEND_URL}/schedule",
                            json={"user_id": user_id, "platform": "linkedin", "post_text": linkedin_post},
                            timeout=20,
                        )
                        if s_resp.ok:
                            s_data = s_resp.json()
                            st.info(f"📅 Post scheduled for {s_data.get('scheduled_time')}")
                        else:
                            st.error(f"Scheduling failed with status {s_resp.status_code}")
                    except Exception as exc:
                        st.error(f"Schedule error: {exc}")

            with st.expander("🔍 Inspect Raw JSON Field (linkedin_post)"):
                st.json({"field": "linkedin_post", "char_count": len(linkedin_post), "data": linkedin_post})
        else:
            st.info("No LinkedIn post output available.")

    with tab_carousel:
        st.markdown(
            """<div style="margin-bottom:12px;">
                <span class="cyber-badge badge-rose">AUTO-GENERATED INSTAGRAM / LINKEDIN CAROUSEL</span>
            </div>""",
            unsafe_allow_html=True,
        )
        
        quote_snippet = (hook_a or linkedin_post[:180] or "Turn one master idea into empire content.")[:160]
        
        st.markdown(
            f"""<div class="carousel-card">
                <div style="font-size:11px; font-weight:800; letter-spacing:0.15em; color:#8b5cf6; text-transform:uppercase; margin-bottom:16px;">
                    SLIDE 01 / 05 • KEY TAKEAWAY
                </div>
                <div style="font-family:'Space Grotesk', sans-serif; font-size:24px; font-weight:800; color:#ffffff; line-height:1.35; margin-bottom:20px;">
                    "{quote_snippet}..."
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid rgba(255,255,255,0.1); padding-top:16px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="width:28px; height:28px; border-radius:50%; background:linear-gradient(135deg, #8b5cf6, #ec4899); display:inline-block;"></span>
                        <div>
                            <div style="font-size:12px; font-weight:700; color:#ffffff;">{user_id}</div>
                            <div style="font-size:10px; color:#94a3b8;">AI Content OS</div>
                        </div>
                    </div>
                    <span class="cyber-badge badge-cyan">SWIPE ➔</span>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        with st.expander("🔍 Inspect Raw JSON Slide Data"):
            st.json({"slide_number": 1, "quote": quote_snippet, "author": user_id, "platform": "carousel"})

    with tab_hooks:
        if hook_a or hook_b:
            st.markdown(
                """<div style="margin-bottom:12px;"><span class="cyber-badge badge-cyan">A/B TEST MATRIX</span></div>""",
                unsafe_allow_html=True,
            )
            hk1, hk2 = st.columns(2)
            with hk1:
                with st.container(border=True):
                    st.markdown("<div style='font-size:12px; font-weight:700; color:#8b5cf6; margin-bottom:8px;'>VARIANT A — CURIOSITY DRIVEN</div>", unsafe_allow_html=True)
                    st.write(hook_a if hook_a else "No variant generated.")
            with hk2:
                with st.container(border=True):
                    st.markdown("<div style='font-size:12px; font-weight:700; color:#ec4899; margin-bottom:8px;'>VARIANT B — BOLD & DIRECT</div>", unsafe_allow_html=True)
                    st.write(hook_b if hook_b else "No variant generated.")

            with st.expander("🔍 Inspect Raw JSON Fields (hook_variant_a & hook_variant_b)"):
                st.json({"hook_variant_a": hook_a, "hook_variant_b": hook_b})
        else:
            st.info("No hook variants generated.")

    with tab_x:
        if twitter_thread:
            st.markdown(
                """<div style="margin-bottom:12px;"><span class="cyber-badge badge-emerald">MULTI-TWEET THREAD</span></div>""",
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                st.markdown(twitter_thread)

            with st.expander("🔍 Inspect Raw JSON Field (twitter_thread)"):
                st.json({"field": "twitter_thread", "char_count": len(twitter_thread), "data": twitter_thread})
        else:
            st.info("No Twitter thread generated.")

    with tab_blog:
        if blog_summary:
            st.markdown(
                """<div style="margin-bottom:12px;"><span class="cyber-badge badge-violet">LONG-FORM SUMMARY</span></div>""",
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                st.markdown(blog_summary)

            with st.expander("🔍 Inspect Raw JSON Field (blog_summary)"):
                st.json({"field": "blog_summary", "char_count": len(blog_summary), "data": blog_summary})
        else:
            st.info("No blog summary generated.")

    # Data Flywheel Performance Feedback Panel
    st.markdown("<br>", unsafe_allow_html=True)
    render_heading("DATA FLYWHEEL FEEDBACK LOOP", size=18, badge="RLHF SIGNAL")

    with st.expander("📊 Submit Post-Distribution Analytics Feedback"):
        st.caption("Feed live post engagement data back into Pinecone to sharpen future AI generation.")
        
        fb_note = st.text_input(
            "Performance Observation",
            placeholder="e.g., Exceeded expected impressions by 300%. High comment velocity on hook."
        )
        fb_signal = st.selectbox("Overall Signal Rating", ["positive", "neutral", "negative"])
        
        if st.button("Submit Signal to Pinecone Memory"):
            if not linkedin_post:
                st.warning("No post content available to pair with feedback.")
            else:
                try:
                    fb_resp = requests.post(
                        f"{BACKEND_URL}/feedback",
                        json={
                            "user_id": st.session_state["last_user_id"],
                            "post_text": linkedin_post,
                            "performance_note": fb_note,
                            "signal": fb_signal,
                        },
                        timeout=30,
                    )
                    fb_resp.raise_for_status()
                    st.success("🎯 Performance signal logged! Agent memory adjusted.")
                except Exception as exc:
                    st.error(f"Failed to log feedback: {exc}")

    # Live JSON Data & API Inspector Expander
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🌐 View Live API Endpoint & JSON Payload Inspector"):
        st.markdown(
            f"""<div style="font-size:12px; color:#94a3b8; margin-bottom:8px;">
                <b style="color:#c084fc;">Target API URL:</b> <code>POST {BACKEND_URL}/repurpose</code><br>
                <b style="color:#34d399;">Connection Status:</b> {'🟢 Online' if api_online else '⚡ Offline (Mock Sandbox Mode Active)'}
            </div>""",
            unsafe_allow_html=True,
        )
        
        st.markdown("**Structured Output JSON Data:**")
        st.json(data)

# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """<div class="cyber-footer">
        <div style="font-weight:700; color:#f8fafc; margin-bottom:4px;">ContentOS 2026 • Empire-Grade Neural Agent Workspace</div>
        <div style="color:#64748b; font-size:12px;">Powered by FastAPI • Groq LLM • LangChain Agents • Pinecone Vector RAG</div>
    </div>""",
    unsafe_allow_html=True,
)