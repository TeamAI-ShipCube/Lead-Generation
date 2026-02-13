import requests
import logging
import re
from urllib.parse import urlparse
from .config import GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CX_PEOPLE
from googleapiclient.discovery import build

BAD_DOMAIN_KEYWORDS = [
    "godaddy",
    "sedo",
    "dan.com",
    "parking",
    "domains",
    "registry"
]
def is_valid_linkedin_url(url):
    """Validate LinkedIn profile URL structure only."""
    if not url:
        return False

    try:
        parsed = urlparse(url)

        if "linkedin.com" not in parsed.netloc.lower():
            return False

        if "/in/" not in parsed.path.lower():
            return False

        if "/company/" in parsed.path.lower():
            return False

        bad_paths = ["/posts/", "/feed/", "/pulse/", "/events/", "/directory/"]
        if any(p in parsed.path.lower() for p in bad_paths):
            return False

        return True

    except:
        return False

def is_valid_company_url(url):
    """
    Validates that a company URL is accessible and not a spam/placeholder.
    """
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        
        # Must have a scheme (http/https)
        if not parsed.scheme:
            return False
        
        # Must have a valid domain
        if not parsed.netloc or '.' not in parsed.netloc:
            return False
        
        # Exclude obvious spam/placeholder domains
        spam_keywords = ['example.com', 'test.com', 'placeholder', 'localhost']
        if any(spam in parsed.netloc.lower() for spam in spam_keywords):
            return False
        
        return True
        
    except Exception as e:
        logging.error(f"Error validating company URL {url}: {e}")
        return False

def get_domain_from_url(url):
    """Extract clean domain from URL."""
    domain = urlparse(url).netloc.replace("www.", "")
    return domain


def is_valid_name(name):
    """Ensure name is realistic person name."""
    if not name or len(name.split()) < 2:
        return False

    if len(name.split()) > 4:
        return False

    invalid_keywords = [
        "linkedin", "company", "team", "staff",
        "executives", "profile", "member"
    ]

    name_lower = name.lower()
    if any(word in name_lower for word in invalid_keywords):
        return False

    return True

def execute_search_strategy(service, query, domain, strategy_name):
    """Helper to execute a single search strategy and process results."""
    logging.info(f"Strategy [{strategy_name}]: {query}")
    
    try:
        res = service.cse().list(q=query, cx=GOOGLE_SEARCH_CX_PEOPLE, num=3).execute()
        items = res.get('items', [])
        
        if not items:
            return None

        # Check items
        for item in items:
            title_snippet = item.get('title', '')
            linkedin_url = item.get('link')
            
            # Parse name from snippet title: "Name - Title | Company"
            parts = re.split(r' [-|] ', title_snippet)
            name = parts[0].strip() if parts else "Unknown"
            
            # Clean suffixes
            name = name.replace(' | LinkedIn', '').replace('LinkedIn', '').strip()
            
            # Validate name 
            if not is_valid_name(name):
                logging.info(f"Strategy [{strategy_name}] skipped vague name: {name}")
                continue
            
            # 3. Validate LinkedIn URL (with benefit of doubt/snippet trust)
            if not linkedin_url or not is_valid_linkedin_url(linkedin_url):
                logging.info(f"Strategy [{strategy_name}] skipped invalid URL/Name mismatch: {name}")
                continue
                
            # If we get here, we found a valid candidate!
            job_title = parts[1].strip() if len(parts) > 1 else "Founder"
            
            name_parts = name.split(' ')
            first_name = name_parts[0]
            last_name = name_parts[-1] if len(name_parts) > 1 else ""
            
            logging.info(f"✓ Strategy [{strategy_name}] success: {name} ({job_title})")
            
            return {
                "first_name": first_name,
                "last_name": last_name,
                "title": job_title,
                "email": None,
                "linkedin_url": linkedin_url
            }
            
    except Exception as e:
        logging.error(f"Error in strategy [{strategy_name}]: {e}")
        return None
        
    return None

def search_with_linkedin_xray_by_domain(domain):

    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX_PEOPLE:
        return None

    service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)

    company_token = domain.split(".")[0]

    strategies = [

        # Executive
        (f'site:linkedin.com/in "{company_token}" (Founder OR CEO OR Owner OR Principal)', "Exec"),

        # Ops
        (f'site:linkedin.com/in "{company_token}" ("Head of Operations" OR Logistics OR "Supply Chain")', "Ops"),

        # Senior fallback
        (f'site:linkedin.com/in "{company_token}" (Director OR VP)', "Senior")
    ]

    for query, label in strategies:

        logging.info(f"🔎 LinkedIn Strategy [{label}] → {query}")

        try:
            res = service.cse().list(
                q=query,
                cx=GOOGLE_SEARCH_CX_PEOPLE,
                num=5
            ).execute()

            items = res.get("items", [])

            for item in items:
                parsed = parse_linkedin_result(item, expected_company=company_token)
                if parsed:
                    logging.info(f"✓ Strategy [{label}] success: {parsed['first_name']} {parsed['last_name']}")
                    return parsed

        except Exception as e:
            logging.warning(f"Strategy {label} failed: {e}")

    return None

from .intelligence import clean_name_with_vertex

