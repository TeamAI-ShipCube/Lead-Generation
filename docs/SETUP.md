# TestScout Setup Guide
## Complete Installation Instructions

---

## Prerequisites

Before starting, ensure you have:

- [ ] Computer with Linux/Mac/Windows
- [ ] Python 3.13 or higher installed
- [ ] Internet connection
- [ ] Google account (for Cloud services)
- [ ] Credit card (for API services - most have free tiers)

---

## Step 1: Install Python & Dependencies

### Check Python Version

```bash
python3 --version
# Should show: Python 3.13.x or higher
```

### Install pip (if not already installed)

```bash
# Linux/Mac
sudo apt-get install python3-pip  # Ubuntu/Debian
brew install python3               # Mac

# Windows
# Download from python.org and install
```

---

## Step 2: Clone/Download Project

```bash
cd ~/Projects/  # Or your preferred location
# If you have the project already, skip to next step
# Otherwise, copy the testScout folder to this location
```

---

## Step 3: Create Virtual Environment

```bash
cd testScout
python3 -m venv venv
```

**Activate the virtual environment:**

```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

---

## Step 4: Install Python Packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**This installs:**
- `vertexai` - Google AI
- `google-api-python-client` - Google Search
- `playwright` - Web scraping
- `python-dotenv` - Environment management
- `requests` - HTTP requests
- And more...

**Install Playwright browsers:**

```bash
playwright install chromium
```

---

## Step 5: Setup Google Cloud

### 5.1 Create Google Cloud Project

1. Go to: https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Project name: `testscout-leads` (or your choice)
4. Click "Create"

### 5.2 Enable Required APIs

```bash
# Install gcloud CLI first if you haven't
# https://cloud.google.com/sdk/docs/install

gcloud config set project testscout-leads

# Enable Vertex AI
gcloud services enable aiplatform.googleapis.com

# Enable Custom Search
gcloud services enable customsearch.googleapis.com
```

**Or enable through console:**
1. APIs & Services → Library
2. Search "Vertex AI API" → Enable
3. Search "Custom Search API" → Enable

### 5.3 Create Service Account

```bash
# Create service account
gcloud iam service-accounts create testscout-sa \
  --display-name="TestScout Service Account"

# Generate credentials file
gcloud iam service-accounts keys create google-credentials.json \
  --iam-account=testscout-sa@testscout-leads.iam.gserviceaccount.com

# Grant Vertex AI permissions
gcloud projects add-iam-policy-binding testscout-leads \
  --member="serviceAccount:testscout-sa@testscout-leads.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

**Move credentials to project:**

```bash
mv google-credentials.json ./testScout/
```

---

## Step 6: Setup Google Custom Search

### 6.1 Get API Key

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" → "API Key"
3. Copy the API key
4. Save it - you'll need it for `.env`

### 6.2 Create Search Engine #1 (Companies)

1. Go to: https://programmablesearchengine.google.com/
2. Click "Add" or "Create"
3. **What to search**: Select "Search the entire web"
4. **Name**: `TestScout Companies`
5. Click "Create"
6. Copy the **Search engine ID** (looks like: `a1b2c3d4e5`)

### 6.3 Create Search Engine #2 (People/LinkedIn)

1. Create another search engine
2. **Sites to search**: Add `linkedin.com/in/*`
3. **Name**: `TestScout People`
4. **Advanced** → Enable "Search only included sites"
5. Click "Create"
6. Copy the **Search engine ID**

---

## Step 7: Setup Hunter.io (Email Verification)

1. Go to: https://hunter.io/
2. Sign up for free account
3. Go to API → API Keys
4. Copy your API key
5. Free tier: 50 searches/month

**Optional APIs** (for enhanced features):
- **Firecrawl**: https://firecrawl.dev/ (alternative scraping)
- **Apollo.io**: https://apollo.io/ (B2B data enrichment)
- **BuiltWith**: https://builtwith.com/ (technology detection)

---

## Step 8: Configure Environment Variables

Create `.env` file in project root:

```bash
cd ~/Projects/testScout
nano .env  # or use any text editor
```

**Add this content** (replace with your actual values):

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=testscout-leads
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/testScout/google-credentials.json

