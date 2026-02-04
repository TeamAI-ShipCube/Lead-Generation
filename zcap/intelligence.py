import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import logging
import json
import time
from .config import GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION

# Configure Vertex AI
# Ensure you have authenticated via `gcloud auth application-default login` or set GOOGLE_APPLICATION_CREDENTIALS
try:
    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)
except Exception as e:
    logging.warning(f"Vertex AI init failed (might be delayed until usage): {e}")

MODEL_NAME = "gemini-2.0-flash-001"  # Vertex AI Model ID

PROMPT_TEMPLATE = """
You are an expert B2B Logistics Sales Strategist for Shipcube. You are analyzing a prospect company to determine if they need 3PL (Third Party Logistics) services.

Input Data:
Company Name: {company_name}
Website Text: {website_text}
Decision Maker: {decision_maker_name} ({decision_maker_title})

Your Task:
Generate a JSON object with the following fields:

**Required Fields:**
- qualification_grade (Number 1-10): strict grading based on 3PL fit.
- why_good (String): A strategic justification. Connect Cause (e.g., funding, growth, product launch) to Effect (need for logistics).
- pain_point (String): Diagnose the operational bottleneck. Look for 'delays', 'hiring ops', 'manual processes', 'compliance'. If no specific pain is found but they are small/growing, infer 'Scaling Friction'.
- icebreaker (String): A hyper-personalized opening line for an email to {decision_maker_name}.
- company_info (String): A 1-sentence summary of what they do.
- recent_updates (String): Summarize 1 relevant news fact or infer from text if possible (e.g. "Launched new collection").

**Optional Enrichment Fields - CRITICAL RULES:**

⚠️ IMPORTANT: DO NOT FABRICATE OR GUESS ANY DATA. ONLY extract information that is EXPLICITLY STATED in the website text. If not found, return empty string "".

**Enrichment Fields (Extract Explicitly):**
- social_media (String): Comma-separated links found (e.g., "Instagram: @handle, LinkedIn: /company/xyz").
- contact_details (String): Phone numbers or physical location (e.g., "Phone: 555-0199, HQ: Austin, TX").
- logistics_signals (String): Shipping/Returns keywords (e.g., "Free Shipping", "30-day returns", "International shipping").
- brand_vibe (String): 2-3 words describing the tone (e.g., "Luxury, Eco-friendly", "Industrial, Budget").
- tech_stack (String): E-commerce platforms or tools mentioned (e.g., "Shopify", "WooCommerce", "Klaviyo", "Recharge").
- product_profile (String): Key logistics traits: "Perishable", "Fragile", "Heavy/Bulky", or "Standard".
- customer_focus (String): "B2B", "B2C", or "Both".
- shipping_locations (String): Analyze shipping policy OR infer from HQ location (e.g., European HQ = International). Values: "US Only", "International", "Global", "North America".

- employee_count (String): 
  * ONLY if EXPLICITLY mentioned (e.g., "We have 50 employees", "Team of 25", "100+ person company")
  * Use exact phrasing from text (e.g., "50", "25-50", "100+", "Small team of 10")
  * If NOT explicitly stated → return ""
  * DO NOT guess, estimate, or infer from company size

- annual_revenue (String): 
  * ONLY if EXPLICITLY mentioned (e.g., "$5M in revenue", "ARR of $10M", "$1-5M annual sales")
  * Use exact phrasing from text
  * If NOT explicitly stated → return ""
  * DO NOT guess or estimate revenue

- company_size (String): 
  * ONLY if EXPLICITLY mentioned (e.g., "We're a startup", "Small business", "Enterprise company")
  * Valid values: "Startup", "Small Business", "Mid-Market", "Enterprise"
  * If NOT explicitly stated → return ""
  * DO NOT infer from other signals - must be directly stated

- industry_tags (String): 
  * Extract ONLY from actual content (e.g., "e-commerce platform", "sustainable fashion brand", "DTC beauty")
  * Comma-separated (e.g., "E-commerce, Fashion, DTC")
  * Base on what they explicitly describe themselves as
  * If unclear or generic → return ""
  * DO NOT guess industry from domain name alone

**STRICT RULE**: When in doubt, return empty string "". Better to have missing data than incorrect data.

Analysis Matrix:
- Grade 1-4: Dropshipping, No physical address, Digital goods. -> Discard logic (but return grade).
- Grade 5-7: Stable business, small team, no news.
- Grade 8-9: Growth signals, hiring Ops, expanding markets.
- Grade 10: Supply chain failure signals, massive funding, direct 3PL match.

Return ONLY the JSON.
"""