def search_decision_maker(company_name, company_url=None):
    """
    Decision maker search using LinkedIn X-Ray by domain (free).
    Falls back to cleaned company name search if no URL provided.
    """
    # 1. Try by Domain (Best)
    domain = None
    if company_url:
        domain = get_domain_from_url(company_url)
    
    if domain:
        logging.info(f"Searching LinkedIn for domain: {domain}")
        dm_info = search_with_linkedin_xray_by_domain(domain)
        if dm_info:
            logging.info(f"✓ LinkedIn X-Ray (Domain) success: {dm_info.get('first_name')} {dm_info.get('last_name')}")
            return dm_info
    
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX_PEOPLE:
        return None
        
    service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)

    # 2. Try by Provided Company Name (Already Cleaned)
    if company_name and len(company_name) > 2 and company_name.lower() != "home":
        logging.info(f"Trying LinkedIn X-Ray by Name: {company_name}")
        query = f'site:linkedin.com/in "{company_name}" (Founder OR CEO OR "Head of Operations")'
        
        try:
            res = service.cse().list(q=query, cx=GOOGLE_SEARCH_CX_PEOPLE, num=1).execute()
            items = res.get('items', [])
            
            if items:
                best_candidate = items[0]
                dm_info = parse_linkedin_result(best_candidate) 
                if dm_info:
                     logging.info(f"✓ LinkedIn X-Ray (Name) success: {dm_info.get('first_name')}")
                     return dm_info
            
            # 2b. Broader Fallback (If Founder/CEO search fails)
            logging.info(f"Primary name search failed for {company_name}. Trying broader roles (Director, Manager)...")
            query_broad = f'site:linkedin.com/in "{company_name}" (Director OR Manager OR VP OR Owner)'

            res_broad = service.cse().list(q=query_broad, cx=GOOGLE_SEARCH_CX_PEOPLE, num=1).execute()
            items_broad = res_broad.get('items', [])
            if items_broad:
                 dm_info = parse_linkedin_result(items_broad[0])
                 if dm_info:
                     logging.info(f"✓ LinkedIn X-Ray (Broader) success: {dm_info.get('first_name')} ({dm_info.get('title')})")
                     return dm_info
                     
        except Exception as e:
            logging.warning(f"name search failed: {e}")

    # 3. Try by Domain-Derived Name (Fallback)
    if domain:
        derived_name = domain.split('.')[0].replace('-', ' ').title()
        if derived_name and derived_name.lower() != company_name.lower():
             logging.info(f"Trying LinkedIn X-Ray by Domain Name: {derived_name}")
             query = f'"{derived_name}" (Founder OR CEO OR "Head of Operations")'
             try:
                res = service.cse().list(q=query, cx=GOOGLE_SEARCH_CX_PEOPLE, num=1).execute()
                items = res.get('items', [])
                if items:
                    best_candidate = items[0]
                    dm_info = parse_linkedin_result(best_candidate) 
                    if dm_info:
                        logging.info(f"✓ LinkedIn X-Ray (Derived) success: {dm_info.get('first_name')}")
                        return dm_info
             except Exception as e:
                pass

    return None

def parse_linkedin_result(item, expected_company=None):
    """
    Strict LinkedIn result parsing with identity validation.
    """

    try:
        title_snippet = item.get("title", "")
        link = item.get("link")
        snippet = item.get("snippet", "").lower()

        if not is_valid_linkedin_url(link):
            return None

        parts = re.split(r"[-|]", title_snippet)
        name = parts[0].replace("LinkedIn", "").strip()

        if not is_valid_name(name):
            return None

        # 🔥 STRICT COMPANY MATCH
        if expected_company:
            company_clean = expected_company.lower().split()[0]

            title_match = company_clean in title_snippet.lower()
            snippet_match = company_clean in snippet

            if not (title_match or snippet_match):
                logging.warning(
                    f"❌ LinkedIn mismatch: {name} not tied to {expected_company}"
                )
                return None

        job_title = parts[1].strip() if len(parts) > 1 else "Founder"

        name_parts = name.split()
        first_name = name_parts[0]
        last_name = name_parts[-1] if len(name_parts) > 1 else ""

        return {
            "first_name": first_name,
            "last_name": last_name,
            "title": job_title,
            "email": None,
            "linkedin_url": link
        }

    except Exception as e:
        logging.warning(f"LinkedIn parse failed: {e}")
        return None


def search_person_linkedin(first_name=None, last_name=None, company=None, broad_search=False):

    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX_PEOPLE:
        return None

    service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)

    queries = []

    # Exact search (person mode)
    if first_name and last_name:
        queries.append(
            f'site:linkedin.com/in "{first_name} {last_name}" "{company}"'
        )

    # Broad search (company mode)
    if broad_search and company:
        queries.append(
            f'site:linkedin.com/in "{company}" (Founder OR CEO OR Owner OR Director OR VP)'
        )

    for query in queries:

        logging.info(f"🔎 Person LinkedIn search: {query}")

        try:
            res = service.cse().list(
                q=query,
                cx=GOOGLE_SEARCH_CX_PEOPLE,
                num=5
            ).execute()

            items = res.get("items", [])

            for item in items:
                parsed = parse_linkedin_result(item, expected_company=company)
                if parsed:
                    return parsed

        except Exception as e:
            logging.warning(f"LinkedIn search failed: {e}")

    return None