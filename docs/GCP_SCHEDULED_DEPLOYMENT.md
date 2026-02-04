# GCP Scheduled Deployment Architecture
## Auto-Start, Auto-Stop, Auto-Alert System

---

## Overview

**Concept:** Daily automated lead generation with intelligent cost optimization

**Flow:**
```
6:00 AM → VM starts → Pipeline runs → 100 leads OR 5 hours → VM stops → Email report
```

**Cost Savings:**
- Always-on VM: $30-50/month
- **Scheduled VM (5 hrs/day): $5-8/month** ✅
- **Savings: 85%**

---

## Architecture Diagram

```
┌─────────────────────┐
│  Cloud Scheduler    │ (Triggers at 6:00 AM daily)
│  (Cron: 0 6 * * *)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Compute Engine VM                  │
│  - Auto-starts via startup script   │
│  - Runs TestScout pipeline          │
│  - Target: 100 leads                │
│  - Max runtime: 5 hours              │
└──────────┬──────────────────────────┘
           │
           ├─────────► (Success: 100 leads)
           │           └─► Auto-shutdown
           │           └─► Sync to Google Sheets
           │           └─► Email: "✅ 100 leads generated"
           │
           └─────────► (Timeout: 5 hours reached)
                       └─► Auto-shutdown
                       └─► Email: "⚠️ Only X leads, see logs"
                       └─► Attach log file
```

---

## GCP Services Used

### 1. Cloud Scheduler
**Purpose:** Trigger VM start at 6 AM daily

**Config:**
```yaml
Schedule: 0 6 * * *  # 6:00 AM daily
Timezone: Asia/Kolkata (or your timezone)
Action: Start Compute Engine instance
```

**Cost:** Free (3 jobs/month free tier)

---

### 2. Compute Engine VM
**Purpose:** Run the TestScout pipeline

**Specs:**
- **Machine type:** e2-medium (2 vCPU, 4GB RAM)
- **OS:** Ubuntu 22.04 LTS
- **Disk:** 20GB standard persistent disk
- **Preemptible:** NO (needs to complete the job)

**Cost:**
- Per hour: ~$0.033
- 5 hours/day × 30 days = 150 hours/month
- **Total: ~$5/month**

---

### 3. Cloud Storage
**Purpose:** Store logs and lead CSVs

**Config:**
- Bucket: `testscout-leads`
- Location: Same as VM (lower latency)
- Storage class: Standard

**Cost:** ~$0.50/month for logs + CSVs

---

### 4. Cloud Functions (or Cloud Run)
**Purpose:** Send email alerts

**Trigger:** VM shutdown event
**Runtime:** Python 3.13
**Cost:** Free tier (2M invocations/month)

---

### 5. Google Sheets API
**Purpose:** Real-time lead sync

**Cost:** Free

---

## Total Monthly Cost Breakdown

| Service | Cost/Month | Notes |
|---------|-----------|-------|
| Cloud Scheduler | $0 | Free tier |
| Compute Engine (e2-medium) | $5 | 5 hrs/day × 30 days |
| Cloud Storage | $0.50 | Logs + CSVs |
| Cloud Functions | $0 | Free tier |
| Vertex AI API | $5-10 | Pay per use |
| Google Custom Search | $10 | ~100 queries/day |
| **Total** | **$20-25/month** | **vs $50+ always-on** |

---

## Implementation Plan

### Phase 1: VM Setup (2-3 hours)

#### Step 1.1: Create VM Instance

```bash
gcloud compute instances create testscout-pipeline \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --metadata-from-file=startup-script=startup.sh
```

#### Step 1.2: Create Startup Script (`startup.sh`)

