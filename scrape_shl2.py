import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
}

def scrape_table(table):
    """Extract data from a single table."""
    assessments = []
    rows = table.find_all("tr")[1:]  # Skip header

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        name_col = cols[0]
        name_tag = name_col.find("a")
        name = name_tag.text.strip() if name_tag else "Unknown"
        url = name_tag["href"] if name_tag and "href" in name_tag.attrs else ""

        remote_col = cols[1]
        remote_testing = "Yes" if remote_col.find("span", class_="catalogue__circle -yes") else "No"

        adaptive_col = cols[2]
        adaptive_irt = "Yes" if adaptive_col.find("span", class_="catalogue__circle -yes") else "No"

        test_type_col = cols[3]
        test_keys = test_type_col.find_all("span", class_="product-catalogue__key")
        test_type = ", ".join(key.text.strip() for key in test_keys) if test_keys else "N/A"

        duration = "N/A"  # Not found in table directly

        assessments.append({
            "name": name,
            "url": "https://www.shl.com" + url,
            "duration": duration,
            "test_type": test_type,
            "remote_testing": remote_testing,
            "adaptive_irt": adaptive_irt
        })

    return assessments

def scrape_pages_for_type(type_param, max_pages, label):
    """Scrape paginated assessment tables for a given type (1 or 2)."""
    all_assessments = []
    for page_start in range(0, max_pages * 12, 12):
        url = f"{BASE_URL}?start={page_start}&type={type_param}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"[{label}] Failed to fetch {url}: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        print(f"[{label}] Scraping: {url}")

        table = soup.find("table")
        if not table:
            print(f"[{label}] No table found, stopping.")
            break

        assessments = scrape_table(table)
        if not assessments:
            print(f"[{label}] No assessments found, stopping.")
            break

        all_assessments.extend(assessments)
        time.sleep(1)  # Be nice to their server

    return all_assessments

def scrape_shl_catalog():
    print("🔍 Scraping Pre-packaged Job Solutions...")
    prepackaged = scrape_pages_for_type(type_param=2, max_pages=12, label="Prepackaged")

    print("🔍 Scraping Individual Test Solutions...")
    individual = scrape_pages_for_type(type_param=1, max_pages=32, label="Individual")

    all_assessments = prepackaged + individual
    df = pd.DataFrame(all_assessments)
    return df

def save_to_csv(df, filename="shl_assessments.csv"):
    if df is not None and not df.empty:
        df.to_csv(filename, index=False)
        print(f"✅ Saved {len(df)} assessments to {filename}")
    else:
        print("❌ No data to save")

if __name__ == "__main__":
    print("🚀 Starting SHL catalog scrape...")
    df = scrape_shl_catalog()
    save_to_csv(df)