def analyze_lead(company_name, website_text, decision_maker_info):
    """
    Sends data to Vertex AI Gemini to get qualification metrics.
    """
    dm_name = "Prospect"
    dm_title = "Founder"
    if decision_maker_info:
        dm_name = f"{decision_maker_info.get('first_name', '')} {decision_maker_info.get('last_name', '')}".strip()
        dm_title = decision_maker_info.get('title', 'Founder')
        
    prompt = PROMPT_TEMPLATE.format(
        company_name=company_name,
        website_text=website_text[:15000], 
        decision_maker_name=dm_name,
        decision_maker_title=dm_title
    )
    
    try:
        model = GenerativeModel(MODEL_NAME)
        
        # Vertex AI generation
        # Adding a small delay just in case of tight loops, though Vertex quotas are usually per minute
        time.sleep(1) 
        
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        if response.text:
            text = response.text.strip()
            # Clean potential markdown
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            data = json.loads(text)
            if isinstance(data, list):
                if data:
                    data = data[0] # Take first item if list
                else:
                    return None
            return data
        
    except Exception as e:
        logging.error(f"Vertex AI analysis failed: {e}")
        return None

def clean_name_with_vertex(raw_name, strict=False):
    """
    Uses Vertex AI Gemini to extract the CLEAN company name from a messy title.
    If strict=True, returns None if the title does not appear to be a company/brand.
    """
    if not raw_name:
        return ""
        
    prompt = f"""
    You are a data cleaning assistant.
    Task: Analyze the Google Search Title and extract the Company Name.
    
    Input Title: "{raw_name}"
    
    Rules:
    1. Determine if this title represents a specific COMPANY, BRAND, or WEBSITE.
    2. If it is a generic list (e.g. "Top 10..."), a directory category, or purely informational, mark is_company=false.
    3. EXTRACT ONLY the brand/company name.
    4. REMOVE seo keywords, pipes, hyphens, "Home", "Welcome to".
    
    Examples:
    "Polish Vitamins & Minerals – Daily Wellness Supplements USA ..." -> {{ "company_name": "Polish Vitamins & Minerals", "is_company": true }}
    "Best 10 Running Shoes in 2025" -> {{ "company_name": "", "is_company": false }}
    "Amazon.com: Nike Shoes" -> {{ "company_name": "Nike", "is_company": true }}
    "General Health - LoveBug Probiotics USA" -> {{ "company_name": "LoveBug Probiotics", "is_company": true }}
    "Funny Cat Videos" -> {{ "company_name": "", "is_company": false }}
    
    Output JSON:
    {{ "company_name": "string", "is_company": boolean }}
    """
    
    try:
        model = GenerativeModel("gemini-2.0-flash-001")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        if response.text:
            data = json.loads(response.text)
            is_company = data.get("is_company", True)
            name = data.get("company_name", "").strip()
            
            if strict and not is_company:
                logging.info(f"Vertex: '{raw_name}' is NOT a company.")
                return None
                
            return name if name else raw_name.split('|')[0].strip()
            
    except Exception as e:
        logging.warning(f"Vertex Name Clean failed: {e}")
        
    return raw_name.split('|')[0].split('-')[0].strip()

