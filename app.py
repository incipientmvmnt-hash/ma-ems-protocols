import streamlit as st
import json
import re
from pathlib import Path

# ---------- Page config ----------
st.set_page_config(
    page_title="MA EMS Protocols",
    page_icon="🚑",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------- Custom CSS ----------
st.markdown("""
<style>
/* Clean, mobile-first design */
html, body, [class*="css"] { font-size: 17px; }
h1 { font-size: 1.8rem !important; margin-bottom: 0.3rem !important; }
h2 { font-size: 1.4rem !important; }
h3 { font-size: 1.2rem !important; }

/* Search input - big and prominent */
div[data-testid="stTextInput"] input {
    font-size: 1.2rem !important;
    padding: 14px 16px !important;
    border-radius: 12px !important;
    border: 2px solid #ddd !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #d9534f !important;
    box-shadow: 0 0 0 2px rgba(217,83,79,0.2) !important;
}

/* Protocol list items */
.proto-item {
    display: block;
    padding: 14px 16px;
    margin: 4px 0;
    border-radius: 10px;
    border: 1px solid #e8e8e8;
    background: white;
    cursor: pointer;
    text-decoration: none;
    color: inherit;
    transition: all 0.15s;
}
.proto-item:hover { 
    background: #f8f9fa; 
    border-color: #d9534f;
    transform: translateX(2px);
}
.proto-id {
    font-weight: 800;
    color: #d9534f;
    font-size: 1rem;
    margin-right: 8px;
}
.proto-title {
    font-size: 1.05rem;
    font-weight: 500;
}
.proto-section-tag {
    font-size: 0.75rem;
    color: #999;
    margin-top: 2px;
}

/* Provider badges */
.badge { 
    display: inline-block; padding: 2px 8px; border-radius: 4px; 
    font-size: 0.75rem; font-weight: 700; margin-right: 3px; 
}
.badge-FR { background: #4a90d9; color: white; }
.badge-E { background: #f0ad4e; color: black; }
.badge-A { background: #5cb85c; color: white; }
.badge-P { background: #d9534f; color: white; }

/* Caution blocks */
.caution-block {
    background: #fff3cd; border-left: 5px solid #dc3545;
    padding: 12px 16px; margin: 10px 0; border-radius: 4px;
    font-weight: 600; color: #856404;
}

/* Protocol content */
.protocol-content {
    font-size: 1.05rem;
    line-height: 1.7;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* Back button */
.back-btn button {
    font-size: 1.1rem !important;
    padding: 10px 20px !important;
}

/* Section dividers */
.section-divider {
    font-weight: 800;
    font-size: 0.85rem;
    color: #d9534f;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 16px 0 6px 4px;
    border-bottom: 2px solid #d9534f;
    margin-top: 20px;
}

/* Hide streamlit menu & footer for clean look */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Highlighted match text */
mark { background: #fff3cd; padding: 1px 3px; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ---------- Load data ----------
@st.cache_data
def load_protocols():
    p = Path(__file__).parent / "protocols_parsed.json"
    if not p.exists():
        st.error("protocols_parsed.json not found. Run parse_protocols.py first.")
        st.stop()
    with open(p) as f:
        data = json.load(f)
    # Build a flat sorted list
    protos = []
    for pid, proto in data.items():
        proto['_id'] = pid
        protos.append(proto)
    # Sort by protocol ID numerically
    def sort_key(p):
        m = re.match(r'(\d+)\.(\d+)([A-Z]?)', p['id'])
        if m:
            return (int(m.group(1)), int(m.group(2)), m.group(3))
        return (99, 99, p['id'])
    protos.sort(key=sort_key)
    return {p['_id']: p for p in protos}, protos

protocols_dict, protocols_list = load_protocols()

# ---------- Session state ----------
if 'view' not in st.session_state:
    st.session_state.view = 'list'  # 'list' or 'detail'
if 'selected_id' not in st.session_state:
    st.session_state.selected_id = None

def show_protocol(pid):
    st.session_state.selected_id = pid
    st.session_state.view = 'detail'

def go_back():
    st.session_state.view = 'list'
    st.session_state.selected_id = None

# ---------- DETAIL VIEW ----------
if st.session_state.view == 'detail' and st.session_state.selected_id:
    proto = protocols_dict.get(st.session_state.selected_id)
    if not proto:
        st.error("Protocol not found")
        go_back()
        st.rerun()
    
    # Back button
    if st.button("← Back to Protocols", type="secondary"):
        go_back()
        st.rerun()
    
    # Header
    st.markdown(f"# {proto['id']} — {proto['title']}")
    
    # Provider badges
    badges = " ".join(f'<span class="badge badge-{l}">{l}</span>' for l in proto.get('provider_levels', []))
    if badges:
        st.markdown(badges, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Content with caution highlighting
    content = proto['content']
    lines = content.split('\n')
    formatted = []
    for line in lines:
        if 'CAUTION' in line.upper() or 'RED FLAG' in line.upper():
            formatted.append(f'<div class="caution-block">⚠️ {line}</div>')
        elif 'STANDING ORDER' in line.upper() or 'MEDICAL CONTROL' in line.upper():
            formatted.append(f'**{line}**')
        else:
            formatted.append(line)
    
    st.markdown(f'<div class="protocol-content">{"<br>".join(formatted)}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    if st.button("← Back to Protocols", key="back_bottom", type="secondary"):
        go_back()
        st.rerun()

# ---------- LIST VIEW ----------
else:
    st.markdown("# 🚑 MA EMS Protocols")
    st.caption("Statewide Treatment Protocols v2026.1")
    
    # Provider level selector
    level_options = ["All Levels", "EMT", "AEMT", "Paramedic"]
    level_map = {"EMT": "E", "AEMT": "A", "Paramedic": "P", "All Levels": None}
    selected_level = st.segmented_control(
        "I am a:",
        options=level_options,
        default="All Levels",
        key="provider_level",
    )
    active_level = level_map.get(selected_level)
    
    # Search bar
    search = st.text_input(
        "Search",
        placeholder="Search protocols... (e.g., cardiac arrest, seizure, intubation)",
        label_visibility="collapsed",
    )
    
    query = search.strip().lower() if search else ""
    
    # Filter by provider level first
    if active_level:
        level_filtered = [p for p in protocols_list if active_level in p.get('provider_levels', []) or 'ALL' in p.get('provider_levels', [])]
    else:
        level_filtered = protocols_list
    
    # Filter protocols
    if query:
        scored = []
        for proto in level_filtered:
            title_lower = proto['title'].lower()
            id_lower = proto['id'].lower()
            content_lower = proto['content'].lower()
            
            score = 0
            # Exact ID match
            if query == id_lower:
                score = 100
            elif query in id_lower:
                score = 50
            # Title match (strongest signal)
            elif query in title_lower:
                # Boost if query matches start of a word in title
                words = title_lower.split()
                if any(w.startswith(query) for w in words):
                    score = 30
                else:
                    score = 20
            # Content match
            elif query in content_lower:
                # Count occurrences for relevance
                count = content_lower.count(query)
                score = min(10, 1 + count)
            
            if score > 0:
                scored.append((score, proto))
        
        scored.sort(key=lambda x: (-x[0], x[1]['id']))
        filtered = [p for _, p in scored]
    else:
        filtered = level_filtered
    
    # Show count
    if query:
        st.caption(f"{len(filtered)} result{'s' if len(filtered) != 1 else ''}")
    
    # Display protocols grouped by section (or flat if searching)
    if query:
        # Flat list for search results - no section headers, just results
        for proto in filtered:
            if st.button(
                f"**{proto['id']}** — {proto['title']}",
                key=f"p_{proto['id']}",
                use_container_width=True,
            ):
                show_protocol(proto['_id'])
                st.rerun()
    else:
        # Grouped by section
        current_section = None
        for proto in filtered:
            sec = proto.get('section', '')
            if sec != current_section:
                current_section = sec
                st.markdown(f'<div class="section-divider">{sec}</div>', unsafe_allow_html=True)
            
            if st.button(
                f"**{proto['id']}** — {proto['title']}",
                key=f"p_{proto['id']}",
                use_container_width=True,
            ):
                show_protocol(proto['_id'])
                st.rerun()
