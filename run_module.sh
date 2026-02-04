#!/bin/bash
echo '🐍 Setting up Python environment...'
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo '📦 Installing dependencies...'
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium

echo '🚀 Running TestScout Pipeline...'
echo '   Logs will be saved to logs/ folder'
python3 -m zcap.run
