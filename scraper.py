import os

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_hrefs() -> list[str]:
    """
    Scrape all product page URLs (hrefs) for men's glasses from SmartEyes.

    The function iterates through paginated product listings until
    no more products are found.

    Returns
    -------
    list[str]
        A list of relative URLs for each glasses product.
        Example: '/glasogon/8056262201190/8056262201190'
    """
    hrefs = []

    url_base = "https://smarteyes.se/glasogon/herr-bagar"

    urls = [f"{url_base}?page={n}" for n in range(2, 101)]
    urls.insert(0, url_base)  # Include the first page without query parameter

    for url in tqdm(urls, desc="get_hrefs()", unit="items"):
        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", class_="product-block-images")

        hrefs_tmp = []  # Temporary list used to verify its length
        for a in links:
            hrefs_tmp.append(a.get("href"))

        if len(hrefs_tmp) > 0:
            hrefs.extend(hrefs_tmp)
        else:
            tqdm.write(f"Last page: {url}")
            break

    return hrefs


def extract_dimensions(hrefs: list[str]) -> dict:
    """
    Extract frame dimensions for each glasses product from SmartEyes.

    The function visits each product page, parses the HTML, and retrieves
    measurements such as frame width, bridge width, lens width, and temple length.

    Parameters
    ----------
    hrefs : list[str]
        List of relative product URLs obtained from `get_hrefs()`.

    Returns
    -------
    dict
        Dictionary with the following keys:
        - 'url': Full URL to the product page
        - 'bredd': Frame width in mm
        - 'brygga': Bridge width in mm
        - 'glasbredd': Lens width in mm
        - 'skalmlangd': Temple length in mm
    """
    result = {"url": [], "bredd": [], "brygga": [], "glasbredd": [], "skalmlangd": []}

    url_base = "https://www.smarteyes.se"

    for i, href in enumerate(tqdm(hrefs, desc="extract_dimensions()", unit="items")):
        url = url_base + href

        result["url"].append(url)

        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        # Select all property names (e.g. 'Bredd', 'Brygga', etc.) form the product page
        props = soup.find_all(
            "p", class_="_text_3kw2f_1 _mb-5_1jxbs_120 _text-caption-head_3kw2f_213"
        )

        # Select all property dimensions from the product page.
        measurements = soup.find_all(
            "p",
            class_="_text_3kw2f_1 _text-caption-head_3kw2f_213 product-detail-frame-measurements__details",
        )

        # Number of property names should equal number of measurements.
        if len(props) == len(measurements):

            for i, _ in enumerate(measurements):
                prop = props[i].get_text(strip=True)  # Property name
                measurement = measurements[i].get_text(strip=True)  # Property dimension

                key = prop.lower().replace("ä", "a")  # Should match a key in 'result'

                try:
                    result[key].append(int(measurement.split(" ")[0]))
                except:
                    # Skip if measurement or key does not exist
                    tqdm.write(
                        f"{href}: invalid measurement value '{measurement}' or key '{key}'."
                    )

        else:
            tqdm.write(f"{href}: not equal number of properties and measurements")

    return result


def save_as_csv(data: dict) -> None:
    """
    Save scraped data as a CSV file.

    Parameters
    ----------
    data : dict
        Dictionary of glasses data, as returned by `extract_dimensions()`.
    """
    data_dir = "data/"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)

    df = pd.DataFrame(data)
    df.to_csv(f"{data_dir}smarteyes-herrbagar.csv", index=False)


def main() -> None:
    """
    Main function to scrape SmartEyes glasses data and save as CSV.

    Steps:
    1. Retrieve all product URLs.
    2. Extract dimensions for each product.
    3. Save the data to 'data/smarteyes-herrbagar.csv'.
    """
    tqdm.write("Scraping SmartEyes")
    hrefs = get_hrefs()
    dim = extract_dimensions(hrefs)
    save_as_csv(dim)
    tqdm.write(f"Number of glasses found: {len(hrefs)}")
    tqdm.write("Script complete!")


if __name__ == "__main__":
    main()
