import re
import logging
from .scraping import scrape_with_playwright, scrape_with_jina
from urllib.parse import urljoin

def extract_emails_from_text(text):
    """Extract email addresses from text using regex."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Filter out common generic/support emails
    exclude_keywords = ['support', 'info', 'hello', 'contact', 'admin', 'noreply', 'sales', 'marketing']
    filtered_emails = []
    
    for email in emails:
        local_part = email.split('@')[0].lower()
        if not any(keyword in local_part for keyword in exclude_keywords):
            filtered_emails.append(email)
    
    return filtered_emails

def extract_name_from_email(email):
    """
    Extracts a likely name from an email address (e.g. john.smith@... -> John Smith).
    Returns (first_name, last_name) or None.
    """
    try:
        local_part = email.split('@')[0]
        # Handle john.smith or john_smith
        parts = re.split(r'[._]', local_part)
        
        if len(parts) >= 2:
            first = parts[0].capitalize()
            last = parts[-1].capitalize()
            # Rigid Validation Blocklist (Expanded)
            blocklist = ['sales', 'support', 'info', 'admin', 'contact', 'team', 'marketing', 'media', 'press', 'inquiries', 'projects', 'hello', 'careers', 'jobs', 'weborders', 'orders', 'shipping', 'returns', 'customer', 'service', 'office', 'shop', 'store']
            
            if first.lower() in blocklist:
                return None
            
            # Additional rigid checks
            if len(first) < 2 or len(first) > 30: return None
            if any(char.isdigit() for char in first): return None
            
            # Basic validation: ensure no numbers and reasonable length
            if first.isalpha() and last.isalpha() and len(first) > 1 and len(last) > 1:
                return first, last
    except:
        pass
    return None

def find_email_on_website(base_url):
    """
    Scrape contact/about pages to find email addresses.
    Uses in-house Playwright scraper (free, unlimited).
    """
    common_contact_paths = [
        '/contact',
        '/contact-us',
        '/about',
        '/about-us',
        '/team',
        '/our-story'
    ]
    
    all_emails = []
    
    # Try scraping main page first
    logging.info(f"Scraping {base_url} for emails...")
    text = scrape_with_playwright(base_url)
    if not text:
        text = scrape_with_jina(base_url)
    
    if text:
        emails = extract_emails_from_text(text)
        all_emails.extend(emails)
    
    # Try common contact pages
    for path in common_contact_paths[:2]:  # Limit to 2 pages
        contact_url = urljoin(base_url, path)
        logging.info(f"Trying {contact_url}...")
        
        text = scrape_with_playwright(contact_url)
        if not text:
            text = scrape_with_jina(contact_url)
        
        if text:
            emails = extract_emails_from_text(text)
            all_emails.extend(emails)
            
            if emails:  # Stop if we found emails
                break
    
    # Deduplicate
    unique_emails = list(set(all_emails))
    
    if unique_emails:
        logging.info(f"✓ Found {len(unique_emails)} email(s) on website: {unique_emails}")
    
    return unique_emails
