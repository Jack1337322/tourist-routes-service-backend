from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Route, UserPreference
from .serializers import (
    RouteSerializer, RouteCreateSerializer, UserPreferenceSerializer
)
from .generators import HybridRouteGenerator, AlgorithmicRouteGenerator, LLMRouteGenerator


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
        """Generate a route using LLM or algorithm."""
        # #region agent log
        import json
        with open('/Users/jack/Desktop/tourist-routes-service/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'sessionId': 'debug-session',
                'runId': 'run1',
                'hypothesisId': 'A',
                'location': 'routes/views.py:61',
                'message': 'Route generation request received',
                'data': {
                    'duration_hours': request.data.get('duration_hours', 4),
                    'generator_type': request.data.get('generator_type', 'hybrid'),
                    'use_llm': request.data.get('use_llm', True),
                    'category_ids': request.data.get('category_ids', None),
                    'max_budget': request.data.get('max_budget', None),
                    'interests': request.data.get('interests', None),
                },
                'timestamp': int(__import__('time').time() * 1000)
            }) + '\n')
        # #endregion
        
        duration_hours = int(request.data.get('duration_hours', 4))
        generator_type = request.data.get('generator_type', 'hybrid')  # 'llm', 'algorithmic', 'hybrid'
        use_llm = request.data.get('use_llm', True)
        
        # Get preferences from request or user
        category_ids = request.data.get('category_ids', None)
        max_budget = request.data.get('max_budget', None)
        interests = request.data.get('interests', None)
        start_latitude = request.data.get('start_latitude', None)
        start_longitude = request.data.get('start_longitude', None)
        
        try:
            if generator_type == 'llm':
                generator = LLMRouteGenerator()
                preferences = {
                    'interests': interests or [],
                    'max_budget': float(max_budget) if max_budget else 0.0,
                    'category_ids': category_ids or []
                }
                llm_response = generator.generate_route(preferences, duration_hours)
                route = generator.create_route_from_llm_response(request.user, llm_response, duration_hours)
            elif generator_type == 'algorithmic':
                generator = AlgorithmicRouteGenerator()
                route = generator.generate_route(
                    request.user,
                    duration_hours,
                    category_ids=category_ids,
                    max_budget=max_budget,
                    interests=interests,
                    start_latitude=start_latitude,
                    start_longitude=start_longitude
                )
            else:  # hybrid
                generator = HybridRouteGenerator()
                route = generator.generate_route(
                    request.user,
                    duration_hours,
                    use_llm=use_llm,
                    category_ids=category_ids,
                    max_budget=max_budget,
                    interests=interests,
                    start_latitude=start_latitude,
                    start_longitude=start_longitude
                )
            
            serializer = RouteSerializer(route)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def optimize(self, request, pk=None):
        """Optimize route order."""
        route = self.get_object()
        
        # Reorder attractions using nearest neighbor
        from .generators import HybridRouteGenerator
        generator = HybridRouteGenerator()
        generator._optimize_route_order(route)
        
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
