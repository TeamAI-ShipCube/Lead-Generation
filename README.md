# Lead Generation Engine (GCP)

## Overview
This repository contains the **Shipcube Lead Generation Engine**, a cloud-native system designed to automatically discover, qualify, and store potential B2B leads for logistics and 3PL outreach.

The solution has been fully migrated from a local Python scraper to a **Google Cloud Run Job–based architecture**, removing laptop dependency and enabling scheduled, scalable execution.

The engine identifies e-commerce and DTC brands, analyzes their business signals, extracts decision-maker information, and optionally syncs qualified leads to **Google Sheets** for sales consumption.

---

## What This System Does
1. Discovers companies using Google Custom Search (brand, DTC, Shopify, category-based queries)
2. Scrapes and analyzes company websites (About, Team, Products)
3. Identifies potential logistics or scaling signals
4. Extracts contact and LinkedIn information (when available)
5. Scores and qualifies leads
6. Stores outputs as CSV and optionally syncs to Google Sheets
7. Runs fully automated on Google Cloud Run (on-demand or scheduled)

---

## Types of Leads Extracted
- E-commerce / DTC brands  
- Shopify-based stores  
- Consumer goods, food, fitness, fashion, accessories  
- Companies showing growth or scaling friction  
- Businesses likely to need 3PL / fulfillment services  

---

## Lead Data Fields
Each lead typically includes:
1. Company name  
2. Website  
3. Category / industry  
4. Business description  
5. Qualification score  
6. Identified pain point or opportunity  
7. Contact person (when available)  
8. LinkedIn profile  
9. Outreach suggestion  

---

## Tech Stack
- Python 3.12  
- Google Cloud Run (Jobs)  
- Google Cloud Build  
- Google Secret Manager  
- Google Custom Search API  
- Google Sheets API  
- Docker  
- GitHub (TeamAI organization)  

---

## Authentication & Security Model
- No service account JSON files are committed  
- Cloud Run uses IAM-based authentication  
- API keys (Google Search, etc.) are stored in Secret Manager  
- Environment variables are injected at runtime  
- Google Sheets access is granted by sharing the sheet with the Cloud Run service account  

---

## Required Environment Variables
Configured directly on the Cloud Run Job:

- `GOOGLE_SEARCH_API_KEY` (via Secret Manager)  
- `GOOGLE_SEARCH_CX_COMPANIES`  
- `GOOGLE_SEARCH_CX_PEOPLE`  
- `GOOGLE_CLOUD_PROJECT`  
- `GOOGLE_CLOUD_LOCATION`  
- `ENABLE_SHEETS_SYNC`  
- `GOOGLE_SHEET_ID`  

---

## Cloud Run Job Management

### Update Environment Variables & Secrets
```bash
gcloud run jobs update shipcube-lead-gen \
  --region us-central1 \
  --set-env-vars \
ENABLE_SHEETS_SYNC=true,\
GOOGLE_SHEET_ID=<SHEET_ID>,\
GOOGLE_SEARCH_CX_COMPANIES=<CX_ID>,\
GOOGLE_SEARCH_CX_PEOPLE=<CX_ID>,\
GOOGLE_CLOUD_PROJECT=<PROJECT_ID>,\
GOOGLE_CLOUD_LOCATION=us-central1 \
  --set-secrets GOOGLE_SEARCH_API_KEY=google-search-api-key:latest

To Run the job
gcloud run jobs execute shipcube-lead-gen --region us-central1

