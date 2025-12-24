from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
from scraper.scraper import KazanAttractionScraper


class ScraperTest(TestCase):
    """Tests for KazanAttractionScraper."""

    def setUp(self):
        self.scraper = KazanAttractionScraper(headless=True)

    def test_scraper_initialization(self):
        """Test scraper initialization."""
        self.assertIsNotNone(self.scraper)
        self.assertTrue(self.scraper.headless)

    @patch('scraper.scraper.webdriver.Chrome')
    def test_init_driver(self, mock_chrome):
        """Test driver initialization."""
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        self.scraper._init_driver()
        
        self.assertIsNotNone(self.scraper.driver)
        mock_chrome.assert_called_once()

    def test_calculate_distance(self):
        """Test distance calculation."""
        # Distance between two points in Kazan
        lat1, lon1 = 55.8304, 49.0661  # Kazan center
        lat2, lon2 = 55.8404, 49.0761  # ~1km away
        
        distance = self.scraper._calculate_distance(lat1, lon1, lat2, lon2)
        
        # Should be approximately 1km
        self.assertGreater(distance, 0.9)
        self.assertLess(distance, 1.5)

    def test_enrich_attraction_data(self):
        """Test attraction data enrichment."""
        attraction_data = {
            'name': 'Казанский Кремль',
            'address': 'Кремль, Казань',
        }
        
        enriched = self.scraper.enrich_attraction_data(attraction_data)
        
        self.assertEqual(enriched['name'], 'Казанский Кремль')
        self.assertIn('rating', enriched)
        self.assertIn('visit_duration', enriched)
        self.assertIn('price', enriched)
        self.assertIn('is_free', enriched)