```bash
#!/bin/bash
# This runs EVERY TIME the VM starts

# Log everything
exec > >(tee /var/log/testscout-startup.log)
exec 2>&1

echo "=== TestScout Pipeline Starting at $(date) ==="

# 1. Install dependencies (if not already installed)
if [ ! -d "/opt/testscout" ]; then
    echo "First-time setup..."
    cd /opt
    git clone https://github.com/yourorg/testscout.git
    cd testscout
    
    # Install Python 3.13
    apt-get update
    apt-get install -y python3.13 python3.13-venv
    
    # Setup venv
    python3.13 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    playwright install chromium
fi

# 2. Pull latest code
cd /opt/testscout
git pull origin main

# 3. Set environment variables from metadata
export GOOGLE_APPLICATION_CREDENTIALS="/opt/testscout/google-credentials.json"
export DAILY_LEAD_TARGET=100
export MIN_QUALIFICATION_GRADE=6

# 4. Run pipeline with timeout
source venv/bin/activate

# Start pipeline in background with 5-hour timeout
timeout 5h python -m zcap.run &
PIPELINE_PID=$!

# 5. Monitor and shutdown logic
monitor_and_shutdown() {
    while kill -0 $PIPELINE_PID 2>/dev/null; do
        # Check if target reached
        LEAD_COUNT=$(wc -l < Master_Leads.csv)
        if [ $LEAD_COUNT -ge 100 ]; then
            echo "✅ Target reached: $LEAD_COUNT leads"
            kill $PIPELINE_PID
            send_success_email $LEAD_COUNT
            shutdown_vm
            exit 0
        fi
        sleep 300  # Check every 5 minutes
    done
    
    # Pipeline stopped (either completed or timeout)
    LEAD_COUNT=$(wc -l < Master_Leads.csv)
    
    if [ $LEAD_COUNT -ge 100 ]; then
        send_success_email $LEAD_COUNT
    else
        send_timeout_email $LEAD_COUNT
    fi
    
    shutdown_vm
}

send_success_email() {
    LEADS=$1
    python3 /opt/testscout/scripts/send_alert.py \
        --status="success" \
        --leads=$LEADS \
        --recipient="developer@company.com"
}

send_timeout_email() {
    LEADS=$1
    # Upload logs to Cloud Storage
    gsutil cp /var/log/testscout-startup.log gs://testscout-logs/$(date +%Y%m%d).log
    gsutil cp logs/run_*.log gs://testscout-logs/pipeline_$(date +%Y%m%d).log
    
    python3 /opt/testscout/scripts/send_alert.py \
        --status="timeout" \
        --leads=$LEADS \
        --log-url="gs://testscout-logs/$(date +%Y%m%d).log" \
        --recipient="developer@company.com"
}

shutdown_vm() {
    echo "=== Shutting down VM at $(date) ==="
    # Sync to Google Sheets before shutdown
    python3 /opt/testscout/scripts/sync_to_sheets.py
    
    # Shutdown the VM
    gcloud compute instances stop testscout-pipeline --zone=us-central1-a
}

# Start monitoring
monitor_and_shutdown
```

---

### Phase 2: Email Alert Script (1 hour)

#### Create `scripts/send_alert.py`

```python
#!/usr/bin/env python3
"""
Send email alerts about pipeline status.
Uses SendGrid or Gmail API.
"""

import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(status, leads, log_url=None, recipient="dev@company.com"):
    """
    Send status email.
    
    Args:
        status: "success" or "timeout"
        leads: Number of leads generated
        log_url: GCS URL to log file (for timeout)
        recipient: Email address
    """
    
    from_email = "testscout@yourcompany.com"
    
    if status == "success":
        subject = f"✅ TestScout: {leads} leads generated successfully"
        body = f"""
        Great news!
        
        The TestScout pipeline completed successfully.
        
        Leads Generated: {leads}
        Status: Target reached
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
        View leads: https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID
        
        VM has been automatically shut down.
        """
    else:  # timeout
        subject = f"⚠️ TestScout: Timeout after {leads} leads"
        body = f"""
        Alert: Pipeline timed out after 5 hours.
        
        Leads Generated: {leads} (target was 100)
        Status: Incomplete
        Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        
        Logs: {log_url}
        
        Possible issues:
        - API quota exhausted
        - ICPs too specific (no companies found)
        - Network issues
        - Scraping failures
        
        Please review logs and adjust configuration.
        
        VM has been automatically shut down.
        """
    
    # Send via SendGrid or Gmail
    # ... (implementation depends on ESP choice)
    
    print(f"Email sent to {recipient}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", required=True)
    parser.add_argument("--leads", type=int, required=True)
    parser.add_argument("--log-url", default=None)
    parser.add_argument("--recipient", required=True)
    args = parser.parse_args()
    
    send_email(args.status, args.leads, args.log_url, args.recipient)
```

