import csv
import os
import logging
from .config import INPUT_ICP_FILE, OUTPUT_FILE

def get_keywords():
    """
    Reads keywords from the input file.
    """
    keywords = []
    if not os.path.exists(INPUT_KEYWORDS_FILE):
        # Create dummy if not exists
        with open(INPUT_KEYWORDS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Keyword"])
            writer.writerow(["Organic Cosmetics USA"])
        return ["Organic Cosmetics USA"] # Return default

    with open(INPUT_KEYWORDS_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        next(reader, None) # Skip header
        for row in reader:
            if row:
                keywords.append(row[0])
    return keywords

def init_storage():
    """
    Initializes the output CSV with headers if it doesn't exist.
    """
    headers = [
        "First Name", "Last Name", "Title", "Email", "LinkedIn URL", "Company", 
        "Company Info", "Qualification Grade", "Why Good?", "Pain_Point", 
        "Icebreaker", "Status", "Recent updates", "Keyword",
        "Employee Count", "Annual Revenue", "Company Size", "Industry Tags",
        "Social Media", "Contact Details", "Logistics Signals", "Brand Vibe", # AI Enrichment
        "Tech Stack", "Product Profile", "Customer Focus", "Shipping Locations" # Phase 2 Deep Intel
    ]
    
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

def save_lead(lead_data, filename=None):
    """
    Appends a lead to the CSV.
    If filename is provided, saves to that file instead of default OUTPUT_FILE.
    Validates lead data before saving.
    """
    if filename is None:
        filename = OUTPUT_FILE
    
    # Minimal validation to prevent bad data
    first_name = lead_data.get('First Name', '').strip()
    last_name = lead_data.get('Last Name', '').strip()
    
    # Skip leads with missing names
    if not first_name or not last_name:
        logging.warning(f"Skipping save: Missing name (First: '{first_name}', Last: '{last_name}')")
        return
    
    # Skip generic first names
    generic_names = ['sales', 'info', 'support', 'team', 'contact', 'admin']
    if first_name.lower() in generic_names:
        logging.warning(f"Skipping save: Generic first name '{first_name}'")
        return
    
    # Skip if first name matches company name
    company = lead_data.get('Company', '').strip()
    if first_name.lower() in company.lower().split():
        logging.warning(f"Skipping save: First name '{first_name}' matches company '{company}'")
        return
    
    headers = [
        "First Name", "Last Name", "Title", "Email", "LinkedIn URL", "Company", 
        "Company Info", "Qualification Grade", "Why Good?", "Pain_Point", 
        "Icebreaker", "Status", "Recent updates", "Keyword",
        "Employee Count", "Annual Revenue", "Company Size", "Industry Tags",
        "Social Media", "Contact Details", "Logistics Signals", "Brand Vibe", # AI Enrichment
        "Tech Stack", "Product Profile", "Customer Focus", "Shipping Locations" # Phase 2 Deep Intel
    ]
    
    # Initialize file with headers if new
    if not os.path.exists(filename):
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    # Ensure keys match schema
    row = []
    for h in headers:
        row.append(lead_data.get(h, ""))
        
    try:
        with open(filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    except Exception as e:
        logging.error(f"Failed to save lead: {e}")
