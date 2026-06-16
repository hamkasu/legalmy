# Scraper module
from app.services.scraper.base_scraper import BaseScraper
from app.services.scraper.kehakiman_scraper import KehakimanScraper
from app.services.scraper.industrial_court_scraper import IndustrialCourtScraper
from app.services.scraper.legislation_scraper import LegislationScraper

__all__ = ['BaseScraper', 'KehakimanScraper', 'IndustrialCourtScraper', 'LegislationScraper']