def extract_contacts_from_text(text, company_name=""):
    """
    Extracts the BEST point of contact (POC) and their Role (POR) from raw website text.
    Prioritizes: Founder > CEO > Director > Manager > Generic Contact.
    Returns: { "first_name": "...", "last_name": "...", "title": "...", "email": "..." } or None
    """
    if not text or len(text) < 100:
        return None
        
    # Truncate text to avoid token limits (focus on likely areas)
    # Team/About pages are usually concise, but main text might be huge.
    analysis_text = text[:10000] 
    
    prompt = f"""
    You are an expert lead researcher.
    Task: Extract the key Decision Maker (POC) and their Role (POR) from the text.
    
    Input Text:
    {analysis_text}
    
    Rules:
    1. Find the Highest Ranking Person (CEO, Founder, Owner, President).
    2. If not found, find High Level Ops (Director of Ops, Logistics Manager).
    3. If not found, find ANY specific contact person listed.
    4. Ignore generic names (e.g. "Jane Doe" placeholders).
    5. Return JSON only.
    
    Output JSON:
    {{ 
        "first_name": "String", 
        "last_name": "String", 
        "title": "String", 
        "confidence": "High/Medium/Low" 
    }}
    or {{}} if no specific person found.
    """
    
    try:
        model = GenerativeModel("gemini-2.0-flash-001")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        if response.text:
            data = json.loads(response.text)
            if data.get("first_name"):
                first = (data.get("first_name") or "").strip()
                last = (data.get("last_name") or "").strip()
                
                # Validation Blocklist
                blocklist = ['sales', 'support', 'info', 'admin', 'contact', 'team', 'marketing', 'media', 'press', 'inquiries']
                if first.lower() in blocklist:
                    logging.info(f"Vertex returned generic name '{first}'. Rejecting.")
                    return None
                    
                # Heuristic: Name shouldn't be the company name
                if first.lower() in company_name.lower().split():
                     logging.info(f"Vertex returned company-like name '{first}' (Company: {company_name}). Rejecting.")
                     return None
                
                # Rigid Validation: 
                # 1. Must not look like an email
                if "@" in first or ".com" in first:
                    logging.info(f"Vertex returned email-like name '{first}'. Rejecting.")
                    return None
                    
                # 2. Must not contain numbers
                if any(char.isdigit() for char in first):
                    logging.info(f"Vertex returned name with numbers '{first}'. Rejecting.")
                    return None
                    
                # 3. Must be reasonable length (2-30 chars)
                if len(first) < 2 or len(first) > 30:
                    logging.info(f"Vertex returned suspect length name '{first}'. Rejecting.")
                    return None

                # 4. Check against extended blocklist of titles often mistaken for names
                title_blocklist = ['founder', 'ceo', 'owner', 'president', 'manager', 'director', 'team', 'staff', 'member', 'partner']
                if first.lower() in title_blocklist:
                    logging.info(f"Vertex returned title '{first}' as name. Rejecting.")
                    return None
                    
                logging.info(f"Vertex Extracted POC from text: {first} ({data.get('title')})")
                return {
                    "first_name": first,
                    "last_name": last,
                    "title": data.get("title") or "Contact",
                    "email": None, 
                    "linkedin_url": ""
                }
    except Exception as e:
        logging.warning(f"Vertex POC Extraction failed: {e}")
        
    return None

def generate_keywords_from_icp(icp_row, variation_seed=None):
    """
    Generates tailored search keywords based on an Ideal Customer Profile (ICP).
    variation_seed: Optional integer to generate different keyword variations for the same ICP.
    Refines keywords to target e-commerce stores likely to need 3PL.
    """
    description = icp_row.get("ICP Description", "")
    geo = icp_row.get("Target Geography", "USA")
    industry = icp_row.get("Target Industry", "")
    
    # Add variation instruction if seed provided
    variation_instruction = ""
    if variation_seed is not None:
        variation_instruction = f"\n    IMPORTANT: This is variation #{variation_seed}. Generate DIFFERENT keywords than previous runs, exploring alternative angles, synonyms, and related niches."
    
    prompt = f"""
    You are an expert SEO and Lead Generation Specialist for a 3PL (Logistics) company.
    Your goal is to find e-commerce brands that match the following Ideal Customer Profile (ICP).
    
    ICP DESCRIPTION: "{description}"
    TARGET GEOGRAPHY: {geo}
    TARGET INDUSTRY: {industry}
    
    TASK:
    Generate a JSON list of 50-100 high-intent search keywords to find these specific companies on Google.{variation_instruction}
    
    CRITERIA for Keywords:
    1. Target "Storefront" intent (companies selling products), NOT informational articles.
    2. Use specific niches (e.g., instead of "clothing", use "sustainable organic cotton baby clothes USA").
    3. Include "Shopify", "DTC", "Direct to Consumer", "Online Store", "Official Site" variations.
    4. Focus on products that are 'shippable' (physical goods).
    5. Exclude terms likely to find dropshippers if the ICP implies established brands.
    
    FORMAT:
    Return ONLY a JSON object with a key "keywords" containing the list of strings.
    Example: 
    {{
        "keywords": [
            "organic dog treat brands USA",
            "luxury leather handbag online store",
            "sustainable activewear shopify",
            ...
        ]
    }}
    """
    
    try:
        model = GenerativeModel("gemini-2.0-flash-001")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        if response.text:
            text = response.text.strip()
            # Clean markdown
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
                
            data = json.loads(text)
            keywords = data.get("keywords", [])
            logging.info(f"Vertex Generated {len(keywords)} keywords for ICP: {industry}")
            return keywords
            
    except Exception as e:
        logging.error(f"Vertex Keyword Gen failed: {e}")
        return []
