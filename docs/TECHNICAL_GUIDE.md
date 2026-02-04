# TestScout Technical Documentation
## Architecture & Developer Guide

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Installation & Setup](#installation--setup)
3. [Module Documentation](#module-documentation)
4. [API Configuration](#api-configuration)
5. [Data Flow](#data-flow)
6. [Troubleshooting](#troubleshooting)
7. [Extending the System](#extending-the-system)

---

## System Architecture

### High-Level Overview

```
Input_ICP.csv
    ↓
[ICP Reader] → [Vertex AI Keyword Generator]
    ↓
[Google Custom Search] → [Company Discovery]
    ↓
[Playwright Scraper] → [Website Content]
    ↓
[Vertex AI Analyzer] → [Lead Qualification]
    ↓
[LinkedIn X-Ray / Email Finder] → [Contact Discovery]
    ↓
[Hunter.io Verifier] → [Email Validation]
    ↓
Master_Leads.csv + processed_domains.csv
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Runtime** | Python 3.13 | Core language |
| **AI/ML** | Google Vertex AI (Gemini 2.0 Flash) | Keyword generation, lead analysis |
| **Search** | Google Custom Search API | Company discovery |
| **Scraping** | Playwright + Jina AI | Website content extraction |
| **Email Verification** | Hunter.io | Email validation |
| **Environment** | python-dotenv, venv | Configuration management |

---

## Installation & Setup

### Prerequisites

```bash
# System requirements
- Python 3.13+
- pip
- Node.js (for Playwright)
- Google Cloud Project
- API keys (Google, Hunter.io)
```

### Step 1: Clone & Setup Virtual Environment

```bash
cd /path/to/testScout
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 3: Configure Environment Variables

Create `.env` file:

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/google-credentials.json

# Google Custom Search
GOOGLE_SEARCH_API_KEY=your-api-key
GOOGLE_SEARCH_CX_COMPANIES=your-search-engine-id-1
GOOGLE_SEARCH_CX_PEOPLE=your-search-engine-id-2

# Third-party APIs
HUNTER_API_KEY=your-hunter-key
FIRECRAWL_API_KEY=your-firecrawl-key  # Optional
APOLLO_API_KEY=your-apollo-key        # Optional
BUILTWITH_API_KEY=your-builtwith-key  # Optional
```

### Step 4: Initialize Data Files

```bash
# Creates necessary CSVs
python -m zcap.run
# Press Ctrl+C after it initializes
```

---

## Module Documentation

### Core Modules (`zcap/`)

#### 1. `config.py`
**Purpose**: Configuration management and environment variable loading

**Key Variables:**
- `DAILY_LEAD_TARGET`: Number of leads to collect (default: 10000)
- `INPUT_ICP_FILE`: ICP input file path
- `OUTPUT_FILE`: Main output CSV

**Functions:**
- `check_config()`: Validates required environment variables

---

#### 2. `run.py`
**Purpose**: Main orchestrator - coordinates entire pipeline

**Main Flow:**
```python
def main():
    # 1. Initialize
    init_storage()
    init_dedup_db()
    init_keyword_tracker()
    
    # 2. Load ICPs
    icps = load_from_csv(INPUT_ICP_FILE)
    
    # 3. Loop through ICPs
    for icp in icps:
        # 3a. Generate keywords (AI)
        keywords = generate_keywords_from_icp(icp)
        
        # 3b. Filter fresh keywords
        fresh_keywords = filter_fresh_keywords(keywords)
        
        # 3c. Search companies
        companies = search_with_keywords(fresh_keywords)
        
        # 3d. Process each company
        for company in companies:
            # Scrape → Analyze → Find DM → Verify → Save
```

**Key Loop Variables:**
- `leads_count`: Tracks progress toward target
- `icp_iteration`: Tracks how many times all ICPs processed
- `variation_seed`: Ensures different keywords each iteration

---

#### 3. `intelligence.py`
**Purpose**: Vertex AI integration for keyword generation and lead analysis

**Key Functions:**

##### `generate_keywords_from_icp(icp_row, variation_seed=None)`
Generates 50-100 targeted keywords from ICP description.

**Input:**
```python
icp_row = {
    "ICP Description": "E-commerce furniture brands...",
    "Target Geography": "USA",
    "Target Industry": "Furniture"
}
```

**Output:**
```python
[
    "modern furniture shopify",
    "DTC bedroom furniture brands",
    "sustainable wood furniture online"
]
```

**Variation Mechanism:**
- `variation_seed=0`: First set of keywords
- `variation_seed=1`: Different angle/synonyms
- `variation_seed=2`: Alternative niches

##### `analyze_lead(company_name, website_text, dm_info)`
Analyzes scraped content to qualify lead.

**Returns:**
```python
{
    "qualification_grade": 8,
    "why_good": "Strong growth signals...",
    "pain_point": "Scaling Friction",
    "company_info": "DTC furniture brand...",
    "employee_count": "25-50",
    "industry_tags": "E-commerce, Furniture",
    ...
}
```

---

#### 4. `discovery.py`
**Purpose**: Google Custom Search integration

**Functions:**

##### `search_with_keywords_shuffled(keywords, market, limit_per_keyword)`
Searches Google for companies using keywords.

**Process:**
1. Shuffle keywords randomly
2. Use first 10 keywords
3. Query: `"{keyword}" ("add to cart" OR "checkout") -inurl:blog -site:amazon.com`
4. Return company data: `{title, link, snippet, keyword}`

##### `search_shopify_stores_broad(market, limit, start_index)`
Broad Shopify discovery without specific keywords.

**Query Example:**
```
site:.com "powered by shopify" ("add to cart" OR "shop now")
-site:myshopify.com -site:amazon.com
```

---

#### 5. `scraping.py`
**Purpose**: Website content extraction

**Strategy - Exhaustive Scraping:**
1. **Homepage** (15,000 chars)
2. **About Page** (`/about`, `/about-us`, `/our-story`)
3. **Team Page** (`/team`, `/leadership`, `/our-team`)
4. **Press/News** (`/press`, `/news`, `/blog`)
5. **Careers** (`/careers`, `/jobs`) - hiring signals

**Fallback Chain:**
```
Playwright (full browser)
    ↓ (if fails)
Jina AI (API-based)
    ↓ (if fails)
Basic HTTP request
```

---

#### 6. `identification.py`
**Purpose**: Decision maker discovery

**Strategies (in order):**

1. **Website Text Analysis** (Vertex AI)
   - Parses About/Team pages
   - Extracts names and titles
   - Validates against blocklists

2. **LinkedIn X-Ray Search**
   - Google search: `site:linkedin.com "CEO" "Company Name"`
   - Parses LinkedIn URLs
   - Extracts names from titles

3. **Email-First Approach**
   - Finds emails on website (`mailto:`, regex)
   - Infers names from email (`john.doe@` → John Doe)

---

#### 7. `verification.py`
**Purpose**: Email validation

**Functions:**

##### `verify_lead(first_name, last_name, domain, company_url)`
Attempts to find and verify email address.

**Process:**
1. **Hunter.io Finder**: Query for specific person
2. **Pattern Guess**: `{first}.{last}@{domain}`
3. **Common Patterns**: Try variations (`{first}@`, `{last}@`)
4. **Hunter.io Verify**: Check if email exists

**Return:**
```python
("john.doe@company.com", "Verified")
("john@company.com", "Pattern Guess (Not Verified)")
```

---

#### 8. `storage.py`
**Purpose**: Data persistence (CSV operations)

**Functions:**

##### `save_lead(lead_data, filename=None)`
Saves lead to CSV with validation.

**Validation Checks:**
- First/Last name not empty
- First name not generic (`sales`, `info`, `support`)
- First name ≠ company name

**CSV Headers:**
```python
[
    "First Name", "Last Name", "Title", "Email",
    "LinkedIn URL", "Company", "Company Info",
    "Qualification Grade", "Why Good?", "Pain_Point",
    "Icebreaker", "Status", "Recent updates", "Keyword",
    "Employee Count", "Annual Revenue", "Company Size",
    "Industry Tags", "Social Media", "Contact Details",
    "Logistics Signals", "Brand Vibe", "Tech Stack",
    "Product Profile", "Customer Focus", "Shipping Locations"
]
```

---

#### 9. `dedup.py`
**Purpose**: Duplicate prevention

**Files:**
- `processed_domains.csv`: Tracks every domain processed

**Functions:**

##### `is_domain_processed(domain)` → bool
Checks if domain already processed.

##### `mark_domain_processed(domain, company_name)`
Marks domain as processed with timestamp.

**Format:**
```csv
domain,company_name,processed_at
example.com,Example Inc,2026-01-21 10:00:00
```

---

#### 10. `keyword_tracker.py` *(NEW - Anti-Stagnation)*
**Purpose**: Track keyword usage to prevent exhaustion

**Functions:**

##### `filter_fresh_keywords(keywords, max_usage=3)`
Returns keywords used < `max_usage` times.

**File: `keyword_usage.csv`**
```csv
keyword,last_used,times_used,companies_found
"modern furniture shopify",2026-01-21 09:00,2,15
"DTC furniture brands",2026-01-21 09:30,1,8
```

##### `mark_keyword_used(keyword, companies_found)`
Increments usage counter after search.

---

## Data Flow Diagram

```
┌─────────────────┐
│  Input_ICP.csv  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ Vertex AI Keyword Generator │ (90-100 keywords per ICP)
└────────┬────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Keyword Freshness    │ (Filter overused keywords)
│ Filter               │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Google Custom Search │ (Discover 10-30 companies)
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Domain Deduplication │ (Skip if already processed)
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Company Validation   │ (Vertex AI: Is this a real company?)
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Website Scraping     │ (Playwright: Homepage, About, Team, Press)
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Decision Maker ID    │ (LinkedIn X-Ray, Website parsing, Email inference)
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Lead Analysis        │ (Vertex AI: Grade 1-10, Extract intel)
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│ Email Verification   │ (Hunter.io: Find + Verify)
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Master_Leads.csv    │
└──────────────────────┘
```

---

## API Configuration

### Google Cloud Setup

#### 1. Create Project
```bash
gcloud projects create testscout-leads
gcloud config set project testscout-leads
```

#### 2. Enable APIs
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable customsearch.googleapis.com
```

#### 3. Create Service Account
```bash
gcloud iam service-accounts create testscout-sa
gcloud iam service-accounts keys create google-credentials.json \
  --iam-account=testscout-sa@testscout-leads.iam.gserviceaccount.com
```

#### 4. Grant Permissions
```bash
gcloud projects add-iam-policy-binding testscout-leads \
  --member="serviceAccount:testscout-sa@testscout-leads.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

### Google Custom Search Engines

Create 2 search engines:

**Engine 1: Companies**
- **What to search**: Entire web
- **Sites to search**: (leave empty for whole web)
- **Advanced**: Enable "Search the entire web"

**Engine 2: People (LinkedIn)**
- **Sites to search**: `linkedin.com/in/*`
- **Advanced**: Image search OFF

---

## Troubleshooting

### Common Errors

#### 1. `ImportError: cannot import name 'INPUT_KEYWORDS_FILE'`
**Cause**: File was renamed from `INPUT_KEYWORDS_FILE` to `INPUT_ICP_FILE`

**Fix**:
```python
# In zcap/storage.py, line 4:
from .config import INPUT_ICP_FILE, OUTPUT_FILE  # ✅ Correct
from .config import INPUT_KEYWORDS_FILE, OUTPUT_FILE  # ❌ Old
```

#### 2. `Playwright Browser Missing`
**Cause**: Chromium not installed

**Fix**:
```bash
source venv/bin/activate
playwright install chromium
```

#### 3. `Vertex AI Authentication Error`
**Cause**: Google credentials not set

**Fix**:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/google-credentials.json"
# OR add to .env file
```

#### 4. `Google Search API Quota Exceeded`
**Cause**: 100 queries/day limit reached

**Fix**:
- Wait 24 hours for reset
- OR upgrade to paid tier
- OR create multiple API keys and rotate

---

## Extending the System

### Adding a New Data Source

**Example: Add Apollo.io integration**

1. **Create module**: `zcap/apollo_integration.py`
```python
def enrich_with_apollo(company_name, domain):
    # API call to Apollo
    return enriched_data
```

2. **Update `run.py`**:
```python
# After lead analysis
apollo_data = enrich_with_apollo(c_name, domain)
current_lead.update(apollo_data)
```

3. **Add to CSV headers** in `storage.py`

### Adding Custom Validation Rules

**Location**: `zcap/storage.py` → `save_lead()`

```python
# Add before saving
if lead_data.get("Qualification Grade", 0) < 5:
    logging.info("Rejecting low-grade lead")
    return False
```

### Modifying Keyword Generation

**Location**: `zcap/intelligence.py` → `generate_keywords_from_icp()`

**Change prompt to generate more/fewer keywords:**
```python
TASK:
Generate a JSON list of 150-200 high-intent search keywords...
#                    ^^^^^^^^ Increase from 50-100
```

---

## Performance Optimization

### Current Bottlenecks

1. **Playwright scraping**: ~5-10s per company
2. **Vertex AI calls**: ~2-3s per call (keyword gen + analysis)
3. **Google Search**: Rate limited to 100/day

### Optimization Strategies

1. **Parallel Processing**:
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_company, c) for c in companies]
```

2. **Caching**:
```python
# Cache Vertex AI responses for same company
@lru_cache(maxsize=1000)
def analyze_lead_cached(company_name, text_hash):
    return analyze_lead(company_name, text)
```

3. **API Key Rotation**:
```python
GOOGLE_API_KEYS = [key1, key2, key3]
current_key_index = 0

def get_next_api_key():
    global current_key_index
    key = GOOGLE_API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(GOOGLE_API_KEYS)
    return key
```

---

## Monitoring & Logging

### Log Files

**Location**: `logs/run_YYYYMMDD_HHMMSS.log`

**Log Levels:**
- `INFO`: Normal operations
- `WARNING`: Recoverable errors (scraping failed, fallback used)
- `ERROR`: Critical errors (API failures, config issues)

### Monitoring Commands

```bash
# Watch live log
tail -f logs/run_$(ls -t logs/ | head -1)

# Count leads generated
grep "Lead saved" logs/run_*.log | wc -l

# Find errors
grep "ERROR" logs/run_*.log

# Track keyword performance
grep "Keyword.*found" logs/run_*.log | sort | uniq -c
```

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "=== TestScout Health Check ==="

# Check if running
pgrep -f "python -m zcap.run" && echo "✅ Pipeline running" || echo "❌ Pipeline not running"

# Check lead count
echo "Total leads: $(wc -l < Master_Leads.csv)"

# Check last run time
echo "Last run: $(ls -t logs/ | head -1)"

# Check API quotas
echo "Google searches today: $(grep "Searching for companies" logs/run_$(date +%Y%m%d)*.log 2>/dev/null | wc -l)"
```

---

## Deployment Checklist

### Pre-Production

- [ ] Test on sample ICP (1-2 companies)
- [ ] Verify all API keys work
- [ ] Check Google Cloud quotas
- [ ] Review scraping ethics / robots.txt compliance
- [ ] Set appropriate `DAILY_LEAD_TARGET`

### Production Launch

- [ ] Start with conservative target (50 leads)
- [ ] Monitor logs for first hour
- [ ] Verify lead quality (check grade distribution)
- [ ] Adjust ICP based on results
- [ ] Scale up target gradually

### Maintenance

- [ ] Weekly: Review lead quality, adjust ICPs
- [ ] Monthly: Check API usage/costs
- [ ] Quarterly: Update dependencies (`pip install --upgrade`)

---

*Last Updated: January 2026*
*Maintainer: [Your Name]*