# Google Custom Search
GOOGLE_SEARCH_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXX  # From Step 6.1
GOOGLE_SEARCH_CX_COMPANIES=a1b2c3d4e5f6g7h8i9  # From Step 6.2
GOOGLE_SEARCH_CX_PEOPLE=j9k8l7m6n5o4p3q2r1  # From Step 6.3

# Email Verification
HUNTER_API_KEY=your_hunter_api_key_here  # From Step 7

# Optional APIs (leave blank if not using)
FIRECRAWL_API_KEY=
APOLLO_API_KEY=
BUILTWITH_API_KEY=
```

**Save and close** (Ctrl+X, then Y, then Enter if using nano)

---

## Step 9: Prepare Input File

Edit `Input_ICP.csv`:

```bash
nano Input_ICP.csv
```

**Add your ideal customer profiles:**

```csv
ICP Description,Target Geography,Target Industry,Company Size
"E-commerce brands selling heavy items that struggle with shipping costs",USA,"Furniture, Fitness",10-50 employees
"Subscription box companies needing fast shipping for perishables",USA,"Food & Beverage",5-20 employees
```

---

## Step 10: Test Run

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Set credentials (Linux/Mac)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/testScout/google-credentials.json"

# Run the pipeline
python -m zcap.run
```

**You should see:**
```
2026-01-21 10:00:00 - INFO - Starting run at 20260121_100000
2026-01-21 10:00:01 - INFO - === Processing ICP: Furniture, Fitness ===
2026-01-21 10:00:05 - INFO - Vertex Generated 85 keywords for ICP: Furniture
2026-01-21 10:00:06 - INFO - Searching for companies...
```

**Let it run for 5-10 minutes**, then **press Ctrl+C** to stop.

**Check results:**
```bash
cat Master_Leads.csv
```

You should see leads collected!

---

## Step 11: Verify Setup

Run these checks:

```bash
# Check Google Cloud auth
gcloud auth list
# Should show your service account

# Check Vertex AI access
python3 -c "import vertexai; vertexai.init(project='testscout-leads', location='us-central1'); print('✅ Vertex AI working')"

# Check Playwright
playwright --version
# Should show version number

# Check logs
ls -lh logs/
# Should show log files
```

---

## Troubleshooting Setup Issues

### Issue: "ModuleNotFoundError: No module named 'vertexai'"

**Fix:**
```bash
source venv/bin/activate  # Make sure venv is active
pip install vertexai
```

### Issue: "Permission denied: google-credentials.json"

**Fix:**
```bash
chmod 600 google-credentials.json
```

### Issue: "Playwright browser not found"

**Fix:**
```bash
source venv/bin/activate
playwright install chromium
```

### Issue: "Google Search API quota exceeded"

**Cause:** Free tier limit is 100 queries/day

**Fix:**
- Wait 24 hours
- OR upgrade to paid tier ($5 per 1000 queries)

### Issue: "Vertex AI authentication failed"

**Fix:**
```bash
# Make sure you're using correct project ID
export GOOGLE_CLOUD_PROJECT=testscout-leads
export GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/google-credentials.json"

# Test authentication
gcloud auth activate-service-account --key-file=google-credentials.json
```

---

## Next Steps

After successful setup:

1. **Read User Guide**: `docs/USER_GUIDE.md`
2. **Refine ICPs**: Edit `Input_ICP.csv` with your specific targets
3. **Run Full Pipeline**: Let it collect 50-100 leads
4. **Review Results**: Check `Master_Leads.csv` for quality
5. **Adjust & Iterate**: Refine ICPs based on results

---

## Getting Help

**Setup Issues:**
- Check logs in `logs/` folder
- Review `.env` file for typos
- Ensure all API keys are valid

**API Cost Concerns:**
- Google Custom Search: Free tier 100/day, then $5/1000
- Vertex AI: Pay-per-use (~$0.0001 per request)
- Hunter.io: Free 50/month, then paid plans

**Common Gotchas:**
- Forgetting to activate venv
- Wrong file paths in `.env`
- Missing Playwright browsers
- Incorrect Google Cloud project ID

---

## Uninstallation

To remove TestScout:

```bash
# Deactivate virtual environment
deactivate

# Remove project folder
rm -rf ~/Projects/testScout

# Optional: Delete Google Cloud project
gcloud projects delete testscout-leads
```

---

*Setup completed! Ready to generate leads.* 🚀

*Last Updated: January 2026*
