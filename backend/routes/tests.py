from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from attractions.models import Category, Attraction
from .models import Route, RouteAttraction, UserPreference

User = get_user_model()


class RouteModelTest(TestCase):
    """Tests for Route model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )

    def test_create_route(self):
        """Test route creation."""
        route = Route.objects.create(
            name='Исторический маршрут',
            description='Маршрут по историческим местам',
            user=self.user,
            duration_hours=4,
            budget=Decimal('1000.00'),
            distance_km=Decimal('5.5'),
        )
        self.assertEqual(route.name, 'Исторический маршрут')
        self.assertEqual(route.user, self.user)
        self.assertEqual(route.duration_hours, 4)

    def test_route_str(self):
        """Test route string representation."""
        route = Route.objects.create(
            name='Культурный маршрут',
            description='Описание',
            user=self.user,
            duration_hours=3,
        )
        expected = f"Культурный маршрут ({self.user.email})"
        self.assertEqual(str(route), expected)


class RouteAttractionModelTest(TestCase):
    """Tests for RouteAttraction model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='История', slug='history')
        self.attraction = Attraction.objects.create(
            name='Казанский Кремль',
            slug='kazan-kremlin',
            description='Описание',
            latitude=55.8304,
            longitude=49.0661,
            category=self.category,
        )
        self.route = Route.objects.create(
            name='Тестовый маршрут',
            description='Описание',
            user=self.user,
            duration_hours=2,
        )

    def test_create_route_attraction(self):
        """Test route attraction creation."""
        route_attraction = RouteAttraction.objects.create(
            route=self.route,
            attraction=self.attraction,
            order=1,
            visit_duration=60,
        )
        self.assertEqual(route_attraction.route, self.route)
        self.assertEqual(route_attraction.attraction, self.attraction)
        self.assertEqual(route_attraction.order, 1)


class RouteAPITest(TestCase):
    """Tests for Route API."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name='История', slug='history')
        self.attraction = Attraction.objects.create(
            name='Казанский Кремль',
            slug='kazan-kremlin',
            description='Описание',
            latitude=55.8304,
            longitude=49.0661,
            category=self.category,
        )

    def test_create_route(self):
        """Test route creation via API."""
        data = {
            'name': 'Новый маршрут',
            'description': 'Описание маршрута',
            'duration_hours': 4,
            'budget': '1000.00',
            'attractions': [
                {
                    'attraction_id': self.attraction.id,
                    'order': 1,
                    'visit_duration': 60,
                }
            ],
        }
        response = self.client.post('/api/routes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], data['name'])

    def test_list_routes(self):
        """Test listing user routes."""
        Route.objects.create(
            name='Тестовый маршрут',
            description='Описание',
            user=self.user,
            duration_hours=2,
        )
        response = self.client.get('/api/routes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_get_route(self):
        """Test getting single route."""
        route = Route.objects.create(
            name='Тестовый маршрут',
            description='Описание',
            user=self.user,
            duration_hours=2,
        )
        response = self.client.get(f'/api/routes/{route.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], route.name)



