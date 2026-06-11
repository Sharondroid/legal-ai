import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin
from collections import deque

BASE_URL = "https://ghalii.org"

# =========================
# CONFIG
# =========================
START_URLS = [
    "https://ghalii.org/",
    "https://ghalii.org/judgments"
]

TARGET_CASES = 300
MAX_PAGES = 1200
REQUEST_DELAY = 1

# =========================
# STORAGE
# =========================
visited_pages = set()
case_links = set()
queue = deque(START_URLS)

# =========================
# CLEAN TEXT FUNCTION
# =========================
def clean_text(soup):
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    body = soup.find("body")
    if not body:
        return ""

    text = body.get_text(separator=" ", strip=True)

    # Remove common GhaLII noise
    noise_phrases = [
        "Do you want to load",
        "GhaLII is a non-profit organisation",
        "Help About us Contact",
        "Terms of Use"
    ]

    for phrase in noise_phrases:
        text = text.replace(phrase, "")

    return " ".join(text.split())

# =========================
# STEP 1: CRAWL SITE
# =========================
print("Starting crawler...")

pages_crawled = 0

while queue and len(case_links) < TARGET_CASES and pages_crawled < MAX_PAGES:

    url = queue.popleft()

    if url in visited_pages:
        continue

    visited_pages.add(url)
    pages_crawled += 1

    try:
        print(f"Crawling: {url}")

        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        for a in soup.find_all("a", href=True):
            full_url = urljoin(BASE_URL, a["href"])

            # Collect judgment links
            if "/akn/gh/judgment/" in full_url:
                case_links.add(full_url)

            # Crawl internal pages only
            elif BASE_URL in full_url and full_url not in visited_pages:
                queue.append(full_url)

        time.sleep(REQUEST_DELAY)

    except Exception:
        print(f"Failed crawling: {url}")

print(f"\nCollected case links: {len(case_links)}")

# =========================
# STEP 2: SCRAPE CASE DATA
# =========================
cases_data = []

for i, link in enumerate(list(case_links)):

    if i >= TARGET_CASES:
        break

    try:
        print(f"Scraping case {i+1}: {link}")

        res = requests.get(link, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        # Case title
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        # Clean full text
        text = clean_text(soup)

        # Skip weak/empty pages
        if len(text) < 200:
            continue

        cases_data.append({
            "case_name": title,
            "source": link,
            "full_text": text[:5000]
        })

        time.sleep(REQUEST_DELAY)

    except Exception:
        print(f"Failed scraping: {link}")

# =========================
# STEP 3: SAVE CSV
# =========================
df = pd.DataFrame(cases_data)
df.to_csv("ghana_cases_ghalii.csv", index=False)

print("\nDONE!")
print(f"Cases saved: {len(df)}")
print("File: ghana_cases_ghalii.csv")