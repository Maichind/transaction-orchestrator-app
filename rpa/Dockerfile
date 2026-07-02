# Playwright official image includes all browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

WORKDIR /rpa

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install only Chromium (lighter than all browsers)
RUN playwright install chromium --with-deps

COPY . .

# Default: scrape "FastAPI" — override with docker run args
ENTRYPOINT ["python", "wikipedia_scraper.py"]
CMD ["FastAPI"]
