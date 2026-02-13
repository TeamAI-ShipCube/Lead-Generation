from googleapiclient.discovery import build
import logging
import random
from .config import GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CX_COMPANIES
import time
import threading
GOOGLE_LOCK = threading.Lock()

# 1. GLOBAL FILTERS
NOISE_SITES = [
    "scribd.com", "slideshare.net", "facebook.com", 
    "instagram.com", "yelp.com", 
    "pdfcoffee.com", "coursehero.com", "issuu.com", "pinterest.com"
]
EXCLUSIONS = " ".join([f"-site:{site}" for site in NOISE_SITES])
TLD_PRIORITY = "(site:.com | site:.io | site:.co | site:.net)"

def search_companies(keyword, market="USA", is_enrichment=False):
    """
    Executes a Google Custom Search with strict type checking to avoid string index errors.
    """

    if is_enrichment:
        query = f'"{keyword}" official website {EXCLUSIONS} {TLD_PRIORITY}'
        logging.info(f"🎯 Enrichment Search: {query}")
    else:
        if market == "USA":
            query = (
                f'"{keyword}" ("add to cart" OR "checkout" OR "cart" OR "basket") '
                f'{EXCLUSIONS} -inurl:blog -inurl:news -inurl:article -site:wikipedia.org '
                '-site:amazon.com -site:ebay.com -site:etsy.com '
                '-site:tiktok.com -site:youtube.com'
            )
        elif market == "UAE":
            query = (
                f'site:.ae "{keyword}" ("add to cart" OR "powered by shopify" OR "delivery") '
                f'{EXCLUSIONS} -inurl:blog -inurl:news -site:amazon.ae -site:noon.com'
            )
        else:
            logging.error(f"Unknown market: {market}")
            return []
        logging.info(f"🔍 Discovery Search: {query}")

    try:
        with GOOGLE_LOCK:
            service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
            time.sleep(1.0)
            res = service.cse().list(
                q=query,
                cx=GOOGLE_SEARCH_CX_COMPANIES,
                num=10
            ).execute()
            items = res.get('items', [])
        
        # SAFETY CHECK: Ensure items is a list of dictionaries
        if not isinstance(items, list):
            logging.warning(f"Expected list from Google API, got {type(items)}")
            return []

        companies = []
        for item in items:
            if isinstance(item, dict):  # Avoid the 'string indices must be integers' crash
                companies.append({
                    "title": item.get('title', 'No Title'),
                    "link": item.get('link', ''),
                    "snippet": item.get('snippet', ''),
                    "market": market,
                    "keyword": keyword
                })
        return companies

    except Exception as e:
        logging.error(f"Google Search failed: {e}")
        return []

def search_shopify_stores_broad(market="USA", limit=10, start_index=None):
    if start_index is None:
        start_index = random.randint(1, 50)
    
    if market == "USA":
        query = (
            f'site:.com "powered by shopify" ("add to cart" OR "shop now") '
            f'{EXCLUSIONS} -site:myshopify.com -inurl:blog -inurl:news '
            '-site:amazon.com -site:ebay.com -site:etsy.com '
            '-site:pinterest.com -site:tiktok.com -site:youtube.com'
        )
    elif market == "UAE":
        query = (
            f'site:.ae "powered by shopify" ("add to cart" OR "checkout") '
            f'{EXCLUSIONS} -inurl:blog -inurl:news'
        )
    else:
        return []

    logging.info(f"Broad Shopify search (start={start_index}): {query}")

    try:
        with GOOGLE_LOCK:
            service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
            time.sleep(1.0)
            res = service.cse().list(
                q=query,
                cx=GOOGLE_SEARCH_CX_COMPANIES,
                num=limit,
                start=start_index
            ).execute()
            items = res.get('items', [])

        if not isinstance(items, list):
            return []

        return [{
            "title": item.get('title', 'No Title'),
            "link": item.get('link', ''),
            "snippet": item.get('snippet', ''),
            "market": market,
            "keyword": "Broad Shopify Discovery"
        } for item in items if isinstance(item, dict)]

    except Exception as e:
        logging.error(f"Broad Shopify search failed: {e}")
        return []

def search_with_keywords_shuffled(keywords, market="USA", limit_per_keyword=5):
    shuffled_keywords = keywords.copy()
    random.shuffle(shuffled_keywords)
    
    all_companies = []
    for keyword in shuffled_keywords[:20]:
        if len(all_companies) >= 100:
            break
        
        query = f'"{keyword}" ("add to cart" OR "checkout" OR "shop now") {EXCLUSIONS} -inurl:blog'
        logging.info(f"Keyword search: {query}")
        
        try:
            with GOOGLE_LOCK:
                service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
                time.sleep(1.0)
                res = service.cse().list(
                    q=query,
                    cx=GOOGLE_SEARCH_CX_COMPANIES,
                    num=limit_per_keyword
                ).execute()
                items = res.get('items', [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            all_companies.append({
                                "title": item.get('title', 'No Title'),
                                "link": item.get('link', ''),
                                "snippet": item.get('snippet', ''),
                                "market": market,
                                "keyword": keyword
                            })
        except Exception as e:
            logging.warning(f"Search failed for keyword '{keyword}': {e}")
            continue
    return all_companies