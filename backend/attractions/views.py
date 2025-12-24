from rest_framework import viewsets, filters, permissions
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Attraction
from .serializers import CategorySerializer, AttractionSerializer, AttractionListSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Category model (read-only)."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class AttractionViewSet(viewsets.ModelViewSet):
    """ViewSet for Attraction model."""
    queryset = Attraction.objects.filter(is_active=True)
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_free']
    search_fields = ['name', 'description', 'address']
    ordering_fields = ['rating', 'name', 'created_at']
    ordering = ['-rating', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return AttractionListSerializer
        return AttractionSerializer

    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Get attractions near a location."""
        latitude = request.query_params.get('lat')
        longitude = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 5.0))  # km

        if not latitude or not longitude:
            return Response(
                {'error': 'Необходимо указать lat и lng'},
                status=400
            )

        # Simple distance calculation (Haversine would be better)
        # For now, using approximate filtering
        lat = float(latitude)
        lng = float(longitude)
        
        # Approximate: 1 degree ≈ 111 km
        lat_range = radius / 111.0
        lng_range = radius / (111.0 * abs(lat / 90.0) if lat != 0 else 111.0)

        attractions = self.queryset.filter(
            latitude__range=(lat - lat_range, lat + lat_range),
            longitude__range=(lng - lng_range, lng + lng_range)
        )
        
        serializer = self.get_serializer(attractions, many=True)
        return Response(serializer.data)

