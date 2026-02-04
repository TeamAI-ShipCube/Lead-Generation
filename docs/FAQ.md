# TestScout FAQ
## Frequently Asked Questions

---

## General Questions

### What does TestScout do?

TestScout automatically finds companies that might need your logistics/shipping services. It searches Google, visits their websites, finds decision makers (CEOs, managers), analyzes how good a fit they are, and collects their contact information - all automatically.

### How is this different from buying a list?

**Bought lists** are:
- Outdated (companies change, people leave)
- Generic (not tailored to YOUR ideal customer)
- Shared (competitors have the same list)
- Expensive ($1-5 per lead)

**TestScout** gives you:
- Fresh leads (discovered in real-time)
- Custom (based on YOUR specific ICP descriptions)
- Exclusive (no one else has these exact leads)
- Affordable (~$0.20 per lead in API costs)

### Is this legal/ethical?

Yes, as long as you:
- ✅ Respect robots.txt (which TestScout does)
- ✅ Use publicly available information only
- ✅ Don't overload servers (rate limiting included)
- ✅ Comply with GDPR/CAN-SPAM when emailing leads

**What TestScout does:**
- Searches public Google results
- Visits publicly accessible websites
- Finds information displayed publicly (About Us, Team pages)

**What TestScout does NOT do:**
- Hack into private databases
- Bypass paywalls
- Scrape protected content
- Send emails (only collects contacts)

---

## Usage Questions

### How do I adjust who it finds?

Edit the `Input_ICP.csv` file. The more specific your description, the better the leads.

**Example - Too Vague:**
```csv
"Online retailers in USA"
```
Result: Will find millions of companies, many irrelevant.

**Example - Just Right:**
```csv
"Shopify-based furniture brands doing $2-10M revenue who are growing fast and struggling with shipping delays for heavy/bulky items"
```
Result: Highly targeted, high-quality leads.

### How many leads can I expect per day?

**Depends on:**
1. **ICP specificity**: Niche = fewer but better; Broad = more but mixed quality
2. **API limits**: Free Google Search = 100 queries/day max
3. **Speed setting**: Currently ~30-100 leads/hour

**Typical scenarios:**
- **Small niche** (e.g., "organic dog treat brands in Texas"): 20-50 leads total
- **Medium market** (e.g., "D2C apparel brands USA"): 500-2000 leads
- **Broad category** (e.g., "e-commerce companies"): 10,000+ leads (but lower quality)

### Can I run it continuously?

Yes! The system has anti-stagnation features:
1. **Domain deduplication** - Never processes same company twice
2. **Keyword variation** - AI generates different keywords each loop
3. **Freshness filtering** - Avoids overused search terms

You can run it 24/7 without getting stuck in loops.

### What if I want to process a domain again?

The system prevents re-processing to avoid duplicates. To reset:

```bash
# Warning: This removes ALL deduplication history
rm processed_domains.csv
# Next run will reprocess everything
```

**Better approach**: Create a new, more specific ICP instead of reprocessing.

---

## Data Questions

### What fields are collected?

**Standard fields:**
- Company Name, Website
- First Name, Last Name, Title
- Email, LinkedIn URL
- Qualification Grade (1-10)

**AI-enhanced fields:**
- Why Good? (fit explanation)
- Pain Point (their problem)
- Icebreaker (personalized opener)
- Industry Tags, Tech Stack
- Employee Count, Revenue (if mentioned publicly)
- Shipping Locations, Logistics Signals

See all 26 fields in `Master_Leads.csv` header.

### How accurate are the emails?

**Accuracy by status:**
- **Verified** (Hunter.io confirmed): ~95% accurate
- **Pattern Guess** (firstname@domain): ~60% accurate  
- **No Email Found**: LinkedIn-only + ~0% email accuracy

**Overall**: Approximately 60-80% of leads have a working email.

**Pro tip**: Prioritize "Verified" emails for cold outreach, use LinkedIn for others.

### What does "Qualification Grade" mean?

AI scores each company 1-10 based on 3PL fit:

| Grade | Likelihood | Description |
|-------|-----------|-------------|
| **10** | Very High | Perfect signals (e.g., "we're struggling with fulfillment") |
| **8-9** | High | Strong indicators (recent funding, hiring ops, expanding) |
| **6-7** | Medium | Stable business, might need 3PL |
| **4-5** | Low | Weak signals, possibly dropshippers |
| **1-3** | Very Low | Digital goods, no physical shipping |

