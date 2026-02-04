import requests
import logging
from .config import BUILTWITH_API_KEY

def search_builtwith(keyword, technology="Shopify", limit=10):
    """
    Search for websites using specific technology via BuiltWith API.
    Free tier: 50 lookups/month
    """
    if not BUILTWITH_API_KEY:
        logging.warning("BuiltWith API key not configured")
        return []
    
    api_url = "https://api.builtwith.com/v20/api.json"
    params = {
        "KEY": BUILTWITH_API_KEY,
        "LOOKUP": keyword,
        "Tech": technology
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = []
        domains = data.get("Results", [])[:limit]
        
        for domain_info in domains:
            domain = domain_info.get("Domain")
            if domain:
                results.append({
                    "title": domain.replace(".com", "").replace("-", " ").title(),
                    "link": f"https://{domain}",
                    "snippet": f"E-commerce store powered by {technology}",
                    "market": "USA",
                    "keyword": keyword
                })
        
        logging.info(f"BuiltWith found {len(results)} {technology} stores for '{keyword}'")
        return results
        
    except Exception as e:
        logging.error(f"BuiltWith API error: {e}")
        return []

def discover_shopify_stores(keyword, limit=10):
    """Wrapper for Shopify stores specifically."""
    return search_builtwith(keyword, "Shopify", limit)

def discover_woocommerce_stores(keyword, limit=10):
    """Wrapper for WooCommerce stores."""
    return search_builtwith(keyword, "WooCommerce", limit)
