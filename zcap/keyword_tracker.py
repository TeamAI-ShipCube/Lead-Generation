import csv
import os
import logging
from datetime import datetime

KEYWORD_TRACKING_FILE = "keyword_usage.csv"

def init_keyword_tracker():
    """Initialize keyword tracking CSV if it doesn't exist."""
    if not os.path.exists(KEYWORD_TRACKING_FILE):
        with open(KEYWORD_TRACKING_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['keyword', 'last_used', 'times_used', 'companies_found'])

def mark_keyword_used(keyword, companies_found):
    """Track keyword usage to avoid over-using exhausted keywords."""
    init_keyword_tracker()
    
    # Read existing data
    keyword_data = {}
    if os.path.exists(KEYWORD_TRACKING_FILE):
        with open(KEYWORD_TRACKING_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                keyword_data[row['keyword']] = {
                    'last_used': row['last_used'],
                    'times_used': int(row['times_used']),
                    'companies_found': int(row['companies_found'])
                }
    
    # Update or add keyword
    if keyword in keyword_data:
        keyword_data[keyword]['times_used'] += 1
        keyword_data[keyword]['companies_found'] += companies_found
        keyword_data[keyword]['last_used'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    else:
        keyword_data[keyword] = {
            'last_used': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'times_used': 1,
            'companies_found': companies_found
        }
    
    # Write back
    with open(KEYWORD_TRACKING_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['keyword', 'last_used', 'times_used', 'companies_found'])
        for kw, data in keyword_data.items():
            writer.writerow([kw, data['last_used'], data['times_used'], data['companies_found']])

def filter_fresh_keywords(keywords, max_usage=3):
    """
    Filter out keywords that have been overused.
    Returns keywords that have been used < max_usage times.
    """
    init_keyword_tracker()
    
    if not os.path.exists(KEYWORD_TRACKING_FILE):
        return keywords  # All fresh if no tracking yet
    
    keyword_usage = {}
    with open(KEYWORD_TRACKING_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            keyword_usage[row['keyword']] = int(row['times_used'])
    
    # Filter keywords
    fresh_keywords = [kw for kw in keywords if keyword_usage.get(kw, 0) < max_usage]
    
    logging.info(f"Keyword freshness: {len(fresh_keywords)}/{len(keywords)} keywords still fresh (used < {max_usage} times)")
    
    return fresh_keywords if fresh_keywords else keywords  # Return all if none are fresh
