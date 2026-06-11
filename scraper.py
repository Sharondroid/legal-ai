import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://ghalii.org"
SEARCH_URL = "https://ghalii.org/search/site/"

query = "law"
target_count = 50

case_links = []
cases_data = []
page = 0


# =========================
# STEP 1: COLLECT CASE LINKS
# =========================
case_links = []

url = "https://ghalii.org/judgments"
res = requests.get(url)
soup = BeautifulSoup(res.text, "html.parser")

for a in soup.find_all("a", href=True):
    href = a["href"]

    if "/akn/gh/judgment/" in href:
        full_link = "https://ghalii.org" + href

        if full_link not in case_links:
            case_links.append(full_link)

    if len(case_links) >= 50:
        break

print(f"Collected {len(case_links)} case links")

# =========================
# STEP 2: SCRAPE CASE DATA
# =========================
for link in case_links:
    try:
        res = requests.get(link, timeout=10)

        if res.status_code != 200:
            print(f"Failed: {link}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")

        # Case title
        title_tag = soup.find("h1")
        case_name = title_tag.get_text(strip=True) if title_tag else "N/A"

        # Cleaner legal text extraction
        paragraphs = soup.find_all("p")
        full_text = " ".join([p.get_text(strip=True) for p in paragraphs])

        # Fallback if <p> is empty
        if not full_text:
            full_text = soup.get_text(separator=" ", strip=True)

        cases_data.append({
            "case_name": case_name,
            "source": link,
            "full_text": full_text[:8000]  # increased limit for better RAG context
        })

        print(f"Scraped: {case_name}")

        time.sleep(1)

    except Exception as e:
        print(f"Error scraping {link}: {e}")


# =========================
# STEP 3: SAVE TO CSV
# =========================
df = pd.DataFrame(cases_data)
df.to_csv("ghana_cases_ghalii.csv", index=False)

print("\nCSV created successfully: ghana_cases_ghalii.csv")
print(f"Total cases saved: {len(df)}")