**Use case:**
- **Grade 9-10**: Immediate outreach (hot leads)
- **Grade 7-8**: Nurture campaign
- **Grade 5-6**: General newsletter list
- **Grade <5**: Review manually or discard

---

## Technical Questions

### What APIs do I need?

**Required (System won't work without these):**
1. **Google Cloud** - Vertex AI + Custom Search
   - Cost: ~$0.15 per lead
   - Setup: docs/SETUP.md

2. **Hunter.io** - Email verification
   - Free tier: 50/month
   - Cost: $49/month for 500

**Optional (Enhanced features):**
3. **Firecrawl** - Alternative scraping (if Playwright fails)
4. **Apollo.io** - B2B data enrichment
5. **BuiltWith** - Technology detection

### How much does it cost to run?

**API costs per 100 leads:**
- Google Custom Search: $10 (100 queries = $10)
- Vertex AI: $5 (keyword generation + analysis)
- Hunter.io: $5 (email verification)
- **Total: ~$0.20 per lead**

**For 1000 leads/month:** ~$200 in API costs

Compare to:
- Buying lists: $1-5 per lead = $1000-$5000
- ZoomInfo subscription: $10,000/year
- Manual research: 20 mins/lead × $25/hr = $8.33/lead

### Can I run this on Windows?

Yes, but with extra steps:

1. Install Python 3.13 from python.org
2. Use `venv\Scripts\activate` instead of `source venv/bin/activate`
3. Install Playwright: `playwright install chromium`
4. Some paths may need adjustment (use backslashes `\`)

See docs/SETUP.md for detailed Windows instructions.

### What if I don't have Google Cloud?

Google Cloud is required for:
- Vertex AI (keyword generation + lead analysis)
- Custom Search (finding companies)

**Alternative (not recommended):**
- Use OpenAI API instead of Vertex AI (requires code changes)
- Use Bing Search API instead of Google (requires code changes)

This would require significant modifications. Recommended to just set up Google Cloud (free trial available).

---

## Troubleshooting Questions

### "No companies found" - What's wrong?

**Possible causes:**

1. **Too specific ICP**
   - Fix: Broaden your description

2. **Google quota exhausted**
   - Check: `grep "cse().list" logs/run_*.log | wc -l`
   - Fix: Wait24 hours or upgrade to paid

3. **Keywords not generating**
   - Check logs for "Vertex Generated"
   - Fix: Check Vertex AI authentication

4. **All companies already processed**
   - Check: `wc -l processed_domains.csv`
   - Fix: Create new, different ICP

### "Email verification failing" - What to do?

**Check Hunter.io quota:**
```bash
# View their dashboard at hunter.io
# Free tier: 50/month
```

**If quota exceeded:**
- Wait until next month
- Upgrade plan
- Temporarily disable email verification:
  - Email will be "Pattern Guess" instead of "Verified"

### Pipeline keeps stopping - Why?

**Common reasons:**

1. **Internet disconnected**
   - Logs will show: "Connection error"

2. **API quota hit**
   - Logs will show: "Quota exceeded" or "429 error"

3. **Target reached**
   - Logs will show: "Daily target X reached!"

4. **Scraping blocked**
   - Logs will show: "Status 403" or "Cloudflare blocked"
   - System will fallback to Jina AI

5. **Python error**
   - Logs will show: "Traceback" with error details
   - Check logs/run_*.log for specifics

### Leads are low quality - How to improve?

**Quick fixes:**

1. **More specific ICPs**
   ```csv
   # Before:
   "E-commerce companies"
   
   # After:
   "Shopify Plus brands selling furniture/home goods, 
   $2-20M revenue, struggling with shipping costs and 
   delivery times for bulky items"
   ```

2. **Filter by grade**
   ```bash
   # Export only high-grade leads
   grep -E "^[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[^,]*,[89]," Master_Leads.csv > high_quality.csv
   ```

3. **Adjust qualification in code**
   - Edit `zcap/intelligence.py` → `PROMPT_TEMPLATE`
   - Add more weight to specific signals

---

## Advanced Questions

### Can I integrate with my CRM?

Not built-in yet, but easy to do:

**Option 1: Manual Import**
```bash
# Export leads
cp Master_Leads.csv leads_for_salesforce.csv
# Import into CRM using their CSV import tool
```

**Option 2: API Integration** (requires coding)
```python
# In zcap/run.py, after save_lead():
push_to_crm(current_lead)  # Your custom function
```

**Popular CRMs:**
- Salesforce: Use their Bulk API
- HubSpot: Use Contacts API
- Pipedrive: Use Persons API

### Can I add more data sources?

Yes! The system is modular.

**Example: Add Apollo.io enrichment**

1. Create `zcap/apollo_integration.py`:
```python
def enrich_with_apollo(company_domain):
    # Call Apollo API
    return {"employee_count": "50-100", "tech_stack": "Shopify Plus"}
```

2. Update `zcap/run.py`:
```python
# After lead analysis
apollo_data = enrich_with_apollo(domain)
current_lead.update(apollo_data)
```

See docs/TECHNICAL_GUIDE.md for details.

### How do I A/B test ICPs?

**Method 1: Run sequentially**
```csv
# Week 1: Test ICP A
"Furniture brands with shipping issues",USA,"Furniture",

# Week 2: Test ICP B  
"Furniture brands expanding to new markets",USA,"Furniture",
```

Compare lead quality and conversion.

**Method 2: Parallel runs** (requires 2 instances)
```bash
# Terminal 1
INPUT_ICP_FILE=Input_ICP_A.csv python -m zcap.run

# Terminal 2
INPUT_ICP_FILE=Input_ICP_B.csv python -m zcap.run
```

### Can I run multiple instances?

Yes, but be careful:

**To avoid conflicts:**
1. Use different output files:
   ```python
   # In config.py
   OUTPUT_FILE = "Master_Leads_Run2.csv"
   ```

2. Separate Google API keys (to avoid quota conflicts)

3. Different processed_domains files:
   ```python
   # In dedup.py
   PROCESSED_DOMAINS_FILE = "processed_domains_run2.csv"
   ```

**Use case:** Test different ICPs in parallel.

---

## Billing & Costs

### Can I reduce API costs?

Yes:

1. **Use fewer keywords**
   - Edit `intelligence.py` → generate 25-50 instead of 50-100

2. **Lower search frequency**
   - Edit `discovery.py` → `limit_per_keyword=1` instead of 3

3. **Skip email verification**
   - Use "Pattern Guess" instead of Hunter.io

4. **Free tier APIs**
   - Google Cloud: $300 free credit (first time)
   - Hunter: 50 emails/month free

### What's the cheapest setup?

**Ultra-budget config:**
- Google Cloud free trial ($300 credit)
- Hunter.io free tier (50/month)
- Limit queries to 50/day
- **Cost: $0 for first 3 months**

After free trial:
- ~10 leads/day = ~$2/day = $60/month

---

## Best Practices

### Recommended workflow?

**Weekly cycle:**

**Monday:**
- Review last week's leads
- Identify patterns (what worked?)
- Adjust ICPs based on findings

**Tuesday-Friday:**
- Run pipeline 4-8 hours/day
- Export high-grade leads daily
- Import to CRM

**Saturday:**
- Backup `Master_Leads.csv`
- Archive old logs
- Plan next week's ICPs

### How often should I update ICPs?

**Guidelines:**
- New market/product: New ICP
- After 500 leads: Refine existing ICP
- Every quarter: Review and refresh
- When quality drops: Adjust immediately

### What metrics should I track?

**Key performance indicators:**

1. **Leads per hour**: Should be 30-100
2. **Qualification grade distribution**: 40%+ should be 7+
3. **Email accuracy**: 60-80% verified/pattern guess
4. **Conversion rate**: Track from lead → customer
5. **Cost per lead**: Should stay ~$0.20

**Track in spreadsheet:**
```
Date | ICPs | Leads | Grade 8+ | Emails | Cost | Conv Rate
```

---

## Support

### Where do I get help?

**Issues by type:**

**Non-technical:**
- ICP refinement → [Add your contact]
- Lead quality → [Add your contact]

**Technical:**
- Setup problems → docs/SETUP.md
- Errors → docs/TECHNICAL_GUIDE.md
- Bugs → [GitHub issues / your support]

**Emergency:**
- Pipeline completely broken → [Your hotline]

### Can I hire help to set this up?

Yes! This is designed for handoff. Provide contractor:
- docs/SETUP.md (complete setup guide)
- Access to your Google Cloud / Hunter accounts
- Your ICP descriptions

Estimated setup time: 2-4 hours for technical person.

---

*Last Updated: January 2026*
