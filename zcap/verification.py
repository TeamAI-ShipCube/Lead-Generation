import smtplib
import dns.resolver
import socket
import logging
import requests
from .config import HUNTER_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_email_with_hunter(first_name, last_name, domain):
    """
    Use Hunter.io to find email. Always returns a tuple (email, status).
    """
    if not HUNTER_API_KEY:
        return None, "No Hunter API Key"
    
    api_url = "https://api.hunter.io/v2/email-finder"
    params = {
        "domain": domain,
        "first_name": first_name,
        "last_name": last_name,
        "api_key": HUNTER_API_KEY
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check if 'data' key exists and contains an email
        if data.get("data") and data["data"].get("email"):
            email = data["data"]["email"]
            confidence = data["data"].get("score", 0)
            logging.info(f"✓ Hunter.io found: {email} (confidence: {confidence}%)")
            return email, "Hunter.io"
        
        return None, "Hunter.io - Not Found"
        
    except Exception as e:
        logging.error(f"Hunter.io error: {e}")
        return None, f"Hunter.io Error: {str(e)}"

def generate_emails(first, last, domain):
    """
    Generates common email patterns.
    """
    if not first or not domain:
        return []
        
    f = first.lower()
    l = last.lower() if last else ""
    d = domain
    
    patterns = [
        f"{f}@{d}",
    ]
    
    if l:
        patterns.extend([
            f"{f}.{l}@{d}",
            f"{f}{l}@{d}",
            f"{f}_{l}@{d}",
            f"{l}.{f}@{d}",
            f"{f[0]}{l}@{d}",
            f"{f[0]}.{l}@{d}"
        ])
        
    return patterns

def get_mx_record(domain):
    """
    Retrieves the highest priority MX record for a domain.
    """
    try:
        records = dns.resolver.resolve(domain, 'MX')
        # Sort by preference and pick the first one
        mx_record = sorted(records, key=lambda r: r.preference)[0].exchange.to_text().rstrip('.')
        return mx_record
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, Exception) as e:
        logging.warning(f"Could not get MX record for {domain}: {e}")
        return None

def verify_email(email, mx_record=None):
    """
    Performs an SMTP handshake to verify if an email exists.
    Returns: 'Valid', 'Invalid', 'Catch-All', or 'Unknown'
    """
    domain = email.split('@')[1]
    
    if not mx_record:
        mx_record = get_mx_record(domain)
        if not mx_record:
            return "Unknown" # DNS failure

    try:
        # Connect to the MX server with SHORT timeout
        server = smtplib.SMTP(timeout=3)  # Fast fail: 3 seconds only
        server.set_debuglevel(0)
        
        # Connect
        server.connect(mx_record)
        
        # HELO/EHLO
        server.helo('verify.shipcube.io')
        
        # MAIL FROM
        server.mail('check@shipcube.io')
        
        # RCPT TO
        code, message = server.rcpt(email)
        server.quit()
        
        if code == 250:
            return "Valid"
        elif code == 550:
            return "Invalid"
        else:
            return "Unknown"

    except Exception as e:
        logging.warning(f"SMTP verification failed for {email}: {e}")
        return "Error"

# Global counter to limit SMTP checks per run
smtp_verification_count = 0
SMTP_VERIFICATION_LIMIT = 2  # Only verify 2 emails per run

# Cache for catch-all domains (to skip SMTP for them)
catch_all_domains = set()

def check_catch_all(domain, mx_record=None):
    """
    Checks if a domain is a catch-all by testing a random invalid email.
    """
    random_email = f"xyz123randomtest@{domain}"
    result = verify_email(random_email, mx_record)
    return result == "Valid"

def verify_lead(first_name, last_name, domain, company_url=None):
    global smtp_verification_count
    
    if not first_name or not domain:
        return None, "Missing Lead Data"

    # 1. Scrape Website (Best for Cloud)
    if company_url:
        try:
            from .email_finder import find_email_on_website
            emails_found = find_email_on_website(company_url)
            if emails_found:
                # Logic to check name matching...
                return emails_found[0], "Website Scrape"
        except Exception as e:
            logging.error(f"Scraper error: {e}")

    # 2. Hunter.io (Very reliable in Cloud)
    email, status = find_email_with_hunter(first_name, last_name, domain)
    if email:
        # Only try SMTP if we are under the limit AND not in a blocked environment
        if smtp_verification_count < SMTP_VERIFICATION_LIMIT:
            smtp_result = smart_smtp_verify(email)
            if smtp_result == "Valid":
                smtp_verification_count += 1
                return email, f"{status} (SMTP Verified)"
        return email, status
    
    # 3. Pattern Guessing (Safe fallback)
    patterns = generate_emails(first_name, last_name, domain)
    if patterns:
        return patterns[0], "Pattern Guess (Not Verified)"
    
    return None, "Email Not Found"
       
def smart_smtp_verify(email):
    """
    Smart SMTP verification with quick fail and catch-all detection.
    Returns: 'Valid', 'Invalid', or 'Skip'
    """
    try:
        domain = email.split('@')[1]
        
        # Skip if domain is known catch-all
        if domain in catch_all_domains:
            logging.info(f"Skipping SMTP for catch-all domain: {domain}")
            return "Skip"
        
        # Get MX record
        mx_record = get_mx_record(domain)
        if not mx_record:
            logging.warning(f"No MX record for {domain}")
            return "Skip"
        
        # Check if catch-all (quick test)
        if check_catch_all(domain, mx_record):
            logging.info(f"Domain {domain} is catch-all - caching")
            catch_all_domains.add(domain)
            return "Skip"
        
        # Verify the actual email
        result = verify_email(email, mx_record)
        
        if result == "Valid":
            logging.info(f"✓ SMTP verified: {email}")
            return "Valid"
        elif result == "Invalid":
            logging.warning(f"✗ SMTP invalid: {email}")
            return "Invalid"
        else:
            return "Skip"
            
    except Exception as e:
        logging.warning(f"SMTP verification error for {email}: {e}")
        return "Skip"
