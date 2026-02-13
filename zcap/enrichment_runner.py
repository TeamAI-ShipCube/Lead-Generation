import csv
import logging
import os
from urllib.parse import urlparse
from datetime import datetime

from .sheets_sync import sync_enriched_lead_to_sheet, get_enrichment_sheet_rows
from .scraping import scrape_website
from .intelligence import analyze_lead
from .verification import verify_lead
from .identification import search_decision_maker   # ✅ FIXED
from .config import check_config
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import re
from .discovery import search_companies

INPUT_FILE = "Input_Enrichment.csv"
OUTPUT_FILE = "Enriched_Output.csv"

FIELDNAMES = [
    "First Name","Last Name","Title","Email","LinkedIn URL","Company",
    "Company Info","Qualification Grade","Why Good?","Pain_Point",
    "Icebreaker","Status","Recent updates","Keyword",
    "Employee Count","Annual Revenue","Company Size","Industry Tags",
    "Social Media","Contact Details","Logistics Signals","Brand Vibe",
    "Tech Stack","Product Profile","Customer Focus","Shipping Locations",
    "Timestamp"
]

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s")

SCRAPE_CACHE = {}
SCRAPE_LOCK = threading.Lock()
MAX_WORKERS = 5


# ---------------------------------------------------
# Website Discovery
# ---------------------------------------------------
def discover_company_website(company):
    try:
        results = search_companies(company, is_enrichment=True)

        if not results:
            logging.warning(f"No website found via Google for {company}")
            return None

        link = results[0].get("link")
        if not link:
            return None

        parsed = urlparse(link)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        logging.info(f"🌐 Official website found: {base_url}")
        return base_url

    except Exception as e:
        logging.error(f"Website discovery failed for {company}: {e}")
        return None

def validate_website_matches_company(company, url, scraped_text):
    """
    Ensures discovered website actually belongs to the input company.
    """

    if not url or not scraped_text:
        return False

    company_clean = company.lower().split()[0]
    domain = urlparse(url).netloc.lower()

    # Domain must contain part of company name
    if company_clean not in domain:
        logging.warning(f"❌ Website domain mismatch: {domain} vs {company}")
        return False

    # Homepage text must contain company name
    if company_clean not in scraped_text.lower():
        logging.warning(f"❌ Website content mismatch for {company}")
        return False

    return True


def extract_company_from_row(row):
    raw_company = (
        row.get("Company Name")
        or row.get("Company name")
        or row.get("Company")
        or ""
    ).strip()

    company = re.split(r"-|\|", raw_company)[0].strip()
    return company


# ---------------------------------------------------
# Mode Detection
# ---------------------------------------------------
def detect_mode(fieldnames):
    headers = [h.lower().strip() for h in fieldnames]
    logging.info(f"Detected headers: {headers}")

    has_first = any("first" in h for h in headers)
    has_last = any("last" in h for h in headers)
    has_company = any("company" in h for h in headers)

    if has_first and has_last and has_company:
        logging.info("🟢 Mode 1 detected — Person Enrichment Mode")
        return "person_mode"

    if has_company and not has_first:
        logging.info("🔵 Mode 2 detected — Company Lead Generation Mode")
        return "company_mode"

    raise ValueError(f"Unsupported CSV structure. Headers found: {headers}")


# ---------------------------------------------------
# Company Mode Lead Generation (FIXED)
# ---------------------------------------------------
def generate_from_company_row(row):
    company = extract_company_from_row(row)
    if not company:
        logging.warning("⚠️ Skipping row: No company name found.")
        return None

    logging.info(f"🔎 Generating lead for company: {company}")

    # 1️⃣ Discover website
    website = discover_company_website(company)
    if not website:
        logging.warning(f"❌ Website not found for {company}")
        return build_blocked_record("", "", "", company, row, "Website Not Found")

    # 2️⃣ Scrape and Validate
    scraped_preview = scrape_website(website)
    if not scraped_preview or not scraped_preview.get("text"):
        return build_blocked_record("", "", "", company, row, "Website Scrape Failed")

    if not validate_website_matches_company(
        company,
        website,
        scraped_preview.get("text", "")
    ):
        return build_blocked_record("", "", "", company, row, "Website Identity Mismatch")

    # 3️⃣ Find decision maker
    person = search_decision_maker(
        company_name=company,
        company_url=website
    )

    if not person:
        # We still want to log the company in the sheet even if no person is found
        return build_blocked_record("", "", "", company, row, "No Decision Maker Found")

    # 4️⃣ Map found person data
    first = person.get("first_name", "")
    last = person.get("last_name", "")
    title = person.get("title", "")
    linkedin_url = person.get("linkedin_url", "")

    # Create a standardized row for the enrichment engine
    # Note: Ensure keys match what enrich_row expects!
    processing_row = {
        "Person Name": f"{first} {last}".strip(),
        "Job Title": title,
        "Company name": company,
        "LinkedIn URL": linkedin_url,
        "Discovered Website": website
    }

    # Pass to the final enrichment (API calls for email, analysis, etc.)
    return enrich_row(processing_row)


# ---------------------------------------------------
# Enrichment Core
# ---------------------------------------------------
def split_name(full_name):
    if not full_name:
        return "", ""

    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0], ""

    return parts[0], " ".join(parts[1:])


def build_combined_text(scraped):
    text = scraped.get("text", "")
    for k in ["about_text", "press_text", "careers_text"]:
        if scraped.get(k):
            text += "\n" + scraped[k]
    return text[:15000]


