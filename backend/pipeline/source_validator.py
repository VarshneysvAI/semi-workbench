"""
SEMI — Source Validator (Updated)

Scores and selects the best source URLs for data extraction.
Now supports:
  - PDF spec sheets (previously blacklisted)
  - Dual-source selection (manufacturer + distributor)
  - Industrial distributor sources for UPC/dimensions data
"""
from backend.pipeline.logger_setup import logger


# Domains that are pure retail / social — never useful for spec data
HARD_BLACKLIST = [
    "amazon", "ebay", "walmart", "aliexpress", "alibaba",
    "etsy", "facebook", "instagram", "pinterest", "youtube",
    "reddit", "quora", "twitter", "tiktok"
]

# Industrial distributors — useful for UPC/dimensions but lower priority than MFR
DISTRIBUTOR_DOMAINS = [
    "grainger", "mcmaster", "zoro", "mscdirect", "fastenal",
    "homedepot", "lowes", "acehardware", "supplyline", 
    "globalindustrial", "uline", "motion", "automationdirect"
]


def score_source_url(url: str, title: str, manufacturer: str) -> int:
    """Score a URL for data extraction quality. Higher = better."""
    score = 0
    url_lower = url.lower()
    title_lower = title.lower()
    mfr_clean = manufacturer.lower().replace(" ", "").replace("inc", "").replace("corp", "").replace("llc", "").replace("/", "")

    # Hard blacklist — these never have spec data
    if any(domain in url_lower for domain in HARD_BLACKLIST):
        return -1000

    # PDF spec sheets get a BONUS (they are gold for technical specs)
    if url_lower.endswith(".pdf"):
        score += 30

    # Manufacturer's own domain gets highest priority
    if mfr_clean and len(mfr_clean) > 2 and mfr_clean in url_lower:
        score += 50

    # Spec-related keywords in URL or title
    spec_keywords = [
        "spec", "specification", "datasheet", "data-sheet", "technical",
        "product", "catalog", "documentation", "manual", "support"
    ]
    if any(kw in url_lower or kw in title_lower for kw in spec_keywords):
        score += 40

    # Distributor domains — useful but lower priority
    if any(domain in url_lower for domain in DISTRIBUTOR_DOMAINS):
        score += 10  # Still positive — we want these as secondary sources

    # Bad content signals
    bad_keywords = [
        "forum", "blog", "news", "careers", "contact", "login",
        "account", "review", "repair", "repairclinic", "partselect",
        "appliancepartspros"
    ]
    if any(kw in url_lower for kw in bad_keywords):
        score -= 50

    return score


def is_distributor_url(url: str) -> bool:
    """Check if a URL belongs to an industrial distributor."""
    url_lower = url.lower()
    return any(domain in url_lower for domain in DISTRIBUTOR_DOMAINS)


def select_sources(candidate_results, manufacturer):
    """
    Select sources for extraction.
    Returns: (best_source, ref_urls)
    
    The best_source is the highest-scored non-distributor URL.
    """
    scored = []
    for r in candidate_results:
        s = score_source_url(r.url, r.title, manufacturer)
        if s >= 0:
            scored.append((s, r))
        else:
            logger.info(f"SOURCE_REJECTED: {r.url}")
            
    scored.sort(key=lambda x: x[0], reverse=True)
    
    if not scored:
        return None, []
        
    selected = scored[0][1]
    references = [x[1].url for x in scored[1:6]]
    logger.info(f"SOURCE_SELECTED: {selected.url} (Score: {scored[0][0]})")
    
    return selected, references


def select_dual_sources(candidate_results, manufacturer):
    """
    Select TWO sources for extraction:
      - Source A: Best manufacturer/spec URL
      - Source B: Best distributor URL (for UPC, dimensions, packaging)
    
    Returns: (source_a, source_b, ref_urls)
    """
    scored = []
    for r in candidate_results:
        s = score_source_url(r.url, r.title, manufacturer)
        if s >= 0:
            scored.append((s, r))
        else:
            logger.info(f"SOURCE_REJECTED: {r.url}")
    
    scored.sort(key=lambda x: x[0], reverse=True)
    
    if not scored:
        return None, None, []
    
    source_a = scored[0][1]
    source_b = None
    references = []
    
    # Find the best secondary source (ideally a distributor if primary is MFR, or vice versa)
    primary_is_distributor = is_distributor_url(source_a.url)
    
    for score, result in scored[1:]:
        if source_b is None:
            this_is_distributor = is_distributor_url(result.url)
            # Pick a source that complements the primary
            if primary_is_distributor != this_is_distributor:
                source_b = result
                logger.info(f"SOURCE_B_SELECTED: {result.url} (Score: {score})")
                continue
        references.append(result.url)
        if len(references) >= 5:
            break
    
    # If no complementary source found, take the second-best regardless
    if source_b is None and len(scored) > 1:
        source_b = scored[1][1]
        logger.info(f"SOURCE_B_SELECTED (same type): {source_b.url}")
    
    logger.info(f"SOURCE_A_SELECTED: {source_a.url} (Score: {scored[0][0]})")
    
    return source_a, source_b, references[:5]
