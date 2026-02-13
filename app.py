import streamlit as st
import json
import re
from pathlib import Path

# ---------- Page config ----------
st.set_page_config(
    page_title="MA EMS Protocols",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Custom CSS for mobile-friendly, big text ----------
st.markdown("""
<style>
/* Global */
html, body, [class*="css"] { font-size: 18px; }
h1 { font-size: 2rem !important; }
h2 { font-size: 1.6rem !important; }
h3 { font-size: 1.3rem !important; }

/* Sidebar nav links */
.sidebar-link {
    display: block;
    padding: 6px 8px;
    margin: 2px 0;
    border-radius: 6px;
    text-decoration: none;
    color: inherit;
    font-size: 0.95rem;
    line-height: 1.3;
    cursor: pointer;
}
.sidebar-link:hover { background: rgba(151,166,195,0.15); }

/* Provider level badges */
.badge { 
    display: inline-block; padding: 2px 8px; border-radius: 4px; 
    font-size: 0.8rem; font-weight: 700; margin-right: 4px; 
}
.badge-fr { background: #4a90d9; color: white; }
.badge-e { background: #f0ad4e; color: black; }
.badge-a { background: #5cb85c; color: white; }
.badge-p { background: #d9534f; color: white; }
.badge-all { background: #777; color: white; }

/* Caution blocks */
.caution-block {
    background: #fff3cd; border-left: 5px solid #dc3545;
    padding: 12px 16px; margin: 12px 0; border-radius: 4px;
    font-weight: 600; color: #856404;
}

/* Protocol content */
.protocol-content {
    font-size: 1.05rem;
    line-height: 1.7;
    white-space: pre-wrap;
    word-wrap: break-word;
}

/* Search results count */
.result-count { color: #888; font-size: 0.9rem; margin-bottom: 1rem; }

/* Section headers in sidebar */
.section-header {
    font-weight: 700; font-size: 0.9rem; color: #666;
    margin-top: 16px; margin-bottom: 4px; padding: 4px 8px;
    text-transform: uppercase; letter-spacing: 0.5px;
    border-bottom: 1px solid #ddd;
}

/* Make buttons look like links on mobile */
div[data-testid="stButton"] button {
    text-align: left !important;
    padding: 8px 12px !important;
    font-size: 1rem !important;
}
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
        return json.load(f)

protocols = load_protocols()

# ---------- Provider level helpers ----------
LEVEL_ORDER = ['FR', 'E', 'A', 'P', 'ALL']
LEVEL_LABELS = {
    'FR': 'First Responder', 'E': 'EMT', 'A': 'AEMT', 
    'P': 'Paramedic', 'ALL': 'All Levels'
}
LEVEL_CSS = {'FR': 'fr', 'E': 'e', 'A': 'a', 'P': 'p', 'ALL': 'all'}

def level_badges(levels):
    return " ".join(
        f'<span class="badge badge-{LEVEL_CSS.get(l,"all")}">{l}</span>'
        for l in levels
    )

def format_content(text):
    """Format protocol content with caution highlighting."""
    # Highlight CAUTION lines
    lines = text.split('\n')
    formatted = []
    in_caution = False
    for line in lines:
        if 'CAUTION' in line.upper() or 'RED FLAG' in line.upper():
            formatted.append(f'<div class="caution-block">⚠️ {line}</div>')
            in_caution = True
        elif in_caution and line.strip() and not line.strip().startswith(('•', '–', '-', 'E', 'A', 'P', 'FR')):
            formatted.append(f'<div class="caution-block">{line}</div>')
        else:
            in_caution = False
            # Bold standing order headers
            if 'STANDING ORDER' in line.upper() or 'MEDICAL CONTROL' in line.upper():
                formatted.append(f'**{line}**')
            else:
                formatted.append(line)
    return '\n'.join(formatted)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🚑 MA EMS Protocols")
    st.markdown("**v2026.1**")
    
    # Provider filter
    level_filter = st.multiselect(
        "Filter by Provider Level",
        options=['FR', 'E', 'A', 'P'],
        format_func=lambda x: LEVEL_LABELS.get(x, x),
        default=[],
        help="Show only protocols relevant to selected levels"
    )
    
    st.markdown("---")
    
    # Group protocols by section
    sections = {}
    for pid, proto in protocols.items():
        sec = proto['section']
        if sec not in sections:
            sections[sec] = []
        sections[sec].append(proto)
    
    for sec_name, sec_protos in sections.items():
        # Filter by provider level if selected
        if level_filter:
            sec_protos = [p for p in sec_protos if 
                         any(l in p['provider_levels'] for l in level_filter) or 
                         'ALL' in p['provider_levels']]
        if not sec_protos:
            continue
        
        st.markdown(f'<div class="section-header">{sec_name}</div>', unsafe_allow_html=True)
        for proto in sec_protos:
            if st.button(
                f"{proto['id']} – {proto['title'][:50]}",
                key=f"nav_{proto['id']}",
                use_container_width=True,
            ):
                st.session_state['selected'] = proto['id']
                st.session_state['search'] = ''

# ---------- Main content ----------
# Search bar - prominent at top
search = st.text_input(
    "🔍 Search protocols",
    value=st.session_state.get('search', ''),
    placeholder="Type to search... (e.g., cardiac arrest, seizure, epinephrine)",
    key="search_input",
)

if search != st.session_state.get('search', ''):
    st.session_state['search'] = search
    st.session_state.pop('selected', None)

selected_id = st.session_state.get('selected', None)

# ---------- Search results ----------
if search:
    query = search.lower()
    results = []
    for pid, proto in protocols.items():
        # Filter by provider level
        if level_filter:
            if not (any(l in proto['provider_levels'] for l in level_filter) or 
                    'ALL' in proto['provider_levels']):
                continue
        
        title_match = query in proto['title'].lower()
        id_match = query in proto['id'].lower()
        content_match = query in proto['content'].lower()
        
        if title_match or id_match or content_match:
            # Score: title/id matches rank higher
            score = 0
            if id_match: score += 10
            if title_match: score += 5
            if content_match: score += 1
            results.append((score, proto))
    
    results.sort(key=lambda x: -x[0])
    
    st.markdown(f'<div class="result-count">{len(results)} result{"s" if len(results) != 1 else ""} for "{search}"</div>', unsafe_allow_html=True)
    
    if results:
        for score, proto in results:
            col1, col2 = st.columns([5, 1])
            with col1:
                if st.button(
                    f"**{proto['id']}** – {proto['title']}",
                    key=f"search_{proto['id']}",
                    use_container_width=True,
                ):
                    st.session_state['selected'] = proto['id']
                    st.rerun()
            with col2:
                st.markdown(level_badges(proto['provider_levels']), unsafe_allow_html=True)
    else:
        st.info("No protocols found. Try different keywords.")

# ---------- Display selected protocol ----------
elif selected_id and selected_id in protocols:
    proto = protocols[selected_id]
    
    # Header
    st.markdown(f"# {proto['id']} – {proto['title']}")
    st.markdown(level_badges(proto['provider_levels']), unsafe_allow_html=True)
    st.markdown("---")
    
    # Content
    content = format_content(proto['content'])
    st.markdown(f'<div class="protocol-content">{content}</div>', unsafe_allow_html=True)

# ---------- Home screen ----------
else:
    st.markdown("# 🚑 Massachusetts EMS Protocols")
    st.markdown("### Statewide Treatment Protocols v2026.1")
    st.markdown("---")
    
    st.markdown("**Quick access:** Use the search bar above or open the sidebar (☰) to browse by section.")
    st.markdown("")
    
    # Show section overview as quick links
    sections_short = {
        '1': ('🏥', 'General Patient Care'),
        '2': ('💊', 'Medical Protocols'),
        '3': ('❤️', 'Cardiac Emergencies'),
        '4': ('🩹', 'Trauma Protocols'),
        '5': ('🫁', 'Airway Protocols'),
        '6': ('👨‍⚕️', 'Medical Director Options'),
        '7': ('📋', 'Policies & Procedures'),
        '8': ('🔥', 'Special Operations'),
    }
    
    cols = st.columns(2)
    for i, (sec_num, (icon, name)) in enumerate(sections_short.items()):
        sec_protocols = [p for p in protocols.values() if p.get('section_num') == sec_num]
        with cols[i % 2]:
            with st.expander(f"{icon} Section {sec_num} – {name} ({len(sec_protocols)})"):
                for proto in sec_protocols:
                    if st.button(
                        f"{proto['id']} – {proto['title'][:45]}",
                        key=f"home_{proto['id']}",
                        use_container_width=True,
                    ):
                        st.session_state['selected'] = proto['id']
                        st.rerun()
    
    # Appendices
    app_protocols = [p for p in protocols.values() if p.get('section_num') == 'A']
    if app_protocols:
        with st.expander(f"📎 Appendices ({len(app_protocols)})"):
            for proto in app_protocols:
                if st.button(
                    f"{proto['id']} – {proto['title'][:45]}",
                    key=f"home_{proto['id']}",
                    use_container_width=True,
                ):
                    st.session_state['selected'] = proto['id']
                    st.rerun()