def build_blocked_record(first, last, title, company, row, reason):
    """
    Creates a lead record for entries that failed validation.
    Ensures 100% compatibility with FIELDNAMES to prevent Google Sheets sync errors.
    """
    # 1. Initialize the dictionary with ALL keys from FIELDNAMES set to empty strings
    # This guarantees the Google Sheet row will have the correct number of columns.
    record = {field: "" for field in FIELDNAMES}

    # 2. Define the specific data for the blocked entry
    blocked_data = {
        "First Name": first or "",
        "Last Name": last or "",
        "Title": title or "Not Found",
        "Email": "Not Found",
        "LinkedIn URL": row.get("LinkedIn URL") or row.get("LinkedIn") or "",
        "Company": company,
        "Status": f"Blocked — {reason}",
        "Pain_Point": reason,  # Store why it was blocked here for easy filtering
        "Qualification Grade": 0,
        "Keyword": "Enrichment",
        "Timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 3. Merge the blocked data into the template
    record.update(blocked_data)

    return record

def enrich_row(row):
    person = row.get("Person Name", "").strip()
    title = row.get("Job Title", "").strip()
    company = extract_company_from_row(row)
    first, last = split_name(person)

    if not company:
        return None

    linkedin_url = row.get("LinkedIn URL", "")
    url = row.get("Discovered Website")

    # --- Scrape Logic ---
    with SCRAPE_LOCK:
        scraped = SCRAPE_CACHE.get(url)
    if not scraped:
        scraped = scrape_website(url)
        with SCRAPE_LOCK:
            SCRAPE_CACHE[url] = scraped

    if not scraped or not scraped.get("text"):
        return build_blocked_record(first, last, title, company, row, "Scrape Failed")

    combined = build_combined_text(scraped)
    dm = {"first_name": first, "last_name": last, "title": title, "linkedin_url": linkedin_url}

    # --- Analysis Logic ---
    analysis = analyze_lead(company, combined, dm)
    if not analysis:
        return build_blocked_record(first, last, title, company, row, "Analysis Failed")

    domain = urlparse(url).netloc.replace("www.", "")
    email, status = verify_lead(first, last, domain, company_url=url)

    # Validate email domain
    if email:
        email_domain = email.split("@")[-1].lower()
        if email_domain != domain.lower():
            logging.warning(f"❌ Email domain mismatch: {email_domain} vs {domain}")
            return build_blocked_record(first, last, title, company, row, "Email Domain Mismatch")

    # --- THE MAPPING (Must match FIELDNAMES exactly) ---
    return {
        "First Name": first,
        "Last Name": last,
        "Title": title,
        "Email": email or "Not Found",
        "LinkedIn URL": linkedin_url,
        "Company": company,
        "Company Info": analysis.get("company_info", ""),
        "Qualification Grade": analysis.get("qualification_grade", 0),
        "Why Good?": analysis.get("why_good", ""),
        "Pain_Point": analysis.get("pain_point", ""),
        "Icebreaker": analysis.get("icebreaker", ""),
        "Status": status or "Processed",
        "Recent updates": analysis.get("recent_updates", ""),
        "Keyword": "Enrichment",
        "Employee Count": analysis.get("employee_count", ""),
        "Annual Revenue": analysis.get("annual_revenue", ""),
        "Company Size": analysis.get("company_size", ""),
        "Industry Tags": analysis.get("industry_tags", ""),
        "Social Media": analysis.get("social_media", ""),
        "Contact Details": analysis.get("contact_details", ""),
        "Logistics Signals": analysis.get("logistics_signals", ""),
        "Brand Vibe": analysis.get("brand_vibe", ""),
        "Tech Stack": analysis.get("tech_stack", ""),
        "Product Profile": analysis.get("product_profile", ""),
        "Customer Focus": analysis.get("customer_focus", ""),
        "Shipping Locations": analysis.get("shipping_locations", ""),
        "Timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }
def load_processed_companies():
    processed = set()

    try:
        rows = get_enrichment_sheet_rows()
    except Exception as e:
        logging.warning(f"Sheet resume load failed: {e}")
        return processed

    for r in rows:
        company = r.get("Company", "").strip().lower()
        if company:
            processed.add(company)

    logging.info(f"📌 Resume loaded {len(processed)} processed companies")
    return processed


# ---------------------------------------------------
# Runner
# ---------------------------------------------------
def run_enrichment():

    processed_companies = load_processed_companies()

    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        mode = detect_mode(reader.fieldnames)

    out_rows = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:

        if mode == "company_mode":

            futures = []

            for row in rows:
                company = extract_company_from_row(row).lower()

                if company in processed_companies:
                    logging.info(f"⏭️ Skipping already processed company: {company}")
                    continue

                futures.append(
                    pool.submit(generate_from_company_row, row)
                )

        else:
            return

        for future in as_completed(futures):
            result = future.result()

            if not result:
                continue

            logging.info(f"📤 Syncing to sheet: {result.get('Company')}")
            sync_enriched_lead_to_sheet(result)

            out_rows.append(result)

    if out_rows:
        write_output(out_rows)


def write_output(rows):
    exists = os.path.exists(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not exists:
            w.writeheader()
        w.writerows(rows)


def main():
    check_config()
    logging.info("🚀 Enrichment run started (Cloud Run)")
    run_enrichment()


if __name__ == "__main__":
    main()
