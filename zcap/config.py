import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
GOOGLE_SEARCH_CX_COMPANIES = os.getenv("GOOGLE_SEARCH_CX_COMPANIES") # Search engine for companies
GOOGLE_SEARCH_CX_PEOPLE = os.getenv("GOOGLE_SEARCH_CX_PEOPLE")       # Search engine for LinkedIn/People
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Keep for backwards compat if needed, or remove if strict Vertex
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
HUNTER_API_KEY = os.getenv("HUNTER_API_KEY") # Optional, for fallback
BUCKET_NAME = os.getenv("BUCKET_NAME", "shipcube-leads-inbox")

# Enhanced API Keys
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")
BUILTWITH_API_KEY = os.getenv("BUILTWITH_API_KEY")

# Limits
DAILY_LEAD_TARGET = 1000  # Very high target - run continuously until manually stopped
GOOGLE_SEARCH_DAILY_LIMIT = 1000
HUNTER_MONTHLY_LIMIT = 50

# Quality Control
MIN_QUALIFICATION_GRADE = 1  # Minimum grade to save lead (0-10). Set to 0 to save all leads, 6+ for quality filtering

# Google Sheets Integration
ENABLE_SHEETS_SYNC = os.getenv("ENABLE_SHEETS_SYNC", "false").lower() == "true"
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")  # Extract from Google Sheets URL
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Files
INPUT_ICP_FILE = "Input_ICP.csv"
OUTPUT_FILE = "Master_Leads.csv"

# Configuration Check
def check_config():
    missing = []
    if not GOOGLE_SEARCH_API_KEY:
        missing.append("GOOGLE_SEARCH_API_KEY")
    if not GOOGLE_SEARCH_CX_COMPANIES:
        missing.append("GOOGLE_SEARCH_CX_COMPANIES")
    
    # Check for Project ID for Vertex AI
    if not GOOGLE_CLOUD_PROJECT:
        missing.append("GOOGLE_CLOUD_PROJECT")
    
    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
