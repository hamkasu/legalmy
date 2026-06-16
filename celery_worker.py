import os
import logging
from celery import Celery
from app import create_app, db
from app.services.ingest_pipeline import IngestPipeline
from app.services.anthropic_service import AnthropicService
from app.services.scraper import KehakimanScraper, IndustrialCourtScraper

flask_app = create_app(os.environ.get('FLASK_ENV', 'development'))
celery = Celery(flask_app.import_name)
celery.conf.update(flask_app.config)

logger = logging.getLogger(__name__)


@celery.task(bind=True, name='ingest.judgment')
def ingest_judgments(self, source='kehakiman', limit=None, start_page=1, end_page=None):
    """
    Celery task to ingest judgments from a specific source.

    Args:
        source: 'kehakiman' or 'industrial_court'
        limit: Maximum number of judgments to ingest (None for unlimited)
        start_page: Starting page number for scraper
        end_page: Ending page number for scraper
    """
    with flask_app.app_context():
        try:
            logger.info(f'Starting ingestion from {source}...')

            # Initialize scraper and pipeline
            if source == 'kehakiman':
                scraper = KehakimanScraper()
            elif source == 'industrial_court':
                scraper = IndustrialCourtScraper()
            else:
                logger.error(f'Unknown source: {source}')
                return {'status': 'error', 'message': f'Unknown source: {source}'}

            anthropic_service = AnthropicService()
            pipeline = IngestPipeline(anthropic_service)

            # Scrape and ingest
            ingested_count = 0
            for index, raw_judgment in enumerate(scraper.scrape(start_page, end_page)):
                if limit and ingested_count >= limit:
                    logger.info(f'Reached limit of {limit} judgments')
                    break

                judgment = pipeline.process_judgment(
                    raw_judgment,
                    index=ingested_count,
                    total=limit or '∞'
                )
                if judgment:
                    ingested_count += 1

                # Update task progress
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': ingested_count,
                        'total': limit or 'unknown',
                        'status': f'Ingesting from {source}...'
                    }
                )

            stats = pipeline.get_stats()
            logger.info(f'Ingestion complete. Stats: {stats}')

            return {
                'status': 'success',
                'source': source,
                'stats': stats
            }

        except Exception as e:
            logger.error(f'Ingestion task failed: {e}')
            return {
                'status': 'error',
                'message': str(e)
            }


@celery.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


if __name__ == '__main__':
    celery.start()