---

### Phase 3: Cloud Scheduler Setup (30 mins)

#### Create daily schedule

```bash
# Create Cloud Scheduler job
gcloud scheduler jobs create compute start-testscout-daily \
  --schedule="0 6 * * *" \
  --time-zone="Asia/Kolkata" \
  --location=us-central1 \
  --description="Start TestScout pipeline daily at 6 AM" \
  --target-gce-instance=testscout-pipeline \
  --target-gce-instance-zone=us-central1-a \
  --http-method=POST
```

#### Test the schedule

```bash
# Manually trigger (for testing)
gcloud scheduler jobs run start-testscout-daily --location=us-central1

# Check logs
gcloud compute instances get-serial-port-output testscout-pipeline \
  --zone=us-central1-a
```

---

### Phase 4: Google Sheets Sync (1-2 hours)

#### Create `scripts/sync_to_sheets.py`

```python
#!/usr/bin/env python3
"""
Sync Master_Leads.csv to Google Sheets.
Runs before VM shutdown.
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
import csv

SHEET_ID = "YOUR_GOOGLE_SHEET_ID"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def sync_leads_to_sheets():
    """Upload latest leads to Google Sheets."""
    
    # Authenticate
    creds = service_account.Credentials.from_service_account_file(
        '/opt/testscout/google-credentials.json', scopes=SCOPES)
    
    service = build('sheets', 'v4', credentials=creds)
    
    # Read CSV
    with open('Master_Leads.csv', 'r') as f:
        reader = csv.reader(f)
        values = list(reader)
    
    # Clear existing data
    service.spreadsheets().values().clear(
        spreadsheetId=SHEET_ID,
        range='Leads!A1:ZZ'
    ).execute()
    
    # Write new data
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range='Leads!A1',
        valueInputOption='RAW',
        body={'values': values}
    ).execute()
    
    print(f"✅ Synced {len(values)} rows to Google Sheets")

if __name__ == "__main__":
    sync_leads_to_sheets()
```

---

## Advanced Features

### 1. Dynamic Scheduling

Instead of fixed 6 AM, adjust based on timezone of target market:

```bash
# For USA prospects (EST): 9 AM EST = 7:30 PM IST
gcloud scheduler jobs update start-testscout-daily \
  --schedule="30 19 * * *"
```

### 2. Weekend Skip

```bash
# Only run Monday-Friday
--schedule="0 6 * * 1-5"
```

### 3. Smart Retry

If pipeline fails, retry once after 1 hour:

```bash
# Add to startup script
if [ $LEAD_COUNT -lt 50 ]; then
    echo "Too few leads, retrying in 1 hour..."
    sleep 3600
    timeout 5h python -m zcap.run
fi
```

### 4. Slack Notifications

Instead of email, send to Slack:

```python
import requests

def send_slack_alert(status, leads):
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK"
    
    message = {
        "text": f"TestScout: {leads} leads generated",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Status:* {status}\n*Leads:* {leads}"
                }
            }
        ]
    }
    
    requests.post(webhook_url, json=message)
```

---

## Monitoring & Alerting

### 1. Cloud Monitoring Dashboard

Create dashboard to track:
- VM uptime (should be ~5 hrs/day)
- Leads generated per day
- Cost per day
- API quota usage

### 2. Alert Policies

```bash
# Alert if VM runs >6 hours (something wrong)
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="TestScout VM Overtime" \
  --condition-filter='resource.type="gce_instance" AND metric.type="compute.googleapis.com/instance/uptime"' \
  --condition-threshold-value=21600  # 6 hours in seconds
```

---

## Troubleshooting

### Common Issues

**1. VM doesn't start at 6 AM**
- Check Cloud Scheduler logs
- Verify IAM permissions (Scheduler needs `compute.instances.start`)
- Check timezone configuration

**2. Pipeline runs but no leads**
- Check `gs://testscout-logs/` for error logs
- Verify API quotas not exhausted
- Check if ICPs are too specific

**3. VM doesn't shutdown**
- Check startup script logs: `gcloud compute instances get-serial-port-output`
- Verify shutdown command has correct permissions
- Check if process is hung (force shutdown after 6 hours)

