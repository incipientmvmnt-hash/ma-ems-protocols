"""Clean up parsed protocol content for display."""
import json
import re

with open("protocols_parsed.json") as f:
    protocols = json.load(f)

def clean_content(text, proto_id, proto_title):
    """Clean up PDF extraction artifacts."""
    lines = text.split('\n')
    cleaned = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines (we'll add spacing later)
        if not stripped:
            continue
        
        # Skip reversed sidebar text (backwards words like "eraC tneitaP lareneG")
        if re.match(r'^[a-z]{3,}\s+[a-z]{3,}$', stripped) and stripped != stripped.lower():
            continue
        reversed_artifacts = [
            'eraC', 'tneitaP', 'lareneG', 'locotorP', 'lacideM',
            'cairdaC', 'seicnegremE', 'amuarT', 'slocotorP',
            'yawriA', 'snoitarepO', 'laicepS', 'snoitpO',
            'rotceriD', 'seiciloP', 'serudecorP'
        ]
        if any(rev in stripped for rev in reversed_artifacts):
            continue
        
        # Skip repeated protocol ID lines at top of pages
        if stripped == proto_id:
            continue
        if re.match(r'^\d+\.\d+[A-Z]?$', stripped):
            continue
            
        # Skip page footers
        if 'Massachusetts Department of Public Health' in stripped:
            continue
        if 'Statewide Treatment Protocols version' in stripped:
            continue
        if stripped == 'Protocol Continues':
            continue
        if re.match(r'^20\d{2}$', stripped):  # stray year numbers
            continue
        
        # Skip duplicate title lines (e.g., "1.0 Routine Patient Care")
        if stripped.startswith(f'{proto_id} '):
            # Only skip if it's just the title repeated
            remainder = stripped[len(proto_id):].strip()
            if remainder.lower() == proto_title.lower():
                continue
        
        # Skip merged ID strings like "1.11.1" or "2.2A2.2A"  
        if re.match(r'^\d+\.\d+[A-Z]?\d+\.\d+[A-Z]?$', stripped):
            continue
        
        # Clean up bullet characters
        stripped = stripped.replace('\uf0b7\uf020', '• ')
        stripped = stripped.replace('\uf0b7', '•')
        stripped = stripped.replace('\uf020', ' ')
        stripped = re.sub(r'^•\s*$', '', stripped)  # standalone bullet
        
        # Fix bullets on their own line - merge with next content
        if stripped == '•':
            continue
        
        if not stripped:
            continue
            
        cleaned.append(stripped)
    
    # Now merge lines intelligently
    merged = []
    i = 0
    while i < len(cleaned):
        line = cleaned[i]
        
        # If line is a bullet point followed by continuation text
        if line.startswith('•') and not line.endswith('.') and not line.endswith(':'):
            # Look ahead for continuation
            while i + 1 < len(cleaned) and not cleaned[i+1].startswith('•') and \
                  not cleaned[i+1].startswith('—') and \
                  not cleaned[i+1].isupper() and \
                  not re.match(r'^(EMT|ADVANCED|PARAMEDIC|FIRST|MEDICAL|NOTE|PEARLS|CAUTION)', cleaned[i+1]) and \
                  not cleaned[i+1].startswith('o '):
                i += 1
                line += ' ' + cleaned[i]
        elif not line.startswith('•') and not line.startswith('o ') and \
             not line.endswith(':') and not line.endswith('.') and \
             not line.isupper() and \
             not re.match(r'^(EMT|ADVANCED|PARAMEDIC|FIRST|MEDICAL|NOTE|PEARLS|CAUTION|FR|[EAPFR]\s)', line):
            # Continuation of previous line
            while i + 1 < len(cleaned) and not cleaned[i+1].startswith('•') and \
                  not cleaned[i+1].startswith('—') and \
                  not cleaned[i+1].isupper() and \
                  not re.match(r'^(EMT|ADVANCED|PARAMEDIC|FIRST|MEDICAL|NOTE|PEARLS|CAUTION|[EAPFR]\s)', cleaned[i+1]) and \
                  not cleaned[i+1].startswith('o '):
                i += 1
                line += ' ' + cleaned[i]
        
        merged.append(line)
        i += 1
    
    return '\n'.join(merged)


for pid, proto in protocols.items():
    proto['content'] = clean_content(proto['content'], proto['id'], proto['title'])

with open("protocols_parsed.json", "w") as f:
    json.dump(protocols, f, indent=2)

# Stats
total_chars = sum(len(p['content']) for p in protocols.values())
print(f"Cleaned {len(protocols)} protocols ({total_chars:,} chars total)")
for pid in list(protocols.keys())[:3]:
    print(f"\n--- {pid}: {protocols[pid]['title']} ---")
    print(protocols[pid]['content'][:400])
