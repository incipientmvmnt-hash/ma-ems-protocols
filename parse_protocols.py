#!/usr/bin/env python3
"""Parse MA EMS protocols from extracted JSON into structured data."""

import json
import re

def parse_protocols():
    with open('protocols_full.json', 'r') as f:
        pages = json.load(f)
    
    # Build TOC mapping from pages 3-5
    toc = {}
    toc_text = ""
    for p in pages:
        if p['page'] in (3, 4, 5):
            toc_text += p['text'] + "\n"
    
    toc_lines = toc_text.split('\n')
    for line in toc_lines:
        m = re.search(r'^(.+?)[….\u2026\s]+(\d+\.\d+[A-Z]?)\s*$', line.strip())
        if m:
            title = re.sub(r'[…\u2026.]+$', '', m.group(1)).strip()
            title = re.sub(r'\s+', ' ', title)
            pid = m.group(2)
            if title and not title.upper().startswith('SECTION'):
                toc[pid] = title
        m = re.search(r'^(.+?)[….\u2026\s]+(A\d+)\s*$', line.strip())
        if m:
            title = re.sub(r'[…\u2026.]+$', '', m.group(1)).strip()
            title = re.sub(r'\s+', ' ', title)
            if title:
                toc[m.group(2)] = title
    
    valid_ids = set(toc.keys())
    
    # Reversed section name -> section number
    rev_sections = {
        'lareneG': '1', 'lacideM': '2', 'caidraC': '3', 
        'amuarT': '4', 'serudecorP': '5', 'snoitpO': '6',
        'seiciloP': '7', 'selpicnirP': '8'
    }
    
    def detect_section(text):
        """Detect section from reversed sidebar text."""
        for marker, sec in rev_sections.items():
            if marker in text:
                return sec
        return None
    
    def find_protocol_id(text, page_num):
        """Find protocol ID in page text."""
        lines = text.strip().split('\n')
        section = detect_section(text)
        
        # Collect candidate IDs from text
        candidates = []
        
        for i, line in enumerate(lines[:15]):
            line = line.strip()
            # Direct match in TOC
            for vid in valid_ids:
                if line == vid or line.startswith(vid + ' '):
                    candidates.append((vid, 0 if i == 0 else 1))
                if re.search(r'\b' + re.escape(vid) + r'\s*$', line) and not line.startswith('1.0 Routine'):
                    candidates.append((vid, 2))
            
            # Reversed ID pattern
            m = re.match(r'^([A-Z]?)(\d+\.\d+)([A-Z]?)\s*$', line)
            if m:
                raw = m.group(1) + m.group(2) + m.group(3)
                rev = raw[::-1]
                if rev in valid_ids:
                    candidates.append((rev, 0 if i == 0 else 1))
                # Try section-aware reversal: if we know section, the reversed
                # "X.Y" where section=S means the actual ID is "S.XY" or similar
                if section:
                    # e.g., section=6, line="9.6" -> try "6.9"
                    num = m.group(2)
                    parts = num.split('.')
                    # Reversed: "AB.S" -> "S.BA"
                    if parts[1] == section:
                        new_id = section + '.' + parts[0][::-1]
                        if new_id in valid_ids:
                            candidates.append((new_id, 0))
                        # With suffix
                        for suffix in ['A', 'P']:
                            if (m.group(1) + new_id) in valid_ids:
                                candidates.append((m.group(1) + new_id, 0))
                            if (new_id + m.group(3)) in valid_ids:
                                candidates.append((new_id + m.group(3), 0))
                            if (m.group(1)[::-1] + new_id) in valid_ids:
                                candidates.append((m.group(1)[::-1] + new_id, 0))
        
        if not candidates:
            return None
        
        # Filter by detected section if available
        if section:
            sec_candidates = [(c, p) for c, p in candidates 
                            if c.split('.')[0] == section or c.startswith('A')]
            if sec_candidates:
                candidates = sec_candidates
        
        # Pick best candidate (lowest priority number, then first found)
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0]
    
    # Manual overrides for pages that are hard to auto-detect
    manual_map = {
        17: '2.2A',   # Anaphylaxis criteria continuation
        18: '2.3A',   # Altered Mental Status Adult
        19: '2.3P',   # Altered Mental Status Pediatric
        20: '2.4',    # Behavioral Emergencies
        21: '2.4',    # Behavioral Emergencies continuation
        22: '2.5',    # Behavioral Emergencies Restraint
        23: '2.6A',   # Bronchospasm Adult
        24: '2.6P',   # Bronchospasm Pediatric
        25: '2.6P',   # continuation
        26: '2.7',    # Hyperthermia
        27: '2.8',    # Hypothermia
        28: '2.9',    # Nerve Agent
        29: '2.9',    # Nerve Agent adult treatment
        30: '2.9',    # Nerve Agent pediatric dosing
        31: '2.10',   # Obstetrical Emergencies
        32: '2.11',   # Newly Born Care
        33: '2.12',   # Resuscitation Newly Born
        34: '2.12',   # continuation
        35: '2.12',   # continuation
        36: '2.13',   # Pain and Nausea
        37: '2.14',   # Poisoning/Overdose
        38: '2.15A',  # Seizures Adult
        39: '2.15P',  # Seizures Pediatric
        40: '2.16A',  # Shock Adult
        41: '2.16A',  # continuation
        42: '2.16A',  # continuation
        43: '2.16P',  # Shock Pediatric
        44: '2.17A',  # Sepsis Adult
        45: '2.17P',  # Sepsis Pediatric
        46: '2.18',   # Stroke
        47: '2.18',   # continuation (was wrongly 2.17)
        48: '2.19',   # Hyperkalemia
        49: '2.20',   # Home Hemodialysis
        50: '2.20',   # continuation
        52: '3.1',    # ACS
        53: '3.1',    # continuation
        54: '3.1',    # continuation
        55: '3.2',    # A-fib
        56: '3.3A',   # Bradycardia Adult
        57: '3.3P',   # Bradycardia Pediatric
        58: '3.4A',   # Cardiac Arrest Adult Asystole/PEA
        59: '3.4P',   # Cardiac Arrest Pediatric Asystole/PEA
        60: '3.5A',   # Cardiac Arrest Adult VF/VT
        61: '3.5P',   # Cardiac Arrest Pediatric VF/VT
        62: '3.6',    # CHF/Pulmonary Edema
        63: '3.7',    # Targeted Temp Management
        64: '3.8',    # Post Resuscitative Care
        65: '3.9A',   # SVT Adult
        66: '3.9P',   # SVT Pediatric
        67: '3.10',   # VT with Pulses
        69: '4.1',    # Burns
        70: '4.1',    # continuation
        71: '4.2',    # Drowning
        72: '4.3',    # Eye Emergencies
        73: '4.4',    # Head Trauma
        74: '4.5',    # Multisystem Trauma
        75: '4.6',    # Musculoskeletal
        76: '4.7',    # Soft Tissue
        77: '4.7',    # continuation
        78: '4.8',    # Spinal
        79: '4.8',    # continuation
        80: '4.9',    # Thoracic
        81: '4.10',   # Traumatic Amputations
        82: '4.11',   # Traumatic Cardiac Arrest
        84: '5.1A',   # Upper Airway Adult
        85: '5.1P',   # Upper Airway Pediatric
        86: '5.2',    # Difficult Airway
        87: '5.3',    # Tracheostomy
        88: '5.4',    # Sedation Intubated
        90: '6.0',    # Medical Director Options
        91: '6.1',    # Needle Cric continuation
        92: '6.1',    # Needle Cric
        93: '6.2',    # Surgical Cric
        94: '6.2',    # continuation
        95: '6.3',    # Glucagon (reversed 3.6 in S6)
        96: '6.4',    # Withholding Resuscitation (reversed 4.6 in S6)
        97: '6.5',    # 12 Lead ECG
        98: '6.5',    # continuation
        99: '6.6',    # Leave-Behind Naloxone
        100: '7.6',   # Sedation for Electrical Therapy
        101: '6.8',   # Automated Transport Ventilators
        102: '6.9',   # Oral Antipsychotics
        103: '6.10',  # Bolus NTG
        104: '6.11',  # Buprenorphine
        105: '6.11',  # continuation
        106: '6.11',  # continuation
        107: '6.12',  # Antibiotic Infusions
        108: '6.13',  # LTOWB
        109: '6.13',  # continuation
        110: '6.13',  # continuation
        111: '6.13',  # continuation
        113: '7.1',   # Air Medical Transport
        114: '7.1',   # continuation
        115: '7.2',   # Electrical Control Weapons (reversed 2.7 in S7)
        116: '7.3',   # MOLST
        117: '7.3',   # continuation
        118: '7.3',   # continuation
        119: '7.4',   # Pediatric Transport
        120: '7.4',   # continuation
        121: '7.5',   # Refusal
        122: '7.5',   # continuation
        123: '6.7',   # Ultrasound
        124: '7.7',   # Withholding
        125: '7.7',   # continuation
        126: '7.8',   # VADs
        127: '7.8',   # continuation
        128: '7.8',   # continuation
        130: '8.1',   # Fire Rehab
        131: '8.1',   # continuation
        132: '8.2',   # MCI Triage
        133: '8.2',   # continuation
        134: '8.3',   # HazMat (reversed 3.8 in S8)
        135: '8.3',   # continuation
        136: '8.4',   # USAR
        137: '8.4',   # continuation
        138: '8.4',   # continuation
        139: '8.4',   # continuation
        140: '8.4',   # continuation
        141: '8.4',   # continuation
        142: '8.4',   # continuation
        143: '8.4',   # continuation
        144: '8.4',   # continuation
        145: '8.4',   # continuation
        146: None,     # Appendices divider
        147: 'A1',    # IFT TOC
        148: 'A1',
        149: 'A1',
        150: 'A1',
        151: 'A1',
        152: 'A1',
        153: 'A1',
        154: 'A1',
        155: 'A1',
        156: 'A1',
        157: 'A1',
        158: 'A1',
        159: 'A1',
        160: 'A1',
        161: 'A1',
        162: 'A1',
        163: 'A1',
        164: 'A1',
        165: 'A1',
        166: 'A1',
        167: 'A1',
        168: 'A2',
        169: 'A2',
        170: 'A2',
        171: 'A2',
        172: 'A3',    # EMS Assessment Tool
        173: 'A3',
        174: 'A3',
        175: 'A3',
    }
    
    # Parse pages
    protocols = {}
    
    for p in pages:
        if p['page'] < 6:
            continue
        text = p['text'].strip()
        if not text:
            continue
        
        # Skip section dividers
        if re.match(r'^SECTION \d+', text) and len(text) < 300:
            continue
        if text.startswith('APPENDICES') and len(text) < 200:
            continue
        
        # Check manual override first
        if p['page'] in manual_map:
            pid = manual_map[p['page']]
            if pid is None:
                continue
        else:
            pid = find_protocol_id(text, p['page'])
            if not pid:
                continue
            # Skip false positives
            if not pid or pid not in valid_ids:
                continue
        
        if pid in protocols:
            protocols[pid]['content'] += '\n\n' + text
            protocols[pid]['pages'].append(p['page'])
        else:
            protocols[pid] = {
                'id': pid,
                'title': toc.get(pid, f'Protocol {pid}'),
                'content': text,
                'pages': [p['page']]
            }
    
    # Section mapping
    section_map = {
        '1': 'Section 1 – General Patient Care',
        '2': 'Section 2 – Medical Protocols',
        '3': 'Section 3 – Cardiac Emergencies',
        '4': 'Section 4 – Trauma Protocols',
        '5': 'Section 5 – Airway Protocols & Procedures',
        '6': 'Section 6 – Medical Director Options',
        '7': 'Section 7 – Medical Policies & Procedures',
        '8': 'Section 8 – Special Operations',
        'A': 'Appendices'
    }
    
    for pid, proto in protocols.items():
        if pid.startswith('A'):
            proto['section'] = 'Appendices'
            proto['section_num'] = 'A'
        else:
            sec = pid.split('.')[0]
            proto['section'] = section_map.get(sec, f'Section {sec}')
            proto['section_num'] = sec
        
        content = proto['content']
        levels = []
        if 'FIRST RESPONDER' in content:
            levels.append('FR')
        if re.search(r'\bEMT\b.*STANDING|EMT/ADVANCED', content):
            levels.append('E')
        if 'ADVANCED EMT' in content or 'AEMT' in content:
            levels.append('A')
        if 'PARAMEDIC' in content:
            levels.append('P')
        proto['provider_levels'] = levels if levels else ['ALL']
    
    # Sort
    def sort_key(item):
        pid = item[0]
        if pid.startswith('A'):
            return (99, 0, '', pid)
        base = pid.rstrip('AP')
        suffix = pid[len(base):]
        parts = base.split('.')
        try:
            return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0, suffix, pid)
        except ValueError:
            return (99, 0, '', pid)
    
    sorted_protocols = dict(sorted(protocols.items(), key=sort_key))
    
    with open('protocols_parsed.json', 'w') as f:
        json.dump(sorted_protocols, f, indent=2)
    
    print(f"Parsed {len(sorted_protocols)} protocols")
    missing = valid_ids - set(sorted_protocols.keys())
    if missing:
        print(f"Missing from TOC: {sorted(missing)}")
    for pid, proto in sorted_protocols.items():
        print(f"  {pid}: {proto['title'][:60]} [{','.join(proto['provider_levels'])}] pg {proto['pages']}")
    
    return sorted_protocols

if __name__ == '__main__':
    parse_protocols()
