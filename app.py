import streamlit as st
import json
import re
from pathlib import Path

st.set_page_config(
    page_title="MA EMS Protocols",
    page_icon="🚑",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- Apple-inspired CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Global reset */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    font-size: 16px;
    color: #1d1d1f;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}
div[data-testid="stToolbar"] {display: none;}

/* Main container spacing */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 720px !important;
}

/* App title */
.app-title {
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 0;
    color: #1d1d1f;
}
.app-subtitle {
    font-size: 0.85rem;
    color: #86868b;
    font-weight: 500;
    margin-top: 2px;
    margin-bottom: 16px;
}

/* Level selector pills */
.level-selector {
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    flex-wrap: wrap;
}
.level-pill {
    padding: 8px 20px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    border: 2px solid #e5e5ea;
    background: white;
    color: #1d1d1f;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
}
.level-pill:hover { border-color: #d1d1d6; background: #f5f5f7; }
.level-pill.active { 
    background: #d9534f; border-color: #d9534f; color: white; 
}

/* Search input */
div[data-testid="stTextInput"] input {
    font-size: 1rem !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    padding: 12px 16px !important;
    border-radius: 12px !important;
    border: 1.5px solid #e5e5ea !important;
    background: #f5f5f7 !important;
    transition: all 0.2s;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #d9534f !important;
    background: white !important;
    box-shadow: 0 0 0 3px rgba(217,83,79,0.12) !important;
}
div[data-testid="stTextInput"] label { display: none !important; }

/* Section headers */
.section-header {
    font-size: 0.75rem;
    font-weight: 700;
    color: #86868b;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding: 20px 0 8px 4px;
}

/* Protocol cards */
.proto-card {
    padding: 14px 16px;
    margin: 0 0 1px 0;
    background: white;
    border-bottom: 1px solid #f0f0f0;
    cursor: pointer;
    transition: background 0.15s;
}
.proto-card:hover { background: #f5f5f7; }
.proto-card:first-child { border-radius: 12px 12px 0 0; }
.proto-card:last-child { border-radius: 0 0 12px 12px; border-bottom: none; }
.proto-card-wrapper {
    background: white;
    border-radius: 12px;
    border: 1px solid #e5e5ea;
    overflow: hidden;
    margin-bottom: 8px;
}
.proto-id-badge {
    font-weight: 700;
    color: #d9534f;
    font-size: 0.85rem;
    margin-right: 8px;
    min-width: 36px;
    display: inline-block;
}
.proto-title-text {
    font-weight: 500;
    font-size: 0.95rem;
    color: #1d1d1f;
}
.proto-arrow {
    float: right;
    color: #c7c7cc;
    font-size: 1rem;
}

/* Provider level badges */
.lvl-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 700;
    margin-right: 4px;
    letter-spacing: 0.3px;
}
.lvl-FR { background: #007aff; color: white; }
.lvl-E { background: #f0ad4e; color: #1d1d1f; }
.lvl-A { background: #34c759; color: white; }
.lvl-P { background: #d9534f; color: white; }

/* Detail view */
.detail-header {
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: -0.3px;
    color: #1d1d1f;
    margin-bottom: 4px;
    line-height: 1.3;
}
.detail-badges {
    margin-bottom: 16px;
}

/* Protocol content */
.protocol-body {
    font-size: 0.95rem;
    line-height: 1.75;
    color: #1d1d1f;
}
.protocol-body .section-title {
    font-weight: 700;
    font-size: 1rem;
    color: #1d1d1f;
    margin-top: 20px;
    margin-bottom: 8px;
    padding-bottom: 4px;
    border-bottom: 2px solid #d9534f;
    display: inline-block;
}
.protocol-body .bullet {
    padding-left: 20px;
    margin: 6px 0;
    position: relative;
}
.protocol-body .bullet::before {
    content: "•";
    position: absolute;
    left: 4px;
    color: #d9534f;
    font-weight: 700;
}
.protocol-body .sub-bullet {
    padding-left: 40px;
    margin: 4px 0;
    position: relative;
    color: #424245;
}
.protocol-body .sub-bullet::before {
    content: "–";
    position: absolute;
    left: 24px;
    color: #86868b;
}
.protocol-body .note-block {
    background: #f5f5f7;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 12px 0;
    font-size: 0.9rem;
    color: #424245;
}
.protocol-body .caution-block {
    background: #fff3cd;
    border-left: 4px solid #d9534f;
    border-radius: 0 10px 10px 0;
    padding: 12px 16px;
    margin: 12px 0;
    font-weight: 600;
    color: #856404;
}
.protocol-body .standing-orders {
    font-weight: 700;
    font-size: 0.95rem;
    color: white;
    background: #424245;
    padding: 8px 14px;
    border-radius: 8px;
    margin: 16px 0 8px 0;
    display: inline-block;
}
.protocol-body .standing-orders.emt { background: #f0ad4e; color: #1d1d1f; }
.protocol-body .standing-orders.aemt { background: #34c759; }
.protocol-body .standing-orders.paramedic { background: #d9534f; }
.protocol-body .standing-orders.fr { background: #007aff; }
.protocol-body .standing-orders.mc { background: #6e6e73; }
.protocol-body .plain {
    margin: 6px 0;
}

/* Back button */
.back-link {
    font-size: 0.9rem;
    font-weight: 600;
    color: #d9534f;
    cursor: pointer;
    padding: 8px 0;
    display: inline-block;
    margin-bottom: 8px;
}

/* Streamlit button overrides */
div[data-testid="stButton"] button {
    text-align: left !important;
    border: none !important;
    background: none !important;
    padding: 10px 16px !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: #1d1d1f !important;
    border-radius: 0 !important;
    border-bottom: 1px solid #f0f0f0 !important;
    width: 100% !important;
    transition: background 0.15s !important;
}
div[data-testid="stButton"] button:hover {
    background: #f5f5f7 !important;
    border-color: #f0f0f0 !important;
}
div[data-testid="stButton"] button p {
    font-size: 0.95rem !important;
}

/* Segmented control override */
div[data-testid="stSegmentedControl"] button {
    border-radius: 20px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    border: none !important;
    border-bottom: none !important;
    padding: 8px 18px !important;
}

/* No results */
.no-results {
    text-align: center;
    padding: 40px 20px;
    color: #86868b;
    font-size: 0.95rem;
}

/* Divider */
.thin-divider {
    height: 1px;
    background: #e5e5ea;
    margin: 16px 0;
}
</style>
""", unsafe_allow_html=True)


# ---------- Load data ----------
@st.cache_data
def load_protocols():
    p = Path(__file__).parent / "protocols_parsed.json"
    with open(p) as f:
        data = json.load(f)
    protos = list(data.values())
    def sort_key(p):
        m = re.match(r'(\d+)\.(\d+)([A-Z]?)', p['id'])
        if m:
            return (int(m.group(1)), int(m.group(2)), m.group(3))
        return (99, 99, p['id'])
    protos.sort(key=sort_key)
    return {p['id']: p for p in protos}, protos

protocols_dict, protocols_list = load_protocols()


# ---------- Format protocol content for display ----------
def format_protocol_html(text):
    lines = text.split('\n')
    html_parts = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # Caution / red flag
        if 'CAUTION' in stripped.upper() or 'RED FLAG' in stripped.upper():
            html_parts.append(f'<div class="caution-block">⚠️ {stripped}</div>')
        # Standing orders headers
        elif re.match(r'^(FIRST RESPONDER|FR)\s+STANDING\s+ORDER', stripped, re.I):
            html_parts.append(f'<div class="standing-orders fr">{stripped}</div>')
        elif re.match(r'^EMT\s+STANDING\s+ORDER', stripped, re.I):
            html_parts.append(f'<div class="standing-orders emt">{stripped}</div>')
        elif re.match(r'^ADVANCED\s+EMT\s+STANDING\s+ORDER', stripped, re.I):
            html_parts.append(f'<div class="standing-orders aemt">{stripped}</div>')
        elif re.match(r'^PARAMEDIC\s+STANDING\s+ORDER', stripped, re.I):
            html_parts.append(f'<div class="standing-orders paramedic">{stripped}</div>')
        elif re.match(r'^MEDICAL\s+CONTROL', stripped, re.I):
            html_parts.append(f'<div class="standing-orders mc">{stripped}</div>')
        # Section titles (ALL CAPS lines)
        elif stripped.isupper() and len(stripped) > 4 and not stripped.startswith('•'):
            html_parts.append(f'<div class="section-title">{stripped}</div>')
        # NOTE blocks
        elif stripped.upper().startswith('NOTE:') or stripped.upper().startswith('NOTE '):
            html_parts.append(f'<div class="note-block">📝 {stripped}</div>')
        elif stripped.upper().startswith('PEARLS:') or stripped.upper().startswith('PEARL:'):
            html_parts.append(f'<div class="note-block">💡 {stripped}</div>')
        # Bullet points
        elif stripped.startswith('•'):
            html_parts.append(f'<div class="bullet">{stripped[1:].strip()}</div>')
        # Sub-bullets
        elif stripped.startswith('o ') or stripped.startswith('- '):
            html_parts.append(f'<div class="sub-bullet">{stripped[2:].strip()}</div>')
        # Provider level indicators at start
        elif re.match(r'^[EAPFR]\s+•', stripped):
            html_parts.append(f'<div class="bullet">{stripped[2:].strip()}</div>')
        elif re.match(r'^[EAPFR]\s', stripped) and len(stripped) > 3:
            html_parts.append(f'<div class="bullet">{stripped[2:].strip()}</div>')
        else:
            html_parts.append(f'<div class="plain">{stripped}</div>')
    
    return '\n'.join(html_parts)


# ---------- Session state ----------
if 'view' not in st.session_state:
    st.session_state.view = 'list'
if 'selected_id' not in st.session_state:
    st.session_state.selected_id = None

def show_protocol(pid):
    st.session_state.selected_id = pid
    st.session_state.view = 'detail'

def go_back():
    st.session_state.view = 'list'
    st.session_state.selected_id = None


# ==================== DETAIL VIEW ====================
if st.session_state.view == 'detail' and st.session_state.selected_id:
    proto = protocols_dict.get(st.session_state.selected_id)
    if not proto:
        go_back()
        st.rerun()
    
    if st.button("← Back"):
        go_back()
        st.rerun()
    
    # Header
    st.markdown(f'<div class="detail-header">{proto["id"]} — {proto["title"]}</div>', unsafe_allow_html=True)
    
    badges = " ".join(f'<span class="lvl-badge lvl-{l}">{l}</span>' for l in proto.get('provider_levels', []))
    st.markdown(f'<div class="detail-badges">{badges}</div>', unsafe_allow_html=True)
    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    
    # Formatted content
    html = format_protocol_html(proto['content'])
    st.markdown(f'<div class="protocol-body">{html}</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    if st.button("← Back", key="back_bottom"):
        go_back()
        st.rerun()


# ==================== LIST VIEW ====================
else:
    # Title
    st.markdown('<div class="app-title">🚑 MA EMS Protocols</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Statewide Treatment Protocols · v2026.1</div>', unsafe_allow_html=True)
    
    # Provider level filter
    level_options = ["All", "EMT", "AEMT", "Paramedic"]
    level_map = {"EMT": "E", "AEMT": "A", "Paramedic": "P", "All": None}
    selected_level = st.segmented_control(
        "Provider Level",
        options=level_options,
        default="All",
        key="provider_level",
        label_visibility="collapsed",
    )
    active_level = level_map.get(selected_level)
    
    # Search
    search = st.text_input(
        "Search",
        placeholder="Search protocols...",
        label_visibility="collapsed",
    )
    
    query = search.strip().lower() if search else ""
    
    # Filter by level
    if active_level:
        pool = [p for p in protocols_list if active_level in p.get('provider_levels', []) or 'ALL' in p.get('provider_levels', [])]
    else:
        pool = protocols_list
    
    # Search filter
    if query:
        scored = []
        for proto in pool:
            title_l = proto['title'].lower()
            id_l = proto['id'].lower()
            content_l = proto['content'].lower()
            
            score = 0
            if query == id_l:
                score = 100
            elif query in id_l:
                score = 50
            elif query in title_l:
                if any(w.startswith(query) for w in title_l.split()):
                    score = 30
                else:
                    score = 20
            elif query in content_l:
                score = min(10, 1 + content_l.count(query))
            
            if score > 0:
                scored.append((score, proto))
        
        scored.sort(key=lambda x: (-x[0], x[1]['id']))
        filtered = [p for _, p in scored]
    else:
        filtered = pool
    
    # Results count when searching
    if query:
        count = len(filtered)
        st.markdown(f'<div style="color:#86868b;font-size:0.8rem;padding:4px 0 8px 4px;">{count} result{"s" if count != 1 else ""}</div>', unsafe_allow_html=True)
    
    if not filtered:
        st.markdown('<div class="no-results">No protocols found.<br>Try different keywords.</div>', unsafe_allow_html=True)
    elif query:
        # Flat results
        for proto in filtered:
            if st.button(f"**{proto['id']}**  ·  {proto['title']}", key=f"p_{proto['id']}", use_container_width=True):
                show_protocol(proto['id'])
                st.rerun()
    else:
        # Grouped by section
        current_section = None
        for proto in filtered:
            sec = proto.get('section', 'Other')
            if sec != current_section:
                current_section = sec
                # Clean section name
                sec_display = sec.replace('Section ', '').replace(' –', ' ·')
                st.markdown(f'<div class="section-header">{sec_display}</div>', unsafe_allow_html=True)
            
            if st.button(f"**{proto['id']}**  ·  {proto['title']}", key=f"p_{proto['id']}", use_container_width=True):
                show_protocol(proto['id'])
                st.rerun()
