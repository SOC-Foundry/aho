import enum
import re
from pathlib import Path

class LayoutVariant(enum.Enum):
    W_BASED = "w_based"          # W0, W1, ... workstreams
    SECTION_BASED = "section_based"  # §1, §2, ... sections (template)

def detect_layout(doc_path: Path) -> LayoutVariant:
    if not doc_path.exists():
        return LayoutVariant.SECTION_BASED # Default
        
    try:
        content = doc_path.read_text()
        
        # Check for W-based markers
        w_matches = re.findall(r'^#{2,3}\s+W[0-6]\s+—', content, re.MULTILINE)
        if len(w_matches) >= 3:
            return LayoutVariant.W_BASED
            
        # Check for section-based markers
        s_matches = re.findall(r'^#{2,3}\s+§[0-9]+', content, re.MULTILINE)
        if len(s_matches) >= 10:
            return LayoutVariant.SECTION_BASED
            
        # Fallback based on majority or just default
        if len(w_matches) > len(s_matches):
            return LayoutVariant.W_BASED
        return LayoutVariant.SECTION_BASED
    except Exception:
        return LayoutVariant.SECTION_BASED
