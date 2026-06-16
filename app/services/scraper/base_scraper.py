import os
import requests
import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all court judgment scrapers."""

    # User agents to rotate through
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    ]

    def __init__(self, source_name, rate_limit_delay=2, max_retries=3):
        """
        Initialize scraper.

        Args:
            source_name: Identifier for the data source (e.g., 'kehakiman', 'industrial_court')
            rate_limit_delay: Seconds to wait between requests (default 2)
            max_retries: Maximum number of retries on failure (default 3)
        """
        self.source_name = source_name
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.user_agent_index = 0
        self.session = self._create_session()
        self.raw_data_dir = Path('/data/raw') / source_name / datetime.now().strftime('%Y%m%d')
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def _create_session(self):
        """Create requests session with retry strategy."""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=['HEAD', 'GET', 'OPTIONS']
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def _get_user_agent(self):
        """Rotate through user agents."""
        ua = self.USER_AGENTS[self.user_agent_index]
        self.user_agent_index = (self.user_agent_index + 1) % len(self.USER_AGENTS)
        return ua

    def _get(self, url, **kwargs):
        """GET request with rate limiting and user agent rotation."""
        headers = kwargs.pop('headers', {})
        headers['User-Agent'] = self._get_user_agent()
        time.sleep(self.rate_limit_delay)
        return self.session.get(url, headers=headers, timeout=30, **kwargs)

    def save_raw_html(self, url, content):
        """Save raw HTML to disk for audit trail."""
        # Create filename from URL hash
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        file_path = self.raw_data_dir / f'{url_hash}.html'
        file_path.write_bytes(content if isinstance(content, bytes) else content.encode('utf-8'))
        logger.debug(f'Saved raw HTML to {file_path}')
        return file_path

    @abstractmethod
    def fetch_listing_page(self, page_number):
        """
        Fetch a listing page of judgments.

        Returns:
            Response object or None if failed
        """
        pass

    @abstractmethod
    def parse_listing(self, response):
        """
        Parse listing page to extract judgment URLs/citations.

        Returns:
            List of dict with 'citation', 'url', and other metadata
        """
        pass

    @abstractmethod
    def fetch_judgment(self, judgment_metadata):
        """
        Fetch a full judgment.

        Returns:
            Raw judgment content (HTML or text)
        """
        pass

    @abstractmethod
    def parse_judgment(self, raw_content):
        """
        Parse judgment content into structured dict.

        Returns:
            Dict with keys: citation, title, court_level, court_location, parties_plaintiff,
                           parties_defendant, date_decided, full_text, outcome, source_url
        """
        pass

    def scrape(self, start_page=1, end_page=None):
        """
        Main scrape loop.

        Yields:
            Parsed judgment dicts
        """
        page = start_page
        while end_page is None or page <= end_page:
            logger.info(f'[{self.source_name}] Fetching page {page}...')
            listing_response = self.fetch_listing_page(page)
            if not listing_response:
                logger.warning(f'Failed to fetch page {page}, stopping')
                break

            self.save_raw_html(listing_response.url, listing_response.content)

            judgments = self.parse_listing(listing_response)
            if not judgments:
                logger.info(f'No judgments on page {page}, stopping')
                break

            for judgment_metadata in judgments:
                raw_content = self.fetch_judgment(judgment_metadata)
                if raw_content:
                    self.save_raw_html(judgment_metadata.get('url', ''), raw_content)
                    parsed = self.parse_judgment(raw_content)
                    if parsed:
                        yield parsed

            page += 1
