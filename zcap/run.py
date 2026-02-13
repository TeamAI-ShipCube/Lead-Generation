import logging
import sys
import os
import random
import time
import csv
from .sheets_sync import sync_lead_to_sheet
from .config import check_config, DAILY_LEAD_TARGET, INPUT_ICP_FILE, MIN_QUALIFICATION_GRADE,GOOGLE_SEARCH_DAILY_LIMIT
from .discovery import search_companies, search_shopify_stores_broad, search_with_keywords_shuffled
from .scraping import scrape_website
from .identification import search_decision_maker, is_valid_company_url
from .intelligence import analyze_lead, clean_name_with_vertex, extract_contacts_from_text, generate_keywords_from_icp
from .verification import verify_lead
from .storage import get_keywords, init_storage, save_lead
from .dedup import init_dedup_db, is_domain_processed, mark_domain_processed, get_domain, get_run_timestamp
from .keyword_tracker import init_keyword_tracker, filter_fresh_keywords, mark_keyword_used
from urllib.parse import urlparse

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
TIMESTAMPED_OUTPUT = None
# Timestamped run
RUN_TIMESTAMP = TIMESTAMP
#TIMESTAMPED_OUTPUT = f"../leads/leads_{RUN_TIMESTAMP}.csv"

def main():
    check_config()
    init_storage()
    init_dedup_db()
    init_keyword_tracker()

    leads_count = 0
    searches_made_today = 0
    logging.info(f"🚀 Starting run at {RUN_TIMESTAMP}")

    icps = []
    if os.path.exists(INPUT_ICP_FILE):
        with open(INPUT_ICP_FILE, mode='r', encoding='utf-8-sig') as f:
            icps = list(csv.DictReader(f))
    else:
        logging.error(f"ICP File not found: {INPUT_ICP_FILE}")
        return

    icp_iteration = 0 
    while leads_count < DAILY_LEAD_TARGET:
        for icp_idx, icp in enumerate(icps):
            if leads_count >= DAILY_LEAD_TARGET: break
                
            logging.info(f"\n=== Processing ICP: {icp.get('Target Industry', 'General')} (Iteration {icp_iteration}) ===")
            
            # Generate and Filter Keywords
            variation_seed = icp_iteration * len(icps) + icp_idx
            try:
                keywords = generate_keywords_from_icp(icp, variation_seed=variation_seed)
            except Exception as e:
                logging.error(f"Failed to generate keywords: {e}")
                keywords = []
            
            fresh_keywords = filter_fresh_keywords(keywords, max_usage=3)
            remaining_searches = GOOGLE_SEARCH_DAILY_LIMIT - searches_made_today
            
            if remaining_searches <= 0:
                logging.info(f"🛑 Daily search limit reached. Shutting down.")
                return

            if len(fresh_keywords) > remaining_searches:
                fresh_keywords = fresh_keywords[:remaining_searches]
                
            if not fresh_keywords: continue

            # Search Companies
            new_batch = search_with_keywords_shuffled(fresh_keywords, market=icp.get("Target Geography", "USA"), limit_per_keyword=3)
            searches_made_today += len(fresh_keywords)
            
            # Keyword Tracking
            for kw in fresh_keywords:
                results_for_kw = [c for c in new_batch if c.get('keyword') == kw]
                mark_keyword_used(kw, len(results_for_kw))

            # Add broad variety search occasionally 
            broad_companies = search_shopify_stores_broad(market="USA", limit=5)
            all_companies = new_batch + broad_companies
            
            # --- . Process Discovered Companies ---
            # Replace the discovery processing loop with this:
            for company in all_companies:
                if leads_count >= DAILY_LEAD_TARGET: break
                
                try:
                    # If this company hangs, the 'except' block will catch it
                    if process_single_company(company):
                        leads_count += 1
                        logging.info(f"Lead saved! Total Progress: {leads_count}/{DAILY_LEAD_TARGET}")
                except Exception as e:
                    logging.error(f"⚠️ Skipping company due to timeout/error: {company.get('title')} -> {e}")
                    continue

        # Increment iteration counter after completing all ICPs
        icp_iteration += 1
        logging.info(f"\n=== Completed ICP iteration {icp_iteration}. Leads: {leads_count}/{DAILY_LEAD_TARGET} ===")

