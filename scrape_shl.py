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
    rows = table.find_all("tr")[1:]  # Skip header row
    
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

        duration = "N/A"

        assessments.append({
            "name": name,
            "url": "https://www.shl.com" + url,
            "duration": duration,
            "test_type": test_type,
            "remote_testing": remote_testing,
            "adaptive_irt": adaptive_irt
        })
    
    return assessments

def scrape_section(base_url, section_name, type_param):
    """Scrape all pages for a given section."""
    url = f"{base_url}?type={type_param}"
    all_assessments = []

    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Failed to fetch {url}: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        print(f"Scraping {url} - Title: {soup.title.text if soup.title else 'No title'}")

        tables = soup.find_all("table")
        found = False
        for table in tables:
            header = table.find("th", class_="custom__table-heading__title")
            if header and section_name in header.text:
                print(f"Found table: {header.text.strip()}")
                assessments = scrape_table(table)
                all_assessments.extend(assessments)
                found = True

        if not found:
            print(f"Table '{section_name}' not found on this page")
            break

        # Find "Next" link (assumes it's a sibling or nearby element)
        next_link = soup.find("a", text="Next")  # Adjust if needed
        if next_link and "href" in next_link.attrs:
            url = "https://www.shl.com" + next_link["href"]
            print(f"Following to next page: {url}")
            time.sleep(1)
        else:
            print(f"No more pages for {section_name}")
            url = None

    return all_assessments

def scrape_shl_catalog():
    # Scrape both sections
    prepackaged = scrape_section(BASE_URL, "Pre-packaged Job Solutions", "2")
    individual = scrape_section(BASE_URL, "Individual Test Solutions", "1")  # Adjust '1' after inspection
    
    # Combine all assessments
    all_assessments = prepackaged + individual
    df = pd.DataFrame(all_assessments)
    return df

def save_to_csv(df, filename="shl_assessments.csv"):
    if df is not None and not df.empty:
        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} assessments to {filename}")
    else:
        print("No data to save")

if __name__ == "__main__":
    print("Scraping SHL catalog...")
    df = scrape_shl_catalog()
    save_to_csv(df)