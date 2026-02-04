import requests
import logging
import re
from urllib.parse import urlparse
from .config import GOOGLE_SEARCH_API_KEY, GOOGLE_SEARCH_CX_PEOPLE
from googleapiclient.discovery import build

def is_valid_linkedin_url(url, person_name=None):
    """
    DEEP validation of LinkedIn URL:
    1. Checks URL format
    2. Verifies page is accessible (200 status)
    3. Confirms content indicates it's a profile page
    4. Optionally verifies person's name appears on the page
    """
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        
        # Step 1: URL Format Validation
        # Must be linkedin.com domain
        if 'linkedin.com' not in parsed.netloc.lower():
            return False
        
        # Must have /in/ path (profile URL)
        if '/in/' not in parsed.path.lower():
            return False
        
        # Must not be a company page
        if '/company/' in parsed.path.lower():
            logging.warning(f"LinkedIn URL is a company page, not a profile: {url}")
            return False
        
        # Must not be a directory/search page
        invalid_paths = ['/directory/', '/search/', '/pub/dir/', '/learning/', '/404']
        if any(path in parsed.path.lower() for path in invalid_paths):
            return False
        
        # Step 2: Content Validation (verify page exists and is legit)
        try:
            # Use Jina AI to quickly fetch LinkedIn page (bypasses login wall)
            jina_url = f"https://r.jina.ai/{url}"
            headers = {
                "X-Return-Format": "text",
                "User-Agent": "Mozilla/5.0 (compatible; LeadBot/1.0)"
            }
            
            response = requests.get(jina_url, headers=headers, timeout=10)
            
            # Check if page is accessible
            if response.status_code != 200:
                logging.warning(f"LinkedIn URL returned {response.status_code}: {url}")
                return False
            
            page_text = response.text.lower()
            
            # Step 3: Verify it's actually a profile page (not 404 or error)
            # LinkedIn profiles have these indicators
            profile_indicators = ['linkedin', 'profile', 'experience', 'education']
            
            # Must have at least 2 profile indicators
            indicator_count = sum(1 for indicator in profile_indicators if indicator in page_text)
            
            if indicator_count < 2:
                logging.warning(f"LinkedIn URL rejected (low confidence/login wall): {url} (Indicators: {indicator_count})")
                return False
            
            # Step 4: Verify person's name appears (if provided)
            # RELAXED: Require at least 1 part match (first OR last) instead of 2 to handle nicknames/variations
            if person_name:
                name_parts = person_name.lower().split()
                
                # Check for matches
                name_matches = sum(1 for part in name_parts if len(part) > 2 and part in page_text)
                
                # Validation: At least 1 part must match (e.g. "John" found in "John Smith")
                # This catches "Wrong Person" but allows "Jon" vs "Jonathan" if last name matches
                if name_matches < 1:
                     logging.warning(f"LinkedIn rejection: Name '{person_name}' not found content of {url}")
                     return False
            
            logging.info(f"✓ LinkedIn URL validated: {url}")
            return True
            
        except requests.exceptions.Timeout:
            logging.warning(f"LinkedIn URL validation timeout: {url} - ALLOWING (Benefit of Doubt)")
            return True
            
        except Exception as e:
            logging.warning(f"LinkedIn URL content check failed: {url} - {e} - ALLOWING (Benefit of Doubt)")
            return True
        
    except Exception as e:
        logging.error(f"Error validating LinkedIn URL {url}: {e}")
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
    """
    Validate if a name is specific enough (not vague like 'Executives ...' or company names).
    """
    if not name or len(name) < 3:
        return False
    
    # Reject vague/generic names
    vague_keywords = [
        'executives', 'team', 'staff', 'member', '...', 'professional', 'profile',
        'linkedin', 'company', 'corporation', 'inc', 'llc', 'ltd',
        'cookies', 'sweets', 'shop', 'store', 'bakery',  # Common business words
        'and', '&', 'associates'
    ]
    name_lower = name.lower()
    
    # Check if name contains any vague keywords
    if any(keyword in name_lower for keyword in vague_keywords):
        return False
    
    # Reject if name has more than 4 words (likely a title/description)
    if len(name.split()) > 4:
        return False
    
    # Reject single-word names (likely company names)
    if len(name.split()) == 1:
        return False
    
    # Check if name has proper format (First Last or First Middle Last)
    words = name.split()
    if len(words) < 2:
        return False
    
    # Reject if first or last name is too short (likely initials or abbreviations)
    if len(words[0]) < 2 or len(words[-1]) < 2:
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
            if not linkedin_url or not is_valid_linkedin_url(linkedin_url, person_name=name):
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
    """
    Multi-Strategy LinkedIn X-Ray search by domain.
    Tries 3 distinct queries to maximize chances of finding a POC.
    """
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_CX_PEOPLE:
        return None
        
    service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
    
    # Define Strategies
    strategies = [
        # Strategy 1: Broad Leadership (Founders/Owners are best for SMBs)
        (f'{domain} (Founder OR CEO OR Owner OR Principal)', "Exec Leadership"),
        
        # Strategy 2: Ops & Logistics (CRITICAL for shipping deals)
        (f'{domain} ("Head of Operations" OR "Director of Operations" OR "Logistics Manager" OR "Supply Chain Director" OR "Warehouse Manager")', "Logistics/Ops"),
        
        # Strategy 3: General Senior Mgmt (Fallback)
        (f'{domain} (Director OR VP OR "Vice President")', "Senior Mgmt")
    ]
    
    # Execute Strategies in order
    for query, name in strategies:
        result = execute_search_strategy(service, query, domain, name)
        if result:
            return result
            
    logging.warning(f"All search strategies failed for {domain}")
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
        query = f'"{company_name}" (Founder OR CEO OR "Head of Operations")'
        
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
            query_broad = f'"{company_name}" (Director OR Manager OR "Head of" OR VP OR Owner)'
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

def parse_linkedin_result(item):
    """Helper to parse a Google Custom Search Result for LinkedIn"""
    try:
        title_snippet = item.get('title', '')
        link = item.get('link')
        
        parts = re.split(r' [-|] ', title_snippet)
        name = parts[0].strip() if parts else "Unknown"
        name = name.replace(' | LinkedIn', '').replace('LinkedIn', '').strip()
        
        if not is_valid_name(name):
            return None
            
        job_title = parts[1].strip() if len(parts) > 1 else "Founder"
        
        name_parts = name.split(' ')
        first_name = name_parts[0]
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "title": job_title,
            "email": None,
            "linkedin_url": link
        }
    except:
        return None