def process_single_company(company):
    """
    Consolidated Pipeline: Handles deep scraping, POC discovery, 
    and AI analysis for both Enrichment and Discovery.
    """
    c_name = company.get("title", "")
    c_link = company.get("link", "")
    
    # 1. Validation & Dedup
    if not is_valid_company_url(c_link):
        return False
    domain = get_domain(c_link)
    if is_domain_processed(domain):
        logging.info(f"⊘ Skipping {c_name} - Already processed.")
        return False

    # 2. Early Name Clean (Gemini)
    cleaned_title = clean_name_with_vertex(c_name, strict=True)
    if not cleaned_title: return False
    c_name = cleaned_title

    # Initialize lead with baseline data
    current_lead = {
        "Company": c_name,
        "Company Info": company.get('snippet', ''),
        "Keyword": company.get('keyword', 'Discovery'),
        "Status": "Processing",
        "Timestamp": get_run_timestamp()
    }

    try:
        # 3. Deep Scraping
        scraped_data = scrape_website(c_link)
        if not scraped_data.get("text") or scraped_data.get("error"):
            current_lead["Status"] = scraped_data.get("error", "Scraping Failed")
            logging.info(f"⛔ Skipping {c_name} — {current_lead['Status']}")
            return False

        # 4. POC Discovery (Website -> LinkedIn)
        dm_info = None
        text_for_poc = (scraped_data.get('team_text', '') + scraped_data.get('about_text', ''))
        if len(text_for_poc) > 100:
            dm_info = extract_contacts_from_text(text_for_poc, company_name=c_name)
        
        if not dm_info:
            dm_info = search_decision_maker(c_name, company_url=c_link)

        if not dm_info:
            current_lead["Status"] = "No Decision Maker Found"
            save_lead(current_lead)
            return False

        # 5. Aggregate Text for AI Analysis
        combined_text = f"HOMEPAGE:\n{scraped_data['text']}"
        if scraped_data.get('about_text'): combined_text += f"\n\nABOUT:\n{scraped_data['about_text']}"
        if scraped_data.get('careers_text'): combined_text += f"\n\nCAREERS:\n{scraped_data['careers_text']}"
        if scraped_data.get('press_text'): combined_text += f"\n\nPRESS:\n{scraped_data['press_text']}"

        # 6. AI Intelligence Analysis
        analysis = analyze_lead(c_name, combined_text, dm_info)
        if not analysis:
            current_lead["Status"] = "Analysis Failed"
            save_lead(current_lead)
            return False

        # 7. Verification (CRITICAL: Define email/v_status before updating current_lead)
        # Extract domain safely
        domain_for_verify = urlparse(c_link).netloc.replace("www.", "")
        
        email, v_status = verify_lead(
            dm_info.get('first_name', ''), 
            dm_info.get('last_name', ''), 
            domain_for_verify, 
            company_url=c_link
        )
        if not v_status:
            v_status = "Verification Unknown"

        # 8. Data Mapping (The "Update" Block)
        current_lead.update({
            # Personal Info
            "First Name": dm_info.get('first_name', ''),
            "Last Name": dm_info.get('last_name', ''),
            "Title": dm_info.get('title', ''),
            "Email": email or "No Email Found",
            "LinkedIn URL": dm_info.get('linkedin_url', ''),
            
            # Company Details
            "Company Info": analysis.get('company_info', current_lead["Company Info"]),
            "Qualification Grade": analysis.get('qualification_grade', 0),
            "Why Good?": analysis.get('why_good', ''),
            "Pain_Point": analysis.get('pain_point', ''),
            "Icebreaker": analysis.get('icebreaker', ''),
            "Status": v_status, 
            "Recent updates": analysis.get('recent_updates', ''),
            
            # Firmographics
            "Employee Count": analysis.get('employee_count', ''),
            "Annual Revenue": analysis.get('annual_revenue', ''),
            "Company Size": analysis.get('company_size', ''),
            "Industry Tags": analysis.get('industry_tags', ''),
            
            # Deep Logistics Intel
            "Social Media": analysis.get('social_media', ''),
            "Contact Details": analysis.get('contact_details', ''),
            "Logistics Signals": analysis.get('logistics_signals', ''),
            "Brand Vibe": analysis.get('brand_vibe', ''),
            "Tech Stack": analysis.get('tech_stack', ''),
            "Product Profile": analysis.get('product_profile', ''),
            "Customer Focus": analysis.get('customer_focus', ''),
            "Shipping Locations": analysis.get('shipping_locations', '')
        })

        # 9. Final Actions: Sync, Save, and Mark Processed
        try:
            sync_lead_to_sheet(current_lead)
            logging.info(f"🚀 SUCCESS: {c_name} synced to Sheets.")
        except Exception as e:
            logging.error(f"❌ Sheets sync failed: {e}")

        save_lead(current_lead) 
        mark_domain_processed(domain, c_name)
        return True 

    except Exception as e:
        logging.error(f"Pipeline crashed for {c_name}: {e}")
        return False

if __name__ == "__main__":
    main()
