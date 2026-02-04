import logging
import sys
import os
import random
import time
import csv
from .config import check_config, DAILY_LEAD_TARGET, INPUT_ICP_FILE, MIN_QUALIFICATION_GRADE,GOOGLE_SEARCH_DAILY_LIMIT
from .discovery import search_companies, search_shopify_stores_broad, search_with_keywords_shuffled
from .scraping import scrape_website
from .identification import search_decision_maker, is_valid_company_url
from .intelligence import analyze_lead, clean_name_with_vertex, extract_contacts_from_text, generate_keywords_from_icp
from .verification import verify_lead
from .storage import get_keywords, init_storage, save_lead
from .dedup import init_dedup_db, is_domain_processed, mark_domain_processed, get_domain, get_run_timestamp
from .keyword_tracker import init_keyword_tracker, filter_fresh_keywords, mark_keyword_used

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

TIMESTAMP = get_run_timestamp() # Use shared timestamp function
LOG_FILE = f"logs/run_{TIMESTAMP}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Timestamped run
RUN_TIMESTAMP = TIMESTAMP
# Ideally TIMESTAMPED_OUTPUT should be imported or set here. 
# config.py doesn't usually hold dynamic timestamps unless init there.
# Let's verify where TIMESTAMPED_OUTPUT was used. 
# In previous version it was: TIMESTAMPED_OUTPUT = f"leads/leads_{RUN_TIMESTAMP}.csv"
TIMESTAMPED_OUTPUT = f"leads/leads_{RUN_TIMESTAMP}.csv"

