from backend.pipeline.logger_setup import logger

def score_source_url(url: str, title: str, manufacturer: str) -> int:
    score = 0
    url_lower = url.lower()
    title_lower = title.lower()
    mfr_clean = manufacturer.lower().replace(" ", "").replace("inc", "").replace("corp", "").replace("llc", "")

    blacklist = ["amazon", "ebay", "walmart", "homedepot", "lowes", 
                 "aliexpress", "alibaba", "etsy", "facebook", "instagram", 
                 "pinterest", "youtube", "reddit", "quora", "grainger", 
                 "zoro", "repairclinic", "partselect", "appliancepartspros", "supplyline"]
                 
    if any(domain in url_lower for domain in blacklist):
        return -1000

    if url_lower.endswith(".pdf"):
        return -1000 # Aggressively reject PDFs as requested to protect compute

    good_keywords = ["spec", "specification", "manual", "data-sheet", "datasheet", "support", "product", "documentation", "owner", "catalog", "installation", "technical", "pdf"]
    if any(kw in url_lower or kw in title_lower for kw in good_keywords):
        score += 50

    if mfr_clean and mfr_clean in url_lower:
        score += 40

    bad_keywords = ["forum", "reddit", "quora", "repair", "review", "blog", "news", "careers", "contact", "login", "account"]
    if any(kw in url_lower for kw in bad_keywords):
        score -= 50

    return score

def select_sources(candidate_results, manufacturer):
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