**4. Email not received**
- Check SendGrid account is active
- Verify recipient email is correct
- Check spam folder

---

## Cost Optimization Tips

### 1. Use Preemptible VMs (Risky)

**Savings:** 80% cheaper (~$1/month instead of $5)

**Risk:** VM can be shut down mid-run by Google

**Solution:** Save progress every 10 leads, resume if preempted

```python
# In run.py
if leads_count % 10 == 0:
    save_checkpoint(leads_count, current_icp)
```

### 2. Smaller VM

If pipeline is CPU-light, use **e2-small** (2GB RAM):
- Cost: ~$0.017/hour = $2.50/month
- Enough for most pipelines

### 3. Batch Processing

Instead of daily 100 leads:
- Run 3 times/week for 200 leads each
- Fewer cold starts, higher efficiency

---

## Security Considerations

### 1. Service Account Permissions

VM service account should have ONLY:
- `roles/compute.instanceAdmin.v1` (self-shutdown)
- `roles/storage.objectCreator` (upload logs)
- `roles/sheets.editor` (sync to Sheets)

### 2. Credentials Management

Store API keys in **Secret Manager**, not in startup script:

```bash
# Fetch from Secret Manager
export SENDGRID_KEY=$(gcloud secrets versions access latest --secret="sendgrid-api-key")
```

### 3. VPC Network

Put VM in private VPC with Cloud NAT for outbound only (no SSH from internet)

---

## Testing Plan

### Before Production

**1. Test startup script:**
```bash
# SSH into VM
gcloud compute ssh testscout-pipeline --zone=us-central1-a

# Run startup script manually
sudo bash /var/lib/google/startup-script
```

**2. Test email alerts:**
```bash
python3 scripts/send_alert.py \
  --status=timeout \
  --leads=50 \
  --recipient=your-email@company.com
```

**3. Test auto-shutdown:**
```bash
# Let pipeline run for 10 mins, verify it shuts down
```

**4. Test Cloud Scheduler:**
```bash
# Trigger manually, check VM starts
gcloud scheduler jobs run start-testscout-daily
```

---

## Deployment Checklist

- [ ] Create GCP project
- [ ] Enable required APIs (Compute, Scheduler, Sheets)
- [ ] Create service account with correct permissions
- [ ] Upload google-credentials.json to VM
- [ ] Create Cloud Storage bucket for logs
- [ ] Create Google Sheet for leads
- [ ] Configure SendGrid/Gmail for alerts
- [ ] Write startup script
- [ ] Create VM instance
- [ ] Test startup script manually
- [ ] Create Cloud Scheduler job
- [ ] Test end-to-end (manual trigger)
- [ ] Monitor first 3 automated runs
- [ ] Fine-tune timing/quotas
- [ ] Document for team

---

## Comparison: Scheduled vs Always-On

| Factor | Scheduled (Auto Start/Stop) | Always-On |
|--------|---------------------------|-----------|
| **Cost** | $20-25/month | $50-60/month |
| **Complexity** | High (many components) | Low (simple VM) |
| **Reliability** | Medium (more failure points) | High (simple = reliable) |
| **Flexibility** | Can adjust schedule easily | Manual start/stop |
| **Monitoring** | Needs alerts for failures | Can check manually |
| **Best For** | Regular, predictable batch jobs | On-demand, irregular usage |

---

## Recommendation

**Use Scheduled Auto-Scaling if:**
- ✅ You need exactly 100 leads per day (consistent volume)
- ✅ You want hands-off operation
- ✅ Cost savings important (saves $300-400/year)
- ✅ Team is comfortable with GCP

**Use Docker Locally if:**
- ✅ Lead volume varies day-to-day
- ✅ Need to experiment with ICPs frequently
- ✅ Team prefers local control
- ✅ Want to minimize moving parts

---

## Next Steps

I can create:
1. **Complete starter files** (startup.sh, send_alert.py, sync_to_sheets.py)
2. **Deployment script** (one command to set everything up)
3. **Monitoring dashboard** (Terraform config for Cloud Monitoring)

Which would you like me to create first?

---

*This architecture provides 85% cost savings while maintaining full automation!*