def main():
    check_config()
    init_storage()
    init_dedup_db()
    init_keyword_tracker()
    
    logging.info(f"Starting run at {RUN_TIMESTAMP}")
    searches_made_today = 0
    # --- 1. Load ICPs ---
    icps = []
    if os.path.exists(INPUT_ICP_FILE):
        with open(INPUT_ICP_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            icps = list(reader)
    else:
        logging.error(f"ICP File not found: {INPUT_ICP_FILE}")
        return

    leads_count = 0
    icp_iteration = 0  # Track how many times we've looped through ICPs
    
    # --- 2. Iterate through each ICP ---
    # We loop indefinitely over ICPs if target not met, to mimic continuous run
    while leads_count < DAILY_LEAD_TARGET:
        for icp_idx, icp in enumerate(icps):
            if leads_count >= DAILY_LEAD_TARGET:
                logging.info(f"Daily target {DAILY_LEAD_TARGET} reached! Exiting.")
                break
                
            logging.info(f"\n=== Processing ICP: {icp.get('Target Industry', 'General')} (Iteration {icp_iteration}) ===")
            
            # --- 3. Generate Keywords for this ICP ---
            # Use iteration as variation seed to get different keywords each loop
            variation_seed = icp_iteration * len(icps) + icp_idx
            try:
                keywords = generate_keywords_from_icp(icp, variation_seed=variation_seed)
            except Exception as e:
                logging.error(f"Failed to generate keywords: {e}")
                keywords = []
                
            if not keywords:
                logging.warning("No keywords generated for this ICP. Skipping.")
                continue
                
            # Filter to only fresh keywords (not overused)
            fresh_keywords = filter_fresh_keywords(keywords, max_usage=3)
            logging.info(f"Generated {len(keywords)} keywords ({len(fresh_keywords)} fresh). Starting Search...")
            
            remaining_searches = GOOGLE_SEARCH_DAILY_LIMIT - searches_made_today
            
            # CRITICAL: Exit if the budget is finished
            if remaining_searches <= 0:
                logging.info(f" Daily search limit ({GOOGLE_SEARCH_DAILY_LIMIT}) reached. Shutting down.")
                sys.exit(0) # This tells Google Cloud the job was successful and to stop charging.

            if len(fresh_keywords) > remaining_searches:
                logging.info(f"Trimming {len(fresh_keywords)} keywords to {remaining_searches} to stay in budget.")
                fresh_keywords = fresh_keywords[:remaining_searches]
                
            if not fresh_keywords:
                logging.info("No search quota remaining for this batch.")
                continue

            logging.info(f"Generated {len(keywords)} keywords. Using {len(fresh_keywords)} for search...")
            
            # --- 4. Search Companies ---
            # Use only fresh keywords to avoid re-searching exhausted terms
            all_companies = search_with_keywords_shuffled(fresh_keywords, market=icp.get("Target Geography", "USA"), limit_per_keyword=3)
            
            # UPDATE COUNTER
            searches_made_today += len(fresh_keywords)
            logging.info(f"Search Quota Used: {searches_made_today}/{GOOGLE_SEARCH_DAILY_LIMIT}")

            # Track keyword usage
            for kw in fresh_keywords[:10]:  # Track first 10 used
                mark_keyword_used(kw, len(all_companies))
            
            # Also mix in some broad search results for variety to keep pipeline moving if keywords fail
            broad_companies = search_shopify_stores_broad(market="USA", limit=10)
            all_companies.extend(broad_companies)
            
            logging.info(f"Found {len(all_companies)} companies (Keywords + Broad).")
            
            # Deduplicate discovery list
            unique_companies = []
            seen_links = set()
            for c in all_companies:
                if c['link'] not in seen_links:
                    unique_companies.append(c)
                    seen_links.add(c['link'])
            all_companies = unique_companies
            random.shuffle(all_companies)
            
            # --- 5. Process Discovered Companies ---
            for company in all_companies:
                if leads_count >= DAILY_LEAD_TARGET:
                    logging.info(f"Daily target {DAILY_LEAD_TARGET} reached! Exiting.")
                    break
                    
                c_name = company.get("title", "")
                c_link = company.get("link", "")
                
                # Validate company URL
                if not is_valid_company_url(c_link):
                    logging.warning(f"⊘ Skipping {c_name} - Invalid/spam URL: {c_link}")
                    continue
                
                # Check deduplication
                domain = get_domain(c_link)
                if is_domain_processed(domain):
                    logging.info(f"⊘ Skipping {c_name} - Already processed (domain: {domain})")
                    continue
                
                # EARLY CHECK: Vertex AI Company Validation
                cleaned_title = clean_name_with_vertex(c_name, strict=True)
                
                if not cleaned_title:
                    logging.info(f"⊘ Skipping {c_name} - Vertex AI says NOT A COMPANY")
                    continue
                    
                logging.info(f"Analyzing Company: {cleaned_title} (Cleaned from '{c_name}')")
                c_name = cleaned_title # Use cleaned name for rest of pipeline
                
                # Initial partial object to ensure we capture "what we got"
                current_lead = {
                    "Company": c_name,
                    "Company Info": company.get('snippet', ''),
                    "Keyword": company.get('keyword', 'Broad Discovery'),
                    "LinkedIn URL": "",
                    "Status": "Identified" 
                }
                
                # Scrape
                try:
                    scraped_data = scrape_website(c_link)
                except Exception as e:
                    logging.warning(f"Scraping crashed for {c_link}: {e}")
                    continue

                if not scraped_data['text']:
                    logging.info(f"Skipping {c_name} - No text scraped.")
                    current_lead["Status"] = "Scraping Failed"
                    save_lead(current_lead)
                    continue
    
                # STRATEGY 1: Extract POC from Website Text (Team/About pages)
                # This saves API calls and is often more accurate for smaller companies
                dm_info = None
                
                # Combine team/about text for analysis if available
                text_to_analyze = ""
                if scraped_data.get('team_text'):
                    text_to_analyze += scraped_data['team_text'] + "\n"
                if scraped_data.get('about_text'):
                    text_to_analyze += scraped_data['about_text']
                
                if len(text_to_analyze) > 100:
                    logging.info("Analyzing Team/About page text for POC...")
                    dm_info = extract_contacts_from_text(text_to_analyze, company_name=c_name)
                    
                # STRATEGY 2: External Search (LinkedIn X-Ray)
                if not dm_info:
                    # Identification X-Ray
                    dm_info = search_decision_maker(c_name, company_url=c_link)
                
                # Fallback: Email-First Name Extraction
                if not dm_info:
                    logging.info(f"Search strategies failed for {c_name}. Trying Email-First fallback...")
                    from .email_finder import find_email_on_website, extract_name_from_email
                    
                    # 1. Try finding emails on website
                    website_emails = find_email_on_website(c_link)
                    
                    for email in website_emails:
                        # 2. Try to infer name from email
                        res = extract_name_from_email(email)
                        if res:
                            first, last = res
                            logging.info(f"✓ Inferred Name from Email: {first} {last} ({email})")
                            dm_info = {
                                "first_name": first,
                                "last_name": last,
                                "title": "Contact (Inferred from Email)",
                                "email": email, # Pre-fill email
                                "linkedin_url": ""
                            }
                            break
                
                if not dm_info:
                    logging.info(f"Skipping {c_name} - No decision maker found.")
                    current_lead["Status"] = "No Decision Maker Found"
                    save_lead(current_lead)
                    continue
                
                # Update with DM info
                current_lead.update({
                    "Company": c_name, # Already cleaned
                    "First Name": dm_info.get('first_name', ''),
                    "Last Name": dm_info.get('last_name', ''),
                    "Title": dm_info.get('title', ''),
                    "LinkedIn URL": dm_info.get('linkedin_url', '')
                })
                
                # Intelligence - Aggregate ALL scraped content for comprehensive analysis
                combined_text = scraped_data['text']  # Homepage (15000 chars)
                
                # Add about page if available
                if scraped_data.get('about_text'):
                    combined_text += "\n\n=== ABOUT US PAGE ===\n" + scraped_data['about_text']
                
                # Add team page if available
                if scraped_data.get('team_text'):
                    combined_text += "\n\n=== TEAM PAGE ===\n" + scraped_data['team_text']
                
                # Add press/news if available (recent updates signal)
                if scraped_data.get('press_text'):
                    combined_text += "\n\n=== PRESS/NEWS ===\n" + scraped_data['press_text']
                
                # Add careers page if available (hiring = growth signal)
                if scraped_data.get('careers_text'):
                    combined_text += "\n\n=== CAREERS PAGE (HIRING SIGNALS) ===\n" + scraped_data['careers_text']
                
                # Include any metadata hints from scraping
                if scraped_data.get('metadata'):
                    metadata_hints = "\n\n=== METADATA HINTS ===\n"
                    for key, value in scraped_data['metadata'].items():
                        metadata_hints += f"{key}: {value}\n"
                    combined_text += metadata_hints
                
                analysis = analyze_lead(c_name, combined_text, dm_info)
                if not analysis:
                    logging.info(f"Skipping {c_name} - Vertex AI analysis failed.")
                    current_lead["Status"] = "Analysis Failed"
                    save_lead(current_lead)
                    continue
                
                # Update with Analysis
                grade = analysis.get('qualification_grade', 0)
                current_lead.update({
                    "Company Info": analysis.get('company_info', current_lead["Company Info"]),
                    "Qualification Grade": grade,
                    "Why Good?": analysis.get('why_good'),
                    "Pain_Point": analysis.get('pain_point'),
                    "Icebreaker": analysis.get('icebreaker'),
                    "Recent updates": analysis.get('recent_updates'),
                    # Optional enrichment fields
                    "Employee Count": analysis.get('employee_count', ''),
                    "Annual Revenue": analysis.get('annual_revenue', ''),
                    "Company Size": analysis.get('company_size', ''),
                    "Industry Tags": analysis.get('industry_tags', ''),
                    # AI Maximization
                    "Social Media": analysis.get('social_media', ''),
                    "Contact Details": analysis.get('contact_details', ''),
                    "Logistics Signals": analysis.get('logistics_signals', ''),
                    "Brand Vibe": analysis.get('brand_vibe', ''),
                    # Phase 2: Deep Intel
                    "Tech Stack": analysis.get('tech_stack', ''),
                    "Product Profile": analysis.get('product_profile', ''),
                    "Customer Focus": analysis.get('customer_focus', ''),
                    "Shipping Locations": analysis.get('shipping_locations', '')
                })
    
                logging.info(f"Qualification Grade: {grade}")
                
                # Quality filter - skip leads below minimum grade
                if MIN_QUALIFICATION_GRADE > 0 and grade < MIN_QUALIFICATION_GRADE:
                    logging.info(f"Lead grade {grade} below minimum {MIN_QUALIFICATION_GRADE}. Skipping.")
                    current_lead["Status"] = "Low Qualification Grade"
                    save_lead(current_lead)
                    continue
                    
                # Verification - Only if grade is good
                from urllib.parse import urlparse
                domain = urlparse(c_link).netloc.replace("www.", "")
                
                email, verification_status = verify_lead(dm_info['first_name'], dm_info['last_name'], domain, company_url=c_link)
                
                current_lead["Email"] = email if email else "No Email Found"
                current_lead["Status"] = verification_status
                
                # Save to both Master_Leads.csv (cumulative) and timestamped file
                save_lead(current_lead)
                save_lead(current_lead, TIMESTAMPED_OUTPUT)  # Also save to run-specific file
                
                # Sync to Google Sheets (if enabled)
                try:
                    from .sheets_sync import sync_lead_to_sheet
                    sync_lead_to_sheet(current_lead)
                except Exception as e:
                    logging.warning(f"Google Sheets sync failed (continuing anyway): {e}")
                
                # Mark as processed
                mark_domain_processed(domain, c_name)
                
                leads_count += 1
                logging.info(f"Lead saved! Total: {leads_count}")
        
        # Increment iteration counter after completing all ICPs
        icp_iteration += 1
        logging.info(f"\n=== Completed ICP iteration {icp_iteration}. Leads: {leads_count}/{DAILY_LEAD_TARGET} ===")

if __name__ == "__main__":
    main()
