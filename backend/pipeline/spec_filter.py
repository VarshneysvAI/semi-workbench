"""
SEMI — Smart Source Text Filtering

Filters raw scraped text to extract only specification-dense content
before sending to NIM. This prevents NIM overload by reducing
30,000+ char pages down to dense 2,000-4,000 char spec snippets.
"""
import re
from backend.pipeline.logger_setup import logger


# Units and patterns that indicate specification content
SPEC_UNITS = re.compile(
    r'\b('
    r'[Vv]olts?|[Vv]|[Ww]atts?|[Ww]|[Aa]mps?|[Aa]|[Hh][Zz]|'
    r'[Mm][Mm]|[Cc][Mm]|[Ii][Nn]\.?|[Ff][Tt]\.?|[Mm]eters?|'
    r'[Kk][Gg]|[Ll][Bb][Ss]?\.?|[Oo][Zz]\.?|[Gg]rams?|'
    r'[Pp][Ss][Ii]|[Bb][Aa][Rr]|[Gg][Pp][Mm]|[Cc][Ff][Mm]|'
    r'[Rr][Pp][Mm]|[Dd][Bb][Aa]?|[Bb][Tt][Uu]|[Gg][Aa][Ll]\.?|'
    r'[Ll]iters?|[Qq]uarts?|'
    r'°[CF]|[Ff]ahrenheit|[Cc]elsius|'
    r'UNSPSC|UPC|EAN|GTIN|'
    r'[Xx]\s*\d|[Hh]\s*[Xx]\s*[Ww]\s*[Xx]\s*[Dd]'
    r')\b',
    re.IGNORECASE
)

SPEC_SEPARATORS = re.compile(r'[:\|=\t]')

SPEC_SECTION_HEADERS = re.compile(
    r'(specification|technical|feature|dimension|detail|'
    r'product\s+data|physical|electrical|mechanical|'
    r'performance|compliance|standard|approval|'
    r'material|construction|package|shipping|'
    r'weight|warranty|certif)',
    re.IGNORECASE
)


def filter_spec_lines(raw_text: str, max_chars: int = 4000) -> str:
    """
    Filters raw scraped text to extract specification-dense lines.
    
    Strategy:
    1. Split text into lines
    2. Score each line for spec relevance (units, key-value separators, numbers)
    3. Keep high-scoring lines + surrounding context
    4. Return a dense spec snippet under max_chars
    """
    if not raw_text or len(raw_text.strip()) < 50:
        return raw_text or ""
    
    lines = raw_text.split('\n')
    scored_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 5:
            continue
        
        score = 0
        
        # Lines with units get high score
        unit_matches = SPEC_UNITS.findall(line)
        score += len(unit_matches) * 3
        
        # Lines with key-value separators (colon, pipe, equals)
        if SPEC_SEPARATORS.search(line):
            score += 2
        
        # Lines with numbers
        numbers = re.findall(r'\d+\.?\d*', line)
        score += min(len(numbers), 3)
        
        # Section headers get bonus
        if SPEC_SECTION_HEADERS.search(line):
            score += 5
        
        # Very long lines (paragraphs) get penalized — we want table rows
        if len(line) > 300:
            score -= 2
        
        # Very short lines with a colon are likely spec entries
        if len(line) < 100 and ':' in line:
            score += 2
        
        scored_lines.append((score, i, line))
    
    # Sort by score descending, keep top lines
    scored_lines.sort(key=lambda x: x[0], reverse=True)
    
    # Collect lines up to max_chars budget
    result_lines = []
    char_count = 0
    
    # Always include section headers and top-scoring lines
    for score, idx, line in scored_lines:
        if score <= 0:
            break
        if char_count + len(line) + 1 > max_chars:
            break
        result_lines.append((idx, line))
        char_count += len(line) + 1
    
    # Sort by original position to preserve reading order
    result_lines.sort(key=lambda x: x[0])
    
    filtered = '\n'.join(line for _, line in result_lines)
    
    if len(filtered.strip()) < 100:
        # Fallback: if filtering was too aggressive, return first max_chars of original
        logger.warning("Spec filter too aggressive, falling back to raw truncation")
        return raw_text[:max_chars]
    
    logger.info(f"SPEC_FILTER: {len(raw_text)} chars -> {len(filtered)} chars ({len(result_lines)} spec lines)")
    return filtered


def extract_product_header(raw_text: str, max_chars: int = 3000) -> str:
    """
    Extracts the product title/description area (top of the page)
    for Pass 1 (Identity & Taxonomy extraction).
    """
    if not raw_text:
        return ""
    
    lines = raw_text.split('\n')
    header_lines = []
    char_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if char_count + len(line) + 1 > max_chars:
            break
        header_lines.append(line)
        char_count += len(line) + 1
    
    return '\n'.join(header_lines)
