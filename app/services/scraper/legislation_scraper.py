import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup
from app.services.scraper.base_scraper import BaseScraper
from app.models.legislation import Act, Section, SubLegislation, SubLegislationType
from app.extensions import db

logger = logging.getLogger(__name__)


class LegislationScraper(BaseScraper):
    """Scraper for Malaysian Acts from Laws of Malaysia Online (lom.agc.gov.my)."""

    BASE_URL = 'https://lom.agc.gov.my'

    CATEGORIES = {
        'Constitutional': 'Constitutional',
        'Criminal': 'Criminal',
        'Civil Procedure': 'Civil Procedure',
        'Company': 'Company Law',
        'Land': 'Land Law',
        'Labour': 'Labour',
        'Tax': 'Tax',
        'Banking': 'Banking',
        'Environment': 'Environment',
        'Family': 'Family',
        'Probate': 'Probate',
        'IP': 'Intellectual Property',
        'Immigration': 'Immigration',
        'Insurance': 'Insurance',
        'Shipping': 'Shipping',
        'Construction': 'Construction',
        'Bankruptcy': 'Bankruptcy',
    }

    def __init__(self):
        super().__init__(source_name='legislation', rate_limit_delay=1)

    def fetch_listing_page(self, page_number):
        """Fetch Acts index from lom.agc.gov.my."""
        url = f'{self.BASE_URL}/acts'
        try:
            response = self._get(url)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f'Failed to fetch {url}: {e}')
            return None

    def parse_listing(self, response):
        """Parse Acts listing page."""
        soup = BeautifulSoup(response.content, 'html.parser')
        acts = []

        # Find Act entries (adjust selector as needed)
        for item in soup.find_all('div', class_='act-entry'):
            try:
                title_elem = item.find('a', class_='act-title')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get('href')
                if not url.startswith('http'):
                    url = f'{self.BASE_URL}{url}'

                # Extract act number from title (e.g., "Act No. 123 of 2020")
                act_pattern = r'Act\s+(?:No\.|Number)\s+(\d+)\s+of\s+(\d{4})'
                match = re.search(act_pattern, title)

                if match:
                    act_number = f'Act {match.group(1)} of {match.group(2)}'
                else:
                    act_number = title[:50]

                # Extract year
                year_match = re.search(r'(\d{4})', title)
                year = int(year_match.group(1)) if year_match else None

                # Get category
                category_elem = item.find('span', class_='category')
                category = category_elem.get_text(strip=True) if category_elem else 'General'

                acts.append({
                    'title': title,
                    'act_number': act_number,
                    'url': url,
                    'year': year,
                    'category': category,
                })
            except Exception as e:
                logger.debug(f'Failed to parse act entry: {e}')
                continue

        logger.info(f'Parsed {len(acts)} acts from listing')
        return acts

    def fetch_judgment(self, act_metadata):
        """Fetch full Act document (PDF or HTML)."""
        url = act_metadata.get('url')
        if not url:
            return None

        try:
            response = self._get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f'Failed to fetch act from {url}: {e}')
            return None

    def parse_judgment(self, raw_content):
        """Parse Act HTML/PDF into structured Act and Sections."""
        soup = BeautifulSoup(raw_content, 'html.parser')

        try:
            # Extract Act details
            title_elem = soup.find('h1', class_='act-title')
            title = title_elem.get_text(strip=True) if title_elem else ''

            # Find sections
            sections = []
            section_pattern = r'Section\s+(\d+[A-Z]?)\s*[-–]\s*([^\n]+)'

            full_text = soup.get_text()
            section_matches = re.finditer(section_pattern, full_text)

            for match in section_matches:
                section_number = match.group(1)
                heading = match.group(2).strip()

                # Get section content (text until next section)
                section_start = match.end()
                next_section = re.search(
                    r'Section\s+\d+[A-Z]?\s*[-–]',
                    full_text[section_start:]
                )
                section_end = section_start + next_section.start() if next_section else len(full_text)
                content = full_text[section_start:section_end].strip()

                sections.append({
                    'section_number': section_number,
                    'heading': heading,
                    'content': content[:2000],  # Truncate very long sections
                })

            return {
                'title': title,
                'full_text': full_text[:10000],  # Store summary
                'sections': sections,
                'source_url': None,
            }
        except Exception as e:
            logger.error(f'Failed to parse act: {e}')
            return None

    def scrape_subsidiary_legislation(self):
        """Scrape PU(A) and PU(B) gazette orders."""
        url = 'https://gazette.agc.gov.my'
        try:
            response = self._get(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            sub_legislations = []

            for item in soup.find_all('div', class_='gazette-entry'):
                try:
                    # Extract PU number
                    pu_elem = item.find('span', class_='pu-number')
                    pu_number = pu_elem.get_text(strip=True) if pu_elem else ''

                    # Determine type (PU_A or PU_B)
                    pu_type = 'PU_A' if 'PU(A)' in pu_number else 'PU_B'

                    # Extract title and date
                    title_elem = item.find('a', class_='pu-title')
                    title = title_elem.get_text(strip=True) if title_elem else ''

                    date_elem = item.find('span', class_='gazetted-date')
                    gazetted_date = date_elem.get_text(strip=True) if date_elem else None

                    sub_legislations.append({
                        'pu_number': pu_number,
                        'type': pu_type,
                        'title': title,
                        'gazetted_date': gazetted_date,
                    })
                except Exception as e:
                    logger.debug(f'Failed to parse gazette entry: {e}')
                    continue

            return sub_legislations
        except Exception as e:
            logger.error(f'Failed to scrape subsidiary legislation: {e}')
            return []
