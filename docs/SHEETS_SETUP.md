# Google Sheets Auto-Sync Setup
## Quick Configuration Guide

---

## Overview

Every lead generated will automatically sync to your Google Sheet in real-time!

**What gets synced:**
- All 26 lead fields (name, email, company, etc.)
- Timestamp of when added
- Appends as new row (never overwrites)

---

## Step-by-Step Setup (10 minutes)

### Step 1: Create Google Sheet

1. Go to: https://sheets.google.com
2. Create a new blank spreadsheet
3. Name it: `TestScout Leads` (or whatever you prefer)
4. **Copy the Sheet ID from URL:**

```
https://docs.google.com/spreadsheets/d/1abc123XYZ456-def789/edit
                                        ^^^^ THIS PART ^^^^
```

**Example:** If URL is:  
`https://docs.google.com/spreadsheets/d/1iJKb8_TY3zX9wLqMnOpR4sT6uVw8xYz/edit`

**Sheet ID is:** `1iJKb8_TY3zX9wLqMnOpR4sT6uVw8xYz`

---

### Step 2: Share Sheet with Service Account

1. Open your Google Sheet
2. Click **Share** button (top right)
3. Add this email (from your google-credentials.json):
   ```
   testscout-sa@your-project-id.iam.gserviceaccount.com
   ```
   
   **To find it:**
   ```bash
   cat google-credentials.json | grep client_email
   # Look for: "client_email": "testscout-sa@..."
   ```

4. Set permission to **Editor**
5. Uncheck "Notify people"
6. Click **Share**

---

### Step 3: Configure TestScout

Edit your `.env` file:

```bash
nano .env   # or any text editor
```

**Add these lines:**

```bash
# Google Sheets Integration
ENABLE_SHEETS_SYNC=true
GOOGLE_SHEET_ID=1iJKb8_TY3zX9wLqMnOpR4sT6uVw8xYz    # Use YOUR Sheet ID
```

**Save the file.**

---

### Step 4: Test It

```bash
# Run pipeline
docker-compose up

# Or if running locally:
python -m zcap.run
```

**Watch the logs:**
```
✅ Google Sheets API initialized for sheet: 1abc...
✅ Initialized headers in sheet: Leads
✅ Synced lead to Google Sheets: Example Company
```

**Open your Google Sheet** - you should see leads appearing automatically! 🎉

---

## What You'll See in Google Sheets

### Headers (automatically created):
```
First Name | Last Name | Title | Email | LinkedIn URL | Company | ...
```

### Data (auto-populated):
```
John | Doe | CEO | john@example.com | linkedin.com/in/johndoe | Example Co | ...
```

### Timestamp Column:
```
2026-01-21 21:50:00
```

Every new lead = new row added automatically!

---

## Troubleshooting

### "Failed to initialize Google Sheets API"

**Check:**
1. Is `google-credentials.json` in the project folder?
2. Is service account email correct?
3. Did you share the sheet with the service account?

**Test manually:**
```bash
cat google-credentials.json | grep client_email
# Copy that email and share Sheet with it
```

---

### "Permission denied" or "403 error"

**Fix:**
1. Open Google Sheet
2. Click Share
3. Make sure service account email is listed with **Editor** permission

---

### "Rate limit exceeded"

Google Sheets API limits:
- 60 requests per minute per user
- 500 requests per 100 seconds per project

**Solution:** Pipeline already has built-in retry logic with backoff.

If generating >60 leads/minute, consider batch mode (automatically handled).

---

### Leads not appearing in Sheet

**Check logs:**
```bash
grep "Sheets" logs/run_*.log
```

**If you see "ENABLE_SHEETS_SYNC=false":**
- Edit `.env`
- Set `ENABLE_SHEETS_SYNC=true`
- Save and restart

---

## Disabling Auto-Sync

Edit `.env`:
```bash
ENABLE_SHEETS_SYNC=false
```

Leads will still save to CSV, just won't sync to Sheets.

---

## Viewing Data

### Real-Time Viewing

**While pipeline runs:**
1. Open Google Sheet in browser
2. Refresh to see new leads (updates within seconds)

### Sharing with Team

1. Share Google Sheet with teammates
2. They can view/edit leads in real-time
3. Everyone sees same data instantly

### Sorting & Filtering

Use Google Sheets built-in features:
- Sort by Qualification Grade (highest first)
- Filter by Status = "Verified"
- Conditional formatting for grades 8-10

---

## Advanced: Multiple Sheets

Want separate sheets for different ICPs?

**Option 1: Multiple tabs**
- Modify `sheets_sync.py`
- Change `sheet_name` parameter
- Use `sheet_name=f"ICP_{icp.get('Target Industry')}"`

**Option 2: Multiple spreadsheets**
- Create multiple sheets
- Use different `GOOGLE_SHEET_ID` per run
- Run multiple Docker containers

---

## Cost

**Google Sheets API:** FREE ✅
- No charge for API calls
- Unlimited syncs
- Standard Google Sheets storage limits apply

---

## Privacy & Security

**Who can see the data?**
- Only people you explicitly share the Sheet with
- Service account doesn't give anyone access
- Sheet remains private unless you share it

**Best practices:**
- Don't share Sheet publicly
- Use workspace domain (yourcompany.com)
- Regularly review shared users

---

## Verification

**Confirm it's working:**

```bash
# Run pipeline for 5 minutes
docker-compose up

# Stop it (Ctrl+C)

# Check Google Sheet
# Should have new leads with timestamps
```

**If working:** ✅ You're done!

---

## Quick Reference

```bash
# Enable
ENABLE_SHEETS_SYNC=true
GOOGLE_SHEET_ID=your-sheet-id-here

# Disable  
ENABLE_SHEETS_SYNC=false

# Get Sheet ID
# From URL: docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit

# Share Sheet
# With: your-service-account@project-id.iam.gserviceaccount.com
# Permission: Editor
```

---

**Now your leads automatically sync to Google Sheets!** 📊

No manual CSV exports needed! Your team sees leads in real-time!

*Last Updated: January 2026*
