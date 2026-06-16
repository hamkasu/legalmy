import httpx
import logging
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

ECOURT_BASE_URL = "https://ecourt.gov.my"
COURTS = {
    "KL": "Kuala Lumpur",
    "SG": "Selangor",
    "JHR": "Johor",
    "PLS": "Penang",
    "PRK": "Perak",
}

async def scrape_cause_list(date: str, court_code: str) -> List[Dict[str, Any]]:
    """
    Scrape cause list from e-Court for a specific date and court.

    Args:
        date: Date in format YYYY-MM-DD
        court_code: Court code (e.g. KL, SG, JHR)

    Returns:
        List of case dictionaries with keys:
        - case_number
        - parties
        - judge_name
        - court
        - hearing_date
        - status
    """
    try:
        # Construct URL for cause list
        url = f"{ECOURT_BASE_URL}/causelist"
        params = {
            "date": date,
            "court": court_code,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        cases = []
        # Parse table rows (adjust selectors based on actual HTML structure)
        table = soup.find("table", class_="cause-list")
        if not table:
            logger.warning(f"No cause list table found for {court_code} on {date}")
            return []

        for row in table.find_all("tr")[1:]:  # Skip header
            try:
                cols = row.find_all("td")
                if len(cols) < 6:
                    continue

                case_dict = {
                    "case_number": cols[0].get_text(strip=True),
                    "parties": cols[1].get_text(strip=True),
                    "judge_name": cols[2].get_text(strip=True),
                    "court": court_code,
                    "hearing_date": cols[3].get_text(strip=True),
                    "status": cols[5].get_text(strip=True),
                }
                cases.append(case_dict)
            except Exception as e:
                logger.debug(f"Error parsing row: {e}")
                continue

        logger.info(f"Scraped {len(cases)} cases for {court_code} on {date}")
        return cases

    except httpx.RequestError as e:
        logger.error(f"Request error scraping e-Court: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error scraping e-Court: {e}")
        return []
