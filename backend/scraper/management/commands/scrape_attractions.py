"""
Django management command to scrape attractions.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from scraper.scraper import KazanAttractionScraper
from attractions.models import Attraction, Category
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape tourist attractions from various sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Run browser in headless mode',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing attractions',
        )

    def handle(self, *args, **options):
        self.stdout.write('Starting attraction scraping...')
        
        scraper = KazanAttractionScraper(headless=options.get('headless', True))
        attractions_data = scraper.scrape_all()
        
        self.stdout.write(f'Found {len(attractions_data)} attractions')
        
        # Get or create default category
        default_category, _ = Category.objects.get_or_create(
            name='Общее',
            defaults={'slug': 'general', 'description': 'Общие достопримечательности'}
        )
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for att_data in attractions_data:
                enriched_data = scraper.enrich_attraction_data(att_data)
                
                # Create slug from name
                slug = self._create_slug(enriched_data['name'])
                
                # Check if attraction exists
                attraction, created = Attraction.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'name': enriched_data['name'],
                        'description': enriched_data.get('description', ''),
                        'short_description': enriched_data.get('description', '')[:500] if enriched_data.get('description') else '',
                        'latitude': enriched_data.get('latitude', 55.8304),  # Default Kazan coordinates
                        'longitude': enriched_data.get('longitude', 49.0661),
                        'address': enriched_data.get('address', ''),
                        'category': default_category,
                        'rating': enriched_data.get('rating', 0.0),
                        'visit_duration': enriched_data.get('visit_duration', 60),
                        'price': enriched_data.get('price', 0.0),
                        'is_free': enriched_data.get('is_free', True),
                        'website': enriched_data.get('url', ''),
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Created: {attraction.name}'))
                elif options.get('update_existing'):
                    # Update existing attraction
                    for key, value in enriched_data.items():
                        if hasattr(attraction, key) and value:
                            setattr(attraction, key, value)
                    attraction.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'Updated: {attraction.name}'))
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Scraping completed. Created: {created_count}, Updated: {updated_count}'
            )
        )

    def _create_slug(self, name: str) -> str:
        """Create URL-friendly slug from name."""
        import re
        from django.utils.text import slugify
        slug = slugify(name)
        # Ensure uniqueness by appending number if needed
        base_slug = slug
        counter = 1
        while Attraction.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

