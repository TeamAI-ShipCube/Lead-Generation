import csv
import os
from datetime import datetime
from urllib.parse import urlparse

PROCESSED_DOMAINS_FILE = "processed_domains.csv"

def init_dedup_db():
    """Initialize the deduplication database if it doesn't exist."""
    if not os.path.exists(PROCESSED_DOMAINS_FILE):
        with open(PROCESSED_DOMAINS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["domain", "first_processed_at", "last_processed_at", "company_name"])

def get_domain(url):
    """Extract domain from URL."""
    return urlparse(url).netloc.replace("www.", "")

def is_domain_processed(domain):
    """Check if a domain has been processed before."""
    if not os.path.exists(PROCESSED_DOMAINS_FILE):
        return False
    
    with open(PROCESSED_DOMAINS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['domain'] == domain:
                return True
    return False

def mark_domain_processed(domain, company_name):
    """Mark a domain as processed with timestamp."""
    timestamp = datetime.now().isoformat()
    
    # Check if already exists
    if is_domain_processed(domain):
        # Update last_processed_at
        rows = []
        with open(PROCESSED_DOMAINS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['domain'] == domain:
                    row['last_processed_at'] = timestamp
                rows.append(row)
        
        with open(PROCESSED_DOMAINS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["domain", "first_processed_at", "last_processed_at", "company_name"])
            writer.writeheader()
            writer.writerows(rows)
    else:
        # Add new entry
        with open(PROCESSED_DOMAINS_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([domain, timestamp, timestamp, company_name])

def get_run_timestamp():
    """Get current run timestamp for file naming."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
