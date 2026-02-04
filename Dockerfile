FROM python:3.11-slim

# Install minimal system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# This command installs the browser AND all necessary system libraries automatically
RUN playwright install chromium --with-deps

COPY . .

CMD ["python", "-m", "zcap.run"]