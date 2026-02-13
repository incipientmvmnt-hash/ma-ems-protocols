#!/usr/bin/env python3
"""Audit and fix protocol content artifacts from PDF extraction."""

import json
import re
from pathlib import Path

def fix_protocol_content(pid, content):
    """Apply all fixes to a protocol's content. Returns (fixed_content, list_of_fixes)."""
    fixes = []
    original = content

    # 1. Remove stray artifact numbers like 20210313, 2013, 20213 on their own or inline
    # These are page/date artifacts from PDF extraction
    for pattern, desc in [
        (r'\b20210313\b', 'stray date artifact 20210313'),
        (r'\b20213\b', 'stray number 20213'),
        (r'(?<!\d)2013(?!\d)(?!\s*[-–])', 'stray year artifact 2013'),
    ]:
        if re.search(pattern, content):
            count = len(re.findall(pattern, content))
            content = re.sub(pattern, '', content)
            fixes.append(f"Removed {count}x {desc}")

    # 2. Remove reversed/garbled text patterns (PDF extraction artifacts)
    # Patterns like P3.2, A6.2, P2.2, A2.2 etc at start of line or standalone
    reversed_patterns = [
        (r'\b[A-Z]\d+\.\d+\b(?!\s*(mg|ml|mm|cm|kg|grams?|mcg|units?|liter|percent|%|hour|min))', 'reversed protocol ref'),
        (r'\blocotorP\b', 'reversed text "locotorP"'),
        (r'\blacideM\b', 'reversed text "lacideM"'),
        (r'\beraC\s+tneitaP\b', 'reversed text "eraC tneitaP"'),
    ]
    for pattern, desc in reversed_patterns:
        if re.search(pattern, content):
            count = len(re.findall(pattern, content))
            content = re.sub(pattern, '', content)
            fixes.append(f"Removed {count}x {desc}")

    # 3. Remove duplicate title lines within content
    # These are lines that repeat the protocol title with garbled numbering
    # e.g. "Altered Mental/Neurological Status/Diabetic 2.3P Emergencies/Coma – Pediatric"
    # Look for lines that have a protocol number embedded mid-title
    dup_title_pattern = r'\n[^\n]*\d+\.\d+[A-Z]?\s+[^\n]*(?:Emergencies|Distress|Poisoning|Care|Arrest|Born|Management|Restraint|Hemorrhage|Hypothermia|Hyperthermia|Insufficiency|Anaphylaxis|Reaction|Behavioral|Obstetrical|Stroke|Seizure|Nausea|Pain)[^\n]*'
    # More targeted: lines that look like "Title X.XY Title continued"
    
    # 4. Replace weird Unicode characters
    unicode_fixes = [
        ('\uf0b7', '•'),
        ('\uf020', ' '),
        ('\uf0a7', '•'),
        ('\uf0d8', '•'),
    ]
    for char, replacement in unicode_fixes:
        if char in content:
            count = content.count(char)
            content = content.replace(char, replacement)
            fixes.append(f"Replaced {count}x Unicode char {repr(char)} with '{replacement}'")

    # 5. Remove stray single-letter provider level indicators on their own line
    # Lines that are just E, A, P, FR (with optional whitespace)
    lines = content.split('\n')
    new_lines = []
    removed_indicators = 0
    for line in lines:
        stripped = line.strip()
        if stripped in ('E', 'A', 'P', 'FR', 'E •', 'A •', 'P •'):
            removed_indicators += 1
            # If it's "E •" etc, keep the bullet
            if '•' in stripped:
                new_lines.append('•')
            continue
        # Also remove lines that are just "E /" or "A /" or similar
        if re.match(r'^[EAPFR]+\s*[/•]?\s*$', stripped) and len(stripped) <= 4:
            removed_indicators += 1
            continue
        new_lines.append(line)
    if removed_indicators:
        fixes.append(f"Removed {removed_indicators}x stray provider level indicators")
    content = '\n'.join(new_lines)

    # 6. Remove "Protocol Continues" / "Protocol Continued" lines
    proto_cont_pattern = r'\n[^\n]*Protocol\s+Continu(?:es|ed)[^\n]*'
    matches = re.findall(proto_cont_pattern, content, re.IGNORECASE)
    if matches:
        content = re.sub(proto_cont_pattern, '', content, flags=re.IGNORECASE)
        fixes.append(f"Removed {len(matches)}x 'Protocol Continues/Continued' lines")

    # 7. Remove footer text
    footer_patterns = [
        r'Massachusetts Department of Public Health[^\n]*',
        r'Office of Emergency Medical Services[^\n]*',
        r'Bureau of Health Care Safety and Quality[^\n]*',
    ]
    for pat in footer_patterns:
        if re.search(pat, content, re.IGNORECASE):
            content = re.sub(pat, '', content, flags=re.IGNORECASE)
            fixes.append(f"Removed footer text matching: {pat[:40]}...")

    # 8. Fix broken line wraps - merge lines split mid-sentence
    # A line ending without punctuation followed by a line starting lowercase
    lines = content.split('\n')
    merged_lines = []
    i = 0
    merge_count = 0
    while i < len(lines):
        line = lines[i]
        # Check if next line should be merged (starts lowercase, current doesn't end with terminal punct)
        while (i + 1 < len(lines) and 
               lines[i+1].strip() and
               lines[i+1].strip()[0].islower() and
               not line.strip().endswith(('.', ':', ';', '!', '?', '•', ')')) and
               line.strip() and
               not lines[i+1].strip().startswith(('o ', '- ', '•'))):
            merge_count += 1
            line = line.rstrip() + ' ' + lines[i+1].strip()
            i += 1
        merged_lines.append(line)
        i += 1
    if merge_count:
        fixes.append(f"Merged {merge_count}x broken line wraps")
    content = '\n'.join(merged_lines)

    # Clean up multiple blank lines and trailing spaces
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = re.sub(r' {2,}', ' ', content)
    content = content.strip()

    return content, fixes


def main():
    path = Path(__file__).parent / "protocols_parsed.json"
    with open(path) as f:
        data = json.load(f)

    total_fixes = 0
    for pid, proto in data.items():
        fixed_content, fixes = fix_protocol_content(pid, proto['content'])
        if fixes:
            print(f"\n{'='*60}")
            print(f"Protocol {pid}: {proto['title']}")
            for fix in fixes:
                print(f"  ✓ {fix}")
            total_fixes += len(fixes)
        proto['content'] = fixed_content

    # Save back
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"DONE: Applied {total_fixes} total fixes across {len(data)} protocols.")
    print(f"Saved to {path}")


if __name__ == '__main__':
    main()
