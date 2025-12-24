from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Category, Attraction

User = get_user_model()


class CategoryModelTest(TestCase):
    """Tests for Category model."""

    def test_create_category(self):
        """Test category creation."""
        category = Category.objects.create(
            name='История',
            slug='history',
            description='Исторические достопримечательности'
        )
        self.assertEqual(category.name, 'История')
        self.assertEqual(category.slug, 'history')

    def test_category_str(self):
        """Test category string representation."""
        category = Category.objects.create(name='Культура', slug='culture')
        self.assertEqual(str(category), 'Культура')


class AttractionModelTest(TestCase):
    """Tests for Attraction model."""

    def setUp(self):
        self.category = Category.objects.create(
            name='История',
            slug='history'
        )

    def test_create_attraction(self):
        """Test attraction creation."""
        attraction = Attraction.objects.create(
            name='Казанский Кремль',
            slug='kazan-kremlin',
            description='Историческая крепость',
            latitude=55.8304,
            longitude=49.0661,
            category=self.category,
            rating=4.8,
            visit_duration=120,
            price=500.00,
        )
        self.assertEqual(attraction.name, 'Казанский Кремль')
        self.assertEqual(attraction.category, self.category)
        self.assertEqual(attraction.rating, 4.8)

    def test_attraction_str(self):
        """Test attraction string representation."""
        attraction = Attraction.objects.create(
            name='Башня Сююмбике',
            slug='syuyumbike-tower',
            description='Падающая башня',
            latitude=55.8304,
            longitude=49.0661,
        )
        self.assertEqual(str(attraction), 'Башня Сююмбике')


class AttractionAPITest(TestCase):
    """Tests for Attraction API."""

    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='История', slug='history')
        self.attraction = Attraction.objects.create(
            name='Казанский Кремль',
            slug='kazan-kremlin',
            description='Историческая крепость',
            latitude=55.8304,
            longitude=49.0661,
            category=self.category,
            rating=4.8,
        )

    def test_list_attractions(self):
        """Test listing attractions."""
        response = self.client.get('/api/attractions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_get_attraction(self):
        """Test getting single attraction."""
        response = self.client.get(f'/api/attractions/{self.attraction.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.attraction.name)

    def test_filter_by_category(self):
        """Test filtering attractions by category."""
        response = self.client.get(
            f'/api/attractions/?category={self.category.id}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

