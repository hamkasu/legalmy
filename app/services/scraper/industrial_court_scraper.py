import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup
from app.services.scraper.base_scraper import BaseScraper
from app.models.judgment import CourtLevel

logger = logging.getLogger(__name__)


class IndustrialCourtScraper(BaseScraper):
    """Scraper for Industrial Court awards (KPTG)."""

    BASE_URL = 'https://www.kptg.my/awards'

    def __init__(self):
        super().__init__(source_name='industrial_court', rate_limit_delay=2)

    def fetch_listing_page(self, page_number):
        """Fetch listing page from KPTG portal."""
        url = f'{self.BASE_URL}?page={page_number}'
        try:
            response = self._get(url)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f'Failed to fetch {url}: {e}')
            return None

    def parse_listing(self, response):
        """Parse award listing page."""
        soup = BeautifulSoup(response.content, 'html.parser')
        awards = []

        for item in soup.find_all('div', class_='award-item'):
            try:
                link_elem = item.find('a', class_='award-link')
                if not link_elem:
                    continue

                title = link_elem.get_text(strip=True)
                url = link_elem.get('href')
                if not url.startswith('http'):
                    url = f'{self.BASE_URL}{url}'

                # Extract award number from title
                award_pattern = r'Award\s+No\.\s+(\d+)/(\d{4})'
                award_match = re.search(award_pattern, title)
                citation = f'Award No. {award_match.group(1)}/{award_match.group(2)}' if award_match else title

                date_elem = item.find('span', class_='award-date')
                date_delivered = date_elem.get_text(strip=True) if date_elem else ''

                awards.append({
                    'citation': citation,
                    'title': title,
                    'url': url,
                    'date_delivered': date_delivered,
                })
            except Exception as e:
                logger.debug(f'Failed to parse award listing: {e}')
                continue

        logger.info(f'Parsed {len(awards)} awards from listing page')
        return awards

    def fetch_judgment(self, award_metadata):
        """Fetch full award document."""
        url = award_metadata.get('url')
        if not url:
            return None

        try:
            response = self._get(url)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f'Failed to fetch award from {url}: {e}')
            return None

    def parse_judgment(self, raw_content):
        """Parse award into structured data."""
        soup = BeautifulSoup(raw_content, 'html.parser')

        try:
            # Extract title
            title_elem = soup.find('h1', class_='award-title')
            title = title_elem.get_text(strip=True) if title_elem else ''

            # Extract full text
            content_elem = soup.find('div', class_='award-content')
            full_text = content_elem.get_text(strip=True) if content_elem else ''

            # Extract parties (claimant vs respondent for industrial matters)
            parties_elem = soup.find('div', class_='award-parties')
            parties_text = parties_elem.get_text(strip=True) if parties_elem else ''

            # In industrial court, it's usually "Claimant v. Respondent"
            parties_plaintiff = []  # Claimant (employee/union)
            parties_defendant = []  # Respondent (employer)

            if 'v.' in parties_text or 'v' in parties_text:
                parts = re.split(r'\s+v\.?\s+', parties_text, maxsplit=1)
                if len(parts) >= 1:
                    parties_plaintiff = [p.strip() for p in parts[0].split(',')]
                if len(parts) >= 2:
                    parties_defendant = [p.strip() for p in parts[1].split(',')]

            # Extract date delivered
            date_delivered = self._extract_date(full_text)

            # Extract citation
            citation = self._extract_citation(title)

            # Extract award type (reinstatement, compensation, dismissed)
            award_type = self._extract_award_type(full_text)

            # Extract quantum if present
            quantum = self._extract_quantum(full_text)

            return {
                'citation': citation,
                'title': title,
                'court_level': CourtLevel.INDUSTRIAL,
                'court_location': 'Malaysia',
                'parties_plaintiff': parties_plaintiff,
                'parties_defendant': parties_defendant,
                'date_decided': date_delivered,
                'date_delivered': date_delivered,
                'full_text': full_text,
                'outcome': self._map_award_outcome(award_type),
                'source_url': None,
                'coram': [],
                'subject_matter': ['Employment'],  # Industrial court is employment-focused
            }
        except Exception as e:
            logger.error(f'Failed to parse award: {e}')
            return None

    def _extract_citation(self, title):
        """Extract award citation."""
        citation_pattern = r'Award\s+No\.\s+(\d+)/(\d{4})'
        match = re.search(citation_pattern, title)
        if match:
            return f'Award No. {match.group(1)}/{match.group(2)}'
        return title[:100]

    def _extract_date(self, text):
        """Extract award date."""
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

    def _extract_award_type(self, text):
        """Determine award type from content."""
        text_upper = text.upper()
        if 'REINSTATEMENT' in text_upper:
            return 'reinstatement'
        elif 'COMPENSATION' in text_upper or 'COMPENSATION' in text_upper:
            return 'compensation'
        elif 'DISMISSED' in text_upper:
            return 'dismissed'
        return 'other'

    def _extract_quantum(self, text):
        """Extract compensation amount if present."""
        # Look for currency amounts
        quantum_pattern = r'RM\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
        match = re.search(quantum_pattern, text)
        return match.group(1) if match else None

    def _map_award_outcome(self, award_type):
        """Map award type to outcome enum."""
        from app.models.judgment import OutcomeType

        if award_type == 'reinstatement':
            return OutcomeType.ALLOWED
        elif award_type == 'compensation':
            return OutcomeType.PARTLY_ALLOWED
        elif award_type == 'dismissed':
            return OutcomeType.DISMISSED
        return None
