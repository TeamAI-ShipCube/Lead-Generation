# TestScout Configuration Quick Reference

## Main Configuration File: `zcap/config.py`

---

## Lead Generation Settings

### `DAILY_LEAD_TARGET` (default: 10000)
**What it does:** Number of leads to collect before pipeline stops  
**Set to:**
- `50` - Small batch for testing
- `100` - Daily target
- `1000` - Weekly batch
- `10000` - Continuous running (runs until you stop it manually)

**Example:**
```python
DAILY_LEAD_TARGET = 100
```

---

### `MIN_QUALIFICATION_GRADE` (default: 0) **NEW!**
**What it does:** Minimum AI score (1-10) required to save a lead  
**Set to:**
- `0` - Save ALL leads (no filtering)
- `6` - Save decent+ leads only
- `7` - Save good leads only
- `8` - Save only excellent leads

**Example:**
```python
MIN_QUALIFICATION_GRADE = 6  # Only save leads with grade 6+
```

**Impact on results:**
| Setting | Leads/Day | Quality | Use Case |
|---------|-----------|---------|----------|
| 0 (all) | 100+ | Mixed | Manual review later |
| 6+ | 40-60 | Good | Sales outreach |
| 8+ | 10-20 | Excellent | Hot prospects only |

---

## API Limits

### `GOOGLE_SEARCH_DAILY_LIMIT` (default: 100)
**What it does:** Max Google searches per day (free tier limit)  
**Don't change unless:** You upgrade to paid tier

### `HUNTER_MONTHLY_LIMIT` (default: 50)
**What it does:** Max Hunter.io verifications per month (free tier)  
**Don't change unless:** You have paid plan

---

## File Paths

### `INPUT_ICP_FILE` (default: "Input_ICP.csv")
**What it does:** Where to read your ideal customer profiles  
**Change if:** You want to test different ICP sets in parallel

**Example:**
```python
INPUT_ICP_FILE = "Input_ICP_Test.csv"  # Use different file
```

### `OUTPUT_FILE` (default: "Master_Leads.csv")
**What it does:** Main output file for all leads  
**Change if:** Running multiple instances

---

## How to Edit Configuration

### Option 1: Direct Edit (Simple)

```bash
nano zcap/config.py
# Edit the values
# Save and exit (Ctrl+X, Y, Enter)
```

### Option 2: Environment Variable (Advanced)

Some values can be overridden via environment:

```bash
export DAILY_LEAD_TARGET=50
python -m zcap.run
```

---

## Common Configurations

### **Maximum Quality Mode**
Generate only top-tier leads:
```python
DAILY_LEAD_TARGET = 50
MIN_QUALIFICATION_GRADE = 8
```

**Result:** ~10-20 grade 8+ leads per run (may take longer)

---

### **Balanced Mode** (Recommended)
Good mix of quality and quantity:
```python
DAILY_LEAD_TARGET = 100
MIN_QUALIFICATION_GRADE = 6
```

**Result:** ~40-70 grade 6+ leads per run

---

### **Volume Mode**
Collect everything for manual review:
```python
DAILY_LEAD_TARGET = 200
MIN_QUALIFICATION_GRADE = 0
```

**Result:** ~100-200 leads of all grades

---

### **Testing Mode**
Quick test run:
```python
DAILY_LEAD_TARGET = 10
MIN_QUALIFICATION_GRADE = 0
```

**Result:** First 10 leads found, useful for debugging

---

## After Changing Configuration

**Always restart the pipeline:**

```bash
# Stop current run (Ctrl+C)
# Start fresh
python -m zcap.run
```

Changes only apply to NEW runs, not ongoing ones.

---

## Monitoring Configuration Impact

### Check what was used in a run:

```bash
# View run log
grep "Daily target\|MIN_QUALIFICATION" logs/run_*.log
```

### Compare configurations:

```bash
# Count leads by grade
cut -d',' -f8 Master_Leads.csv | sort | uniq -c
```

---

## Advanced: Keyword Freshness

Located in `zcap/run.py` (not config.py):

```python
fresh_keywords = filter_fresh_keywords(keywords, max_usage=3)
#                                                  ^^^^^^^^
```

**Change `max_usage`:**
- `1` - Use each keyword only once (maximum variety)
- `3` - Default (good balance)
- `5` - Reuse keywords more (less variety)

---

## Troubleshooting

### "Not enough leads generated"
- **Lower** `MIN_QUALIFICATION_GRADE` (try 0 or 5)
- **Increase** `DAILY_LEAD_TARGET`
- Check if ICPs are too specific

### "Too many low-quality leads"
- **Raise** `MIN_QUALIFICATION_GRADE` (try 7 or 8)
- Refine ICP descriptions in Input_ICP.csv

### "Pipeline stops immediately"
- Check `DAILY_LEAD_TARGET` - might already be reached
- Check logs for errors

---

*Quick reference for zcap/config.py settings*
