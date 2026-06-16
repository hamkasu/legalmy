import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup
from app.services.scraper.base_scraper import BaseScraper
from app.models.judgment import CourtLevel

logger = logging.getLogger(__name__)


class KehakimanScraper(BaseScraper):
    """Scraper for Kehakiman.gov.my judgment portal."""

    BASE_URL = 'https://www.kehakiman.gov.my/en/judgment'

    def __init__(self):
        super().__init__(source_name='kehakiman', rate_limit_delay=2)

    def fetch_listing_page(self, page_number):
        """Fetch listing page from Kehakiman portal."""
        url = f'{self.BASE_URL}?page={page_number}'
        try:
            response = self._get(url)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f'Failed to fetch {url}: {e}')
            return None

    def parse_listing(self, response):
        """Parse judgment listing page."""
        soup = BeautifulSoup(response.content, 'html.parser')
        judgments = []

        # Find judgment listing items (adjust selector as needed)
        for item in soup.find_all('div', class_='judgment-item'):
            try:
                title_elem = item.find('a', class_='judgment-link')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                url = title_elem.get('href')
                if not url.startswith('http'):
                    url = f'{self.BASE_URL}{url}'

                # Extract citation from title if present
                citation_match = re.search(r'\[(\d{4})\]\s+(\d+)\s+(\w+)\s+(\d+)', title)
                citation = f'[{citation_match.group(1)}] {citation_match.group(2)} {citation_match.group(3)} {citation_match.group(4)}' if citation_match else title

                # Extract metadata
                meta_text = item.find('div', class_='judgment-meta')
                court = meta_text.get_text(strip=True) if meta_text else ''
                date_text = item.find('span', class_='judgment-date')
                date_decided = date_text.get_text(strip=True) if date_text else ''

                judgments.append({
                    'citation': citation,
                    'title': title,
                    'url': url,
                    'court': court,
                    'date_decided': date_decided,
                })
            except Exception as e:
                logger.debug(f'Failed to parse listing item: {e}')
                continue

        logger.info(f'Parsed {len(judgments)} judgments from listing page')
        return judgments

    def fetch_judgment(self, judgment_metadata):
        """Fetch full judgment from URL."""
        url = judgment_metadata.get('url')
        if not url:
            return None

        try:
            response = self._get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f'Failed to fetch judgment from {url}: {e}')
            return None

    def parse_judgment(self, raw_content):
        """Parse HTML judgment into structured data."""
        soup = BeautifulSoup(raw_content, 'html.parser')

        try:
            # Extract title
            title_elem = soup.find('h1', class_='judgment-title')
            title = title_elem.get_text(strip=True) if title_elem else ''

            # Extract full text
            content_elem = soup.find('div', class_='judgment-content')
            full_text = content_elem.get_text(strip=True) if content_elem else ''

            # Extract parties
            parties_text = ''
            parties_elem = soup.find('div', class_='judgment-parties')
            if parties_elem:
                parties_text = parties_elem.get_text(strip=True)

            # Simple party extraction (this would need more sophisticated parsing)
            parties_plaintiff = []
            parties_defendant = []
            if 'v.' in parties_text or 'v' in parties_text:
                parts = re.split(r'\s+v\.?\s+', parties_text, maxsplit=1)
                if len(parts) >= 1:
                    parties_plaintiff = [p.strip() for p in parts[0].split(',')]
                if len(parts) >= 2:
                    parties_defendant = [p.strip() for p in parts[1].split(',')]

            # Extract court level from content
            court_level = self._detect_court_level(full_text)

            # Extract date
            date_decided = self._extract_date(full_text)

            # Extract citation
            citation = self._extract_citation(title, full_text)

            return {
                'citation': citation,
                'title': title,
                'court_level': court_level,
                'court_location': 'Malaysia',
                'parties_plaintiff': parties_plaintiff,
                'parties_defendant': parties_defendant,
                'date_decided': date_decided,
                'full_text': full_text,
                'outcome': None,  # Will be extracted by AI enrichment
                'source_url': None,  # Will be set by pipeline
                'coram': [],  # Will be extracted by AI enrichment
                'subject_matter': [],  # Will be extracted by AI enrichment
            }
        except Exception as e:
            logger.error(f'Failed to parse judgment: {e}')
            return None

    def _detect_court_level(self, text):
        """Detect court level from judgment text."""
        text_upper = text.upper()
        if 'FEDERAL COURT' in text_upper:
            return CourtLevel.FEDERAL
        elif 'COURT OF APPEAL' in text_upper:
            return CourtLevel.APPEAL
        elif 'HIGH COURT' in text_upper:
            return CourtLevel.HIGH
        elif 'SESSIONS COURT' in text_upper:
            return CourtLevel.SESSIONS
        elif 'MAGISTRATE' in text_upper:
            return CourtLevel.MAGISTRATE
        elif 'INDUSTRIAL COURT' in text_upper:
            return CourtLevel.INDUSTRIAL
        elif 'SYARIAH' in text_upper:
            return CourtLevel.SYARIAH_HIGH
        return CourtLevel.HIGH  # Default

    def _extract_date(self, text):
        """Extract judgment date from text."""
        # Look for date patterns like "1 January 2024" or "1/1/2024"
        date_patterns = [
            r'(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None

    def _extract_citation(self, title, text):
        """Extract citation from title or text."""
        # Look for citation patterns like "[2024] 3 CLJ 101"
        citation_pattern = r'\[(\d{4})\]\s+(\d+)\s+(\w+)\s+(\d+)'
        match = re.search(citation_pattern, title)
        if match:
            return f"[{match.group(1)}] {match.group(2)} {match.group(3)} {match.group(4)}"

        # Fallback: use title as citation
        return title[:100]
