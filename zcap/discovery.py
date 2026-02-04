from googleapiclient.discovery import build
import logging
import random
from .config import GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CX_COMPANIES, GOOGLE_SEARCH_DAILY_LIMIT

def get_google_search_service():
    return build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)

def search_companies(keyword, market="USA"):
    """
    Executes a Google Custom Search to find Shopify/WooCommerce stores.
    """
    service = get_google_search_service()
    
    # Construct Query based on Market
    if market == "USA":
        # Search for storefronts, excluding blogs, marketplaces, and social media
        query = (
            f'"{keyword}" ("add to cart" OR "checkout" OR "cart" OR "basket") '
            '-inurl:blog -inurl:news -inurl:article -site:wikipedia.org '
            '-site:amazon.com -site:ebay.com -site:etsy.com -site:yelp.com '
            '-site:pinterest.com -site:facebook.com -site:linkedin.com '
            '-site:tiktok.com -site:instagram.com -site:youtube.com'
        )
    elif market == "UAE":
        query = (
            f'site:.ae "{keyword}" ("add to cart" OR "powered by shopify" OR "delivery") '
            '-inurl:blog -inurl:news -site:amazon.ae -site:noon.com'
        )
    else:
        logging.error(f"Unknown market: {market}")
        return []

    logging.info(f"Searching for companies with query: {query}")

    try:
        # Fetch 10 results (1 page)
        res = service.cse().list(q=query, cx=GOOGLE_SEARCH_CX_COMPANIES, num=10).execute()
        items = res.get('items', [])
        
        companies = []
        for item in items:
            company_data = {
                "title": item.get('title'),
                "link": item.get('link'),
                "snippet": item.get('snippet'),
                "market": market,
                "keyword": keyword
            }
            companies.append(company_data)
            
        return companies

    except Exception as e:
        logging.error(f"Google Search failed: {e}")
        return []

def search_shopify_stores_broad(market="USA", limit=10, start_index=None):
    """
    Broad search for ANY Shopify stores in a region (not keyword-specific).
    Uses randomized start index to get different results each run.
    """
    service = get_google_search_service()
    
    # Randomize start position for variety (Google allows start 1-91)
    if start_index is None:
        start_index = random.randint(1, 50)  # Random starting position
    
    if market == "USA":
        # Search for any US Shopify stores with active cart/checkout
        query = (
            'site:.com "powered by shopify" ("add to cart" OR "shop now") '
            '-site:myshopify.com -inurl:blog -inurl:news '
            '-site:amazon.com -site:ebay.com -site:etsy.com '
            '-site:tiktok.com -site:instagram.com -site:youtube.com'
        )
    elif market == "UAE":
        query = (
            'site:.ae "powered by shopify" ("add to cart" OR "checkout") '
            '-inurl:blog -inurl:news'
        )
    else:
        logging.error(f"Unknown market: {market}")
        return []

    logging.info(f"Broad Shopify search (start={start_index}): {query}")

    try:
        res = service.cse().list(
            q=query, 
            cx=GOOGLE_SEARCH_CX_COMPANIES, 
            num=limit,
            start=start_index
        ).execute()
        items = res.get('items', [])
        
        companies = []
        for item in items:
            company_data = {
                "title": item.get('title'),
                "link": item.get('link'),
                "snippet": item.get('snippet'),
                "market": market,
                "keyword": "Broad Shopify Discovery"
            }
            companies.append(company_data)
            
        logging.info(f"Broad search found {len(companies)} Shopify stores (from position {start_index})")
        return companies

    except Exception as e:
        logging.error(f"Broad Shopify search failed: {e}")
        return []

def search_with_keywords_shuffled(keywords, market="USA", limit_per_keyword=3):
    """
    Search using randomly shuffled keywords to get variety.
    Returns mixed results from different keywords.
    """
    service = get_google_search_service()
    
    # Shuffle keywords for randomness
    shuffled_keywords = keywords.copy()
    random.shuffle(shuffled_keywords)
    
    all_companies = []
    keywords_used = 0
    
    # Use first few keywords until we have enough companies
    for keyword in shuffled_keywords[:10]:  # Max 10 keywords per run
        if len(all_companies) >= 30:  # Generous buffer
            break
            
        query = f'"{keyword}" ("add to cart" OR "checkout") -inurl:blog -site:amazon.com -site:ebay.com'
        
        try:
            res = service.cse().list(
                q=query, 
                cx=GOOGLE_SEARCH_CX_COMPANIES, 
                num=limit_per_keyword
            ).execute()
            items = res.get('items', [])
            
            for item in items:
                company_data = {
                    "title": item.get('title'),
                    "link": item.get('link'),
                    "snippet": item.get('snippet'),
                    "market": market,
                    "keyword": keyword
                }
                all_companies.append(company_data)
            
            keywords_used += 1
            logging.info(f"Keyword '{keyword}' found {len(items)} companies")
            
        except Exception as e:
            logging.warning(f"Search failed for keyword '{keyword}': {e}")
            continue
    
    logging.info(f"Keyword search used {keywords_used} keywords, found {len(all_companies)} total companies")
    return all_companies
