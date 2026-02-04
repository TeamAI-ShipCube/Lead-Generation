# TestScout Docker Deployment Guide
## Complete Installation & Usage Instructions

---

## What's Included

This Docker package contains **everything** you need to run TestScout:
- ✅ Python 3.13
- ✅ All Python dependencies (Vertex AI, Playwright, etc.)
- ✅ Playwright browser (Chromium)
- ✅ System libraries
- ✅ TestScout application code

**One command to run everything!**

---

## Table of Contents

1. [Install Docker Desktop](#step-1-install-docker-desktop)
2. [Setup TestScout](#step-2-setup-testscout)
3. [Run the Pipeline](#step-3-run-the-pipeline)
4. [View Results](#step-4-view-results)
5. [Troubleshooting](#troubleshooting)

---

## Step 1: Install Docker Desktop

### For Windows

#### Option A: Using Installer (Recommended)

1. **Download Docker Desktop**
   - Go to: https://www.docker.com/products/docker-desktop/
   - Click "Download for Windows"
   - File size: ~500MB

2. **System Requirements**
   - Windows 10/11 (64-bit)
   - WSL 2 enabled (Docker will help you enable it)
   - Virtualization enabled in BIOS
   - 4GB RAM minimum (8GB recommended)

3. **Run Installer**
   - Double-click `Docker Desktop Installer.exe`
   - Check "Use WSL 2 instead of Hyper-V" (recommended)
   - Click "OK"
   - Wait for installation (5-10 minutes)

4. **Restart Computer**
   - Required after installation

5. **Start Docker Desktop**
   - Search for "Docker Desktop" in Start Menu
   - Run it
   - Accept the service agreement
   - Wait for "Docker Desktop is running" (green icon in system tray)

6. **Verify Installation**
   ```powershell
   # Open PowerShell and run:
   docker --version
   # Should show: Docker version 24.x.x or higher
   
   docker-compose --version
   # Should show: Docker Compose version 2.x.x or higher
   ```

#### Option B: Using Winget (Windows 11)

```powershell
# Open PowerShell as Administrator
winget install Docker.DockerDesktop
```

#### Troubleshooting: Enable WSL 2

If installation asks you to enable WSL 2:

```powershell
# Run in PowerShell as Administrator
wsl --install
# Restart computer
```

---

### For Mac

#### Option A: Using Installer (Recommended)

1. **Download Docker Desktop**
   - Go to: https://www.docker.com/products/docker-desktop/
   - Choose your Mac type:
     - **Mac with Intel chip**: Download "Mac with Intel chip"
     - **Mac with Apple chip (M1/M2/M3)**: Download "Mac with Apple chip"

2. **System Requirements**
   - macOS 11 or newer
   - 4GB RAM minimum (8GB recommended)

3. **Install**
   - Open the downloaded `.dmg` file
   - Drag "Docker.app" to Applications folder
   - Open Applications → Docker
   - Click "Open" when macOS asks for confirmation

4. **First Launch**
   - Docker will ask for privileged access
   - Enter your Mac password
   - Accept service agreement
   - Wait for "Docker Desktop is running" (whale icon in menu bar)

5. **Verify Installation**
   ```bash
   # Open Terminal and run:
   docker --version
   docker-compose --version
   ```

#### Option B: Using Homebrew

```bash
brew install --cask docker
open -a Docker  # Start Docker Desktop
```

---

### For Linux (Ubuntu/Debian)

#### Complete Installation

```bash
# 1. Update package index
sudo apt-get update

# 2. Install dependencies
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 3. Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 4. Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. Add your user to docker group (avoid using sudo)
sudo usermod -aG docker $USER

# 7. Log out and log back in (or run:)
newgrp docker

# 8. Verify installation
docker --version
docker compose version  # Note: 'compose' not 'docker-compose' on newer versions
```

#### For Other Linux Distributions

**Fedora:**
```bash
sudo dnf install docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

**Arch Linux:**
```bash
sudo pacman -S docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

---

## Step 2: Setup TestScout

### 2.1 Get the TestScout Files

**Option A: If you have the project folder**
```bash
# Navigate to the testScout directory
cd /path/to/testScout
```

**Option B: If you have a zip file**
```bash
# Extract the zip
unzip testscout.zip
cd testScout
```

**Option C: If you have Git access**
```bash
git clone <repository-url>
cd testScout
```

---

### 2.2 Verify Required Files

Make sure these files exist:

```bash
# Check for required files
ls -la

# You should see:
# - Dockerfile
# - docker-compose.yml
# - .dockerignore
# - Input_ICP.csv
# - .env.example
# - requirements.txt
# - zcap/ (folder)
```

---

### 2.3 Setup Environment Variables

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env file with your API keys
nano .env   # or use any text editor
```

**Add your API keys to `.env`:**

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/app/google-credentials.json

# Google Custom Search
GOOGLE_SEARCH_API_KEY=AIzaSy...
GOOGLE_SEARCH_CX_COMPANIES=abc123...
GOOGLE_SEARCH_CX_PEOPLE=xyz789...

# Email Verification
HUNTER_API_KEY=your-hunter-key

# Optional
FIRECRAWL_API_KEY=
APOLLO_API_KEY=
```

---

### 2.4 Add Google Credentials

```bash
# Copy your google-credentials.json to the project root
cp /path/to/your/google-credentials.json ./
```

---

### 2.5 Edit Your ICPs

Edit `Input_ICP.csv` with your target customer profiles:

```bash
nano Input_ICP.csv
```

**Example:**
```csv
ICP Description,Target Geography,Target Industry,Company Size
"D2C furniture brands struggling with shipping",USA,"Furniture, Home Decor",10-50 employees
```

---

## Step 3: Run the Pipeline

### One-Command Setup and Run

```bash
# Build the Docker image and run (first time)
docker-compose up --build

# This will:
# 1. Build the Docker image (~10-15 minutes first time)
# 2. Install all dependencies
# 3. Start the pipeline
# 4. Generate leads until target reached
```

**What you'll see:**
```
Creating network "testscout_default" ...
Building testscout
Step 1/12 : FROM python:3.13-slim
...
Successfully built abc123def456
Starting testscout-pipeline ...
testscout-pipeline | 2026-01-21 21:00:00 - INFO - Starting run at 20260121_210000
testscout-pipeline | 2026-01-21 21:00:01 - INFO - === Processing ICP: Furniture ===
testscout-pipeline | 2026-01-21 21:00:05 - INFO - Vertex Generated 87 keywords
...
```

---

### Subsequent Runs

After the first build, you can run with:

```bash
# Simple run
docker-compose up

# Run in background (detached mode)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the pipeline
docker-compose down
```

---

### Alternative: Run Without Docker Compose

```bash
# Build the image
docker build -t testscout:latest .

# Run the container
docker run -it --rm \
  -v $(pwd)/Input_ICP.csv:/app/Input_ICP.csv \
  -v $(pwd)/Master_Leads.csv:/app/Master_Leads.csv \
  -v $(pwd)/leads:/app/leads \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/google-credentials.json:/app/google-credentials.json \
  testscout:latest
```

---

## Step 4: View Results

### While Running

**Monitor progress:**
```bash
# View live logs
docker-compose logs -f testscout

# Check lead count
wc -l Master_Leads.csv
```

### After Completion

**View leads:**
```bash
# Open in Excel/Sheets
open Master_Leads.csv  # Mac
start Master_Leads.csv  # Windows
xdg-open Master_Leads.csv  # Linux

# Or view in terminal
head -20 Master_Leads.csv
```

**Check logs:**
```bash
# View latest log
tail -100 logs/run_*.log

# Search for errors
grep "ERROR" logs/run_*.log
```

---

## Advanced Usage

### Run with Custom Settings

**Change lead target:**
```bash
# Edit docker-compose.yml
environment:
  - DAILY_LEAD_TARGET=50

# Or pass as environment variable
docker-compose run -e DAILY_LEAD_TARGET=50 testscout
```

**Run with specific ICP file:**
```bash
docker-compose run \
  -v $(pwd)/Input_ICP_Test.csv:/app/Input_ICP.csv \
  testscout
```

---

### Schedule Runs (Optional)

**On Linux/Mac (using cron):**
```bash
# Edit crontab
crontab -e

# Add line to run daily at 6 AM
0 6 * * * cd /path/to/testScout && docker-compose up
```

**On Windows (using Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 6:00 AM
4. Action: Start a program
   - Program: `docker-compose`
   - Arguments: `up`
   - Start in: `C:\path\to\testScout`

---

## Stopping and Cleanup

### Stop the Pipeline

```bash
# Stop gracefully
docker-compose down

# Force stop
docker-compose down --timeout 10

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Clean Up Docker Resources

```bash
# Remove testscout image
docker rmi testscout:latest

# Remove all unused Docker resources
docker system prune -a

# Check disk usage
docker system df
```

---

## Troubleshooting

### Issue: "Cannot connect to Docker daemon"

**Windows/Mac:**
- Make sure Docker Desktop is running (icon in system tray/menu bar)
- Restart Docker Desktop

**Linux:**
```bash
sudo systemctl start docker
sudo systemctl status docker
```

---

### Issue: Build fails with "No space left on device"

**Solution:**
```bash
# Clean up unused Docker resources
docker system prune -a --volumes

# Or increase Docker Desktop disk limit:
# Docker Desktop → Settings → Resources → Disk image size
```

---

### Issue: "Permission denied" on Linux

**Solution:**
```bash
# Make sure you're in docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo (not recommended)
sudo docker-compose up
```

---

### Issue: Playwright browser not working

**Check logs:**
```bash
docker-compose logs testscout | grep "Playwright"
```

**Common fixes:**
```bash
# Rebuild image with --no-cache
docker-compose build --no-cache

# Check if chromium is installed
docker-compose run testscout playwright --version
```

---

### Issue: "File not found: google-credentials.json"

**Solution:**
```bash
# Make sure the file is in the project root
ls -la google-credentials.json

# Check docker-compose.yml volume mount
grep google-credentials.json docker-compose.yml
```

---

### Issue: Leads CSV is empty

**Checks:**
1. **API keys valid?**
   ```bash
   cat .env | grep -v "^#"
   ```

2. **ICPs specific enough?**
   ```bash
   cat Input_ICP.csv
   ```

3. **Check logs for errors:**
   ```bash
   grep "ERROR\|WARNING" logs/run_*.log
   ```

---

### Issue: Container exits immediately

**Debug:**
```bash
# Run interactively to see errors
docker-compose run testscout /bin/bash

# Inside container, run manually
python -m zcap.run
```

---

## Performance Tips

### Speed Up Builds

**Use Docker BuildKit:**
```bash
# Add to .env or export
export DOCKER_BUILDKIT=1

# Build faster
docker-compose build
```

### Optimize Resources

**Adjust in docker-compose.yml:**
```yaml
deploy:
  resources:
    limits:
      cpus: '4.0'      # Use more CPUs
      memory: 8G       # Use more RAM
```

---

## Updating TestScout

```bash
# Stop current container
docker-compose down

# Pull latest code (if using git)
git pull

# Rebuild image
docker-compose build --no-cache

# Run with new version
docker-compose up
```

---

## Uninstall

### Remove TestScout

```bash
# Stop and remove containers
docker-compose down -v

# Remove image
docker rmi testscout:latest

# Remove project files
cd ..
rm -rf testScout
```

### Uninstall Docker Desktop

**Windows:**
- Settings → Apps → Docker Desktop → Uninstall

**Mac:**
- Drag Docker.app from Applications to Trash

**Linux:**
```bash
sudo apt-get purge docker-ce docker-ce-cli containerd.io
sudo rm -rf /var/lib/docker
```

---

## Quick Reference Card

### Essential Commands

```bash
# Start pipeline
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop pipeline
docker-compose down

# Rebuild after changes
docker-compose up --build

# Run specific command
docker-compose run testscout python -m zcap.run
```

---

## Support

**Common Questions:**
- See `docs/FAQ.md`

**Technical Issues:**
- Check `docs/TECHNICAL_GUIDE.md`

**Docker Issues:**
- https://docs.docker.com/desktop/troubleshoot/overview/

---

## System Requirements Summary

| OS | Min RAM | Min Disk | Docker Version |
|----|---------|----------|----------------|
| Windows 10/11 | 8GB | 20GB | 24.0+ |
| macOS 11+ | 8GB | 20GB | 24.0+ |
| Linux | 4GB | 20GB | 24.0+ |

---

**You're Ready!** 🚀

Run `docker-compose up` and watch the leads roll in!

*Last Updated: January 2026*
