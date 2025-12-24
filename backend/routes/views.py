from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from decimal import Decimal
from .models import Route, UserPreference
from .serializers import (
    RouteSerializer, RouteCreateSerializer, UserPreferenceSerializer
)
from .generators import LLMRouteGenerator


class RouteViewSet(viewsets.ModelViewSet):
    """ViewSet for Route model."""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Route.objects.filter(user=user)
        
        # Filter by public routes if requested
        is_public = self.request.query_params.get('public', None)
        if is_public == 'true':
            queryset = Route.objects.filter(is_public=True)
        elif is_public == 'false':
            queryset = Route.objects.filter(user=user, is_public=False)
        
        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RouteCreateSerializer
        return RouteSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """Increment view count for a route."""
        route = self.get_object()
        route.views_count += 1
        route.save()
        return Response({'views_count': route.views_count})

    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status for a route."""
        route = self.get_object()
        route.is_favorite = not route.is_favorite
        route.save()
        return Response({'is_favorite': route.is_favorite})

    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """Get user's favorite routes."""
        routes = self.get_queryset().filter(is_favorite=True)
        serializer = self.get_serializer(routes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate a route using LLM."""
        duration_hours = int(request.data.get('duration_hours', 4))
        
        # Get route name and description from request
        route_name = request.data.get('name', None)
        route_description = request.data.get('description', None)
        
        # Get place types for combining different types of places
        # Examples: ["attractions", "restaurants", "bars", "cafes", "museums", "parks"]
        place_types = request.data.get('place_types', None)
        if place_types is None:
            # Default: only attractions if not specified
            place_types = ['attractions']
        
        # Get preferences from request or user
        category_ids = request.data.get('category_ids', None)
        max_budget = request.data.get('max_budget', None)
        interests = request.data.get('interests', None)
        
        try:
            generator = LLMRouteGenerator()
            preferences = {
                'interests': interests or [],
                'max_budget': float(max_budget) if max_budget else 0.0,
                'category_ids': category_ids or [],
                'route_name': route_name,  # Pass route name to generator
                'route_description': route_description,  # Pass route description to generator
                'place_types': place_types  # Pass place types for combining
            }
            llm_response = generator.generate_route(preferences, duration_hours)
            route = generator.create_route_from_llm_response(request.user, llm_response, duration_hours)
            
            serializer = RouteSerializer(route)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def optimize(self, request, pk=None):
        """Optimize route order using nearest neighbor algorithm."""
        route = self.get_object()
        
        route_attractions = list(route.route_attractions.select_related('attraction').all())
        
        if len(route_attractions) <= 1:
            serializer = self.get_serializer(route)
            return Response(serializer.data)
        
        # Calculate distance helper
        def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            import math
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (math.sin(dlat / 2) ** 2 +
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
                 math.sin(dlon / 2) ** 2)
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        # Get coordinates
        points = [
            (float(ra.attraction.latitude), float(ra.attraction.longitude), ra)
            for ra in route_attractions
        ]
        
        # Reorder using nearest neighbor
        ordered = [points[0]]
        remaining = points[1:]
        
        while remaining:
            current = ordered[-1]
            nearest = min(
                remaining,
                key=lambda p: calculate_distance(
                    current[0], current[1], p[0], p[1]
                )
            )
            ordered.append(nearest)
            remaining.remove(nearest)
        
        # Update order
        for new_order, (_, _, route_attraction) in enumerate(ordered, 1):
            route_attraction.order = new_order
            route_attraction.save()
        
        # Recalculate distance
        total_distance = 0.0
        for i in range(len(ordered) - 1):
            distance = calculate_distance(
                ordered[i][0], ordered[i][1],
                ordered[i + 1][0], ordered[i + 1][1]
            )
            total_distance += distance
        
        route.distance_km = Decimal(str(total_distance))
        route.save()
        
        serializer = self.get_serializer(route)
        return Response(serializer.data)


class UserPreferenceViewSet(viewsets.ModelViewSet):
    """ViewSet for UserPreference model."""
    serializer_class = UserPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get', 'put'])
    def my_preferences(self, request):
        """Get or update current user preferences."""
        preference, created = UserPreference.objects.get_or_create(user=request.user)
        
        if request.method == 'GET':
            serializer = self.get_serializer(preference)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            serializer = self.get_serializer(preference, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
