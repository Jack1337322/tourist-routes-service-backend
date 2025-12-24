"""
Celery tasks for scraping attractions.
"""
from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)


@shared_task
def scrape_attractions_task():
    """Periodic task to scrape attractions."""
    logger.info('Starting periodic attraction scraping...')
    try:
        call_command('scrape_attractions', headless=True)
        logger.info('Attraction scraping completed successfully')
    except Exception as e:
        logger.error(f'Error during attraction scraping: {e}')
        raise

