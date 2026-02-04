import requests
import logging
import time
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from urllib.parse import urljoin, urlparse

def scrape_with_playwright_enhanced(url, scroll_for_dynamic=True):
    """
    Enhanced Playwright scraper for modern dynamic websites.
    - Handles lazy loading via scrolling
    - Waits for dynamic content
    - Extracts structured metadata
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Set viewport for consistent rendering
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Navigate with multiple wait strategies
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            # Wait for network to be mostly idle (handles lazy loading)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except:
                pass  # Continue even if networkidle times out
            
            # Additional wait for JS frameworks (React, Vue, etc.)
            time.sleep(1)
            
            # Scroll to load dynamic content (lazy loading)
            if scroll_for_dynamic:
                try:
                    page.evaluate("""
                        () => {
                            window.scrollTo(0, document.body.scrollHeight / 2);
                        }
                    """)
                    time.sleep(0.5)
                    page.evaluate("""
                        () => {
                            window.scrollTo(0, document.body.scrollHeight);
                        }
                    """)
                    time.sleep(0.5)
                except:
                    pass
            
            # Extract text content
            text = page.inner_text('body')
            
            # Try to extract structured metadata
            metadata = {}
            try:
                # Company size indicators
                employee_indicators = page.locator('text=/\\d+[\\+\\-]?\\s*(employees|team members|people)/i').all_text_contents()
                if employee_indicators:
                    metadata['employee_hint'] = employee_indicators[0]
                
                # Revenue indicators  
                revenue_indicators = page.locator('text=/\\$\\d+[MmBbKk]?\\s*(revenue|ARR|sales)/i').all_text_contents()
                if revenue_indicators:
                    metadata['revenue_hint'] = revenue_indicators[0]
            except:
                pass
            
            browser.close()
            
            if text and len(text) > 100:
                logging.info(f"✓ Playwright scraped: {len(text)} chars from {url}")
                return text[:15000], metadata  # Return text and metadata
            
            return None, {}
            
    except PlaywrightTimeout:
        logging.warning(f"Playwright timeout for {url}")
        return None, {}
    except Exception as e:
        logging.error(f"Playwright error for {url}: {e}")
        return None, {}

def scrape_with_playwright(url):
    """
    Wrapper for backwards compatibility.
    """
    text, _ = scrape_with_playwright_enhanced(url, scroll_for_dynamic=True)
    return text

def scrape_with_jina(url):
    """
    Scrapes a URL using Jina AI Reader (unlimited free fallback).
    """
    jina_url = f"https://r.jina.ai/{url}"
    headers = {
        "X-Return-Format": "text"
    }
    
    try:
        response = requests.get(jina_url, headers=headers, timeout=30)
        response.raise_for_status()
        text = response.text[:15000]
        
        if text and len(text) > 100:
            logging.info(f"✓ Jina AI scraped: {len(text)} chars from {url}")
            return text
        
        return None
        
    except Exception as e:
        logging.error(f"Jina AI error for {url}: {e}")
        return None

def scrape_website(url):
    """
    ENHANCED exhaustive scraping for modern dynamic websites.
    
    Traverses multiple pages for comprehensive data:
    1. Homepage (main content)
    2. About/Company pages (team size, mission, history)
    3. Press/News pages (recent updates, funding)
    4. Team pages (leadership info)
    5. Careers pages (hiring signals - growth indicator)
    6. Contact pages (for email finding)
    
    Uses both Playwright (dynamic) and Jina AI (fallback).
    """
    from urllib.parse import urljoin
    
    scraped_data = {
        "url": url,
        "text": "",
        "about_text": "",
        "team_text": "",
        "press_text": "",
        "careers_text": "",
        "metadata": {},
        "error": None
    }
    
    logging.info(f"🔍 Exhaustive scraping: {url}")
    
    # 1. HOMEPAGE - Primary content
    text, metadata = scrape_with_playwright_enhanced(url, scroll_for_dynamic=True)
    if text:
        scraped_data["text"] = text
        scraped_data["metadata"] = metadata
        logging.info(f"✓ Homepage: {len(text)} chars")
    else:
        logging.info(f"Playwright failed, trying Jina AI for homepage...")
        text = scrape_with_jina(url)
        if text:
            scraped_data["text"] = text
            logging.info(f"✓ Homepage (Jina): {len(text)} chars")
    
    # If homepage failed completely, return error
    if not scraped_data["text"]:
        scraped_data["error"] = "All scraping methods failed for homepage"
        logging.error(f"✗ Both scrapers failed for {url}")
        return scraped_data
    
    # 2. ABOUT PAGES - Company info, team size, mission
    about_paths = ['/about', '/about-us', '/our-story', '/company', '/who-we-are']
    about_found = False
    
    for path in about_paths[:3]:  # Try top 3 variations
        if about_found:
            break
        about_url = urljoin(url, path)
        logging.info(f"  → Trying: {path}")
        
        about_text, about_meta = scrape_with_playwright_enhanced(about_url, scroll_for_dynamic=False)
        if not about_text:
            about_text = scrape_with_jina(about_url)
        
        if about_text and len(about_text) > 200:
            scraped_data["about_text"] = about_text[:5000]
            scraped_data["metadata"].update(about_meta)
            logging.info(f"✓ About page: {len(about_text)} chars")
            about_found = True
    
    # 3. TEAM PAGES - Leadership, team size
    team_paths = ['/team', '/our-team', '/leadership', '/people']
    for path in team_paths[:2]:  # Try top 2
        team_url = urljoin(url, path)
        team_text, _ = scrape_with_playwright_enhanced(team_url, scroll_for_dynamic=False)
        if not team_text:
            team_text = scrape_with_jina(team_url)
        
        if team_text and len(team_text) > 200:
            scraped_data["team_text"] = team_text[:3000]
            logging.info(f"✓ Team page: {len(team_text)} chars")
            break
    
    # 4. PRESS/NEWS PAGES - Recent updates, funding announcements
    press_paths = ['/press', '/news', '/newsroom', '/media', '/blog']
    for path in press_paths[:2]:  # Try top 2
        press_url = urljoin(url, path)
        press_text = scrape_with_jina(press_url)  # Jina is faster for simple pages
        if not press_text:
            press_text, _ = scrape_with_playwright_enhanced(press_url, scroll_for_dynamic=False)
        
        if press_text and len(press_text) > 200:
            scraped_data["press_text"] = press_text[:3000]
            logging.info(f"✓ Press page: {len(press_text)} chars")
            break
    
    # 5. CAREERS PAGES - Hiring signals (growth indicator)
    careers_paths = ['/careers', '/jobs', '/join-us', '/join-our-team']
    for path in careers_paths[:2]:  # Try top 2
        careers_url = urljoin(url, path)
        careers_text = scrape_with_jina(careers_url)  # Fast scrape
        
        if careers_text and len(careers_text) > 100:
            scraped_data["careers_text"] = careers_text[:2000]
            logging.info(f"✓ Careers page: {len(careers_text)} chars")
            break
    
    # Summary
    total_chars = (len(scraped_data.get("text", "")) + 
                   len(scraped_data.get("about_text", "")) +
                   len(scraped_data.get("team_text", "")) +
                   len(scraped_data.get("press_text", "")) +
                   len(scraped_data.get("careers_text", "")))
    
    logging.info(f"✅ Total scraped: {total_chars} chars across multiple pages")
    
    return scraped_data
