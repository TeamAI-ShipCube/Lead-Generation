# TestScout Lead Generation System
## Quick Start Guide for Non-Technical Users

---

## What is TestScout?

TestScout is an **automated lead generation system** that finds potential customers (companies) who might need your shipping/logistics services. Instead of manually searching Google, this system does it automatically 24/7.

## How It Works (Simple Explanation)

Think of it like a smart robot assistant that:

1. **Reads your ideal customer description** (from a file you edit)
2. **Generates 100+ search keywords** using AI
3. **Searches Google** for companies matching those keywords
4. **Visits their websites** to collect information
5. **Finds decision makers** (CEOs, founders, managers)
6. **Analyzes fit** (rates companies 1-10)
7. **Verifies email addresses**
8. **Saves everything to a spreadsheet** (CSV file)

## What You Need

- **Computer** with internet connection
- **Google Cloud account** (for AI and search)
- **Basic CSV editing skills** (Excel/Google Sheets)

---

## Daily Operations

### Starting the System

1. Open Terminal (command line)
2. Navigate to the project folder:
   ```bash
   cd /path/to/testScout
   ```
3. Run the pipeline:
   ```bash
   source venv/bin/activate
   python -m zcap.run
   ```
4. **That's it!** The system runs automatically until you press `Ctrl+C` or 200 successful leads are generated.

### Editing Your Target Customers (ICPs)

**File to edit**: `Input_ICP.csv`

Open with Excel/Google Sheets and modify:

| Column | What to Write | Example |
|--------|--------------|---------|
| **ICP Description** | Detailed description of your ideal customer | "E-commerce brands selling furniture who struggle with shipping delays" |
| **Target Geography** | Where they're located | "USA" or "UK" or "Global" |
| **Target Industry** | Industry/category | "Furniture, Home Decor" |
| **Company Size** | Size of company | "10-50 employees" or "Mid-Market" |

**Tips:**
- The more specific your description, the better leads you get
- You can have multiple ICPs (rows)
- Save the file after editing
- Restart the pipeline to use new ICPs

### Viewing Your Leads

**Main File**: `Master_Leads.csv`

Open with Excel/Google Sheets to see all leads collected.

**Columns explained:**
- **Company**: Company name
- **First Name / Last Name**: Decision maker's name
- **Email**: Their email address
- **Qualification Grade**: 1-10 score (higher = better fit)
- **Why Good?**: AI explanation of why they're a good prospect
- **Pain_Point**: Problem they're facing
- **Icebreaker**: Suggested opening line for outreach

**Pro tip**: Sort by "Qualification Grade" (descending) to see best leads first!

---

## Common Questions

### Q: How many leads will I get?

**A:** The system target is set in the configuration. Currently: **200 leads** (runs until you stop it).

### Q: How long does it take?

**A:** Typically **30-100 leads per hour**, depending on:
- How specific your ICPs are
- Internet speed
- Google API limits

### Q: What if I get duplicate companies?

**A:** The system automatically prevents duplicates using `processed_domains.csv`. Each company is only processed once, ever.

### Q: The system stopped working!

**A:** Check the latest log file in the `logs/` folder. Look for errors. Common issues:
- Internet connection lost
- Google API quota exhausted (resets daily)
- Website blocking our scraper

---

## Understanding the Results

### Qualification Grades

| Grade | Meaning | Action |
|-------|---------|--------|
| **9-10** | Perfect fit! | Contact immediately |
| **7-8** | Strong prospect | Prioritize in outreach |
| **5-6** | Decent fit | Consider for campaigns |
| **1-4** | Weak fit | Review manually or skip |

### Status Field

| Status | Meaning |
|--------|---------|
| **Verified** | Email found and verified |
| **Pattern Guess** | Email guessed (firstname@company.com) |
| **No Email Found** | Couldn't find email, but has LinkedIn |
| **Scraping Failed** | Couldn't access website |

---

## Daily Workflow (Recommended)

**Morning:**
1. Check `Master_Leads.csv` for new leads
2. Export high-grade leads (8-10) to your CRM
3. Review any errors in logs

**Afternoon:**
4. Adjust ICPs if needed (refine descriptions)
5. Restart pipeline if stopped

**Evening:**
6. Monitor progress (check lead count)
7. Let it run overnight

---

## Getting Help

### Non-Technical Issues
- **Can't find the file?** → Check your testScout project folder
- **CSV looks weird?** → Open with Excel, not Notepad
- **Leads are low quality?** → Refine your ICP descriptions (be more specific)

### Technical Issues
- **System won't start?** → See Technical Guide (docs/TECHNICAL_GUIDE.md)
- **API errors?** → Check Google Cloud console for quota
- **Python errors?** → Contact technical support

---

## Files You Should Know

| File | What It Is | Can I Edit? |
|------|-----------|-------------|
| `Input_ICP.csv` | Your target customers | ✅ YES - Edit anytime |
| `Master_Leads.csv` | All leads collected | ❌ NO - View only |
| `processed_domains.csv` | Duplicate tracker | ❌ NO - Auto-managed |
| `.env` | API keys and secrets | ⚠️ CAREFUL - Only if you know what you're doing |

---

## Pro Tips

1. **Start Specific, Then Broaden**
   - Week 1: Very specific ICP ("Shopify furniture brands in Texas")
   - Week 2: Broaden ("Furniture e-commerce nationwide")

2. **Quality Over Quantity**
   - Better to have 50 perfect leads than 500 mediocre ones
   - Use qualification grades to filter

3. **Refresh ICPs Weekly**
   - Markets change, so update your ICPs
   - Add new industries you discover

4. **Backup Regularly**
   - Copy `Master_Leads.csv` to Google Drive weekly
   - Export to your CRM to avoid losing data

---

## Support Contacts

**For Non-Technical Questions:**
- Lead quality issues
- ICP refinement advice
- General usage questions

**For Technical Questions:**
- System crashes
- API errors
- Installation issues

*(Add your contact information here)*

---

## Quick Reference Card

**Start System:**
```bash
cd /path/to/testScout
source venv/bin/activate
python -m zcap.run
```

**Stop System:**
Press `Ctrl+C`

**View Leads:**
Open `Master_Leads.csv` in Excel

**Edit ICPs:**
Open `Input_ICP.csv` in Excel

**Check Logs:**
Look in `logs/` folder for latest `run_*.log`

---

*Last Updated: January 2026*
