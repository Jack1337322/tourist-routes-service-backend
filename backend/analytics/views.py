from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from routes.models import Route, RouteAttraction
from attractions.models import Attraction, Category


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def popular_routes(request):
    """Get popular routes based on views."""
    limit = int(request.query_params.get('limit', 10))
    
    routes = Route.objects.filter(is_public=True).order_by('-views_count')[:limit]
    
    data = [{
        'id': route.id,
        'name': route.name,
        'views_count': route.views_count,
        'user': route.user.email,
        'created_at': route.created_at
    } for route in routes]
    
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def route_statistics(request):
    """Get route statistics."""
    total_routes = Route.objects.count()
    public_routes = Route.objects.filter(is_public=True).count()
    total_views = Route.objects.aggregate(total=Count('views_count'))['total'] or 0
    avg_duration = Route.objects.aggregate(avg=Avg('duration_hours'))['avg'] or 0
    
    # Routes by duration
    duration_stats = Route.objects.values('duration_hours').annotate(
        count=Count('id')
    ).order_by('duration_hours')
    
    # Most popular categories
    category_stats = Category.objects.annotate(
        route_count=Count('attractions__route_attractions__route', distinct=True)
    ).order_by('-route_count')[:10]
    
    return Response({
        'total_routes': total_routes,
        'public_routes': public_routes,
        'total_views': total_views,
        'avg_duration': round(avg_duration, 2),
        'duration_distribution': list(duration_stats),
        'popular_categories': [
            {'name': cat.name, 'count': cat.route_count}
            for cat in category_stats
        ]
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def attraction_statistics(request):
    """Get attraction statistics."""
    total_attractions = Attraction.objects.filter(is_active=True).count()
    avg_rating = Attraction.objects.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Attractions by category
    category_stats = Category.objects.annotate(
        count=Count('attractions', filter=Q(attractions__is_active=True))
    ).filter(count__gt=0).order_by('-count')
    
    # Rating distribution
    rating_ranges = [
        (0, 1, '0-1'),
        (1, 2, '1-2'),
        (2, 3, '2-3'),
        (3, 4, '3-4'),
        (4, 5, '4-5'),
    ]
    
    rating_dist = []
    for min_rating, max_rating, label in rating_ranges:
        count = Attraction.objects.filter(
            is_active=True,
            rating__gte=min_rating,
            rating__lt=max_rating
        ).count()
        rating_dist.append({'range': label, 'count': count})
    
    return Response({
        'total_attractions': total_attractions,
        'avg_rating': round(avg_rating, 2),
        'by_category': [
            {'name': cat.name, 'count': cat.count}
            for cat in category_stats
        ],
        'rating_distribution': rating_dist
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def popular_attractions(request):
    """Get popular attractions based on mentions in routes."""
    limit = int(request.query_params.get('limit', 20))
    category_id = request.query_params.get('category_id', None)
    
    # Base queryset: count mentions in routes
    queryset = Attraction.objects.filter(is_active=True).annotate(
        mention_count=Count('route_attractions', distinct=True)
    ).filter(mention_count__gt=0)
    
    # Filter by category if provided
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    # Order by mention count and get top N
    attractions = queryset.select_related('category').order_by('-mention_count')[:limit]
    
    data = [{
        'id': attr.id,
        'name': attr.name,
        'mention_count': attr.mention_count,
        'category': attr.category.name if attr.category else None,
        'category_id': attr.category.id if attr.category else None,
        'rating': float(attr.rating),
        'address': attr.address,
    } for attr in attractions]
    
    return Response({'attractions': data})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def category_popularity(request):
    """Get category popularity based on routes using attractions from each category."""
    categories = Category.objects.annotate(
        route_count=Count('attractions__route_attractions__route', distinct=True),
        attraction_count=Count('attractions', filter=Q(attractions__is_active=True), distinct=True)
    ).filter(route_count__gt=0).order_by('-route_count')
    
    data = [{
        'id': cat.id,
        'name': cat.name,
        'route_count': cat.route_count,
        'attraction_count': cat.attraction_count,
    } for cat in categories]
    
    return Response({'categories': data})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def popular_attractions_by_category(request):
    """Get top attractions grouped by category."""
    limit_per_category = int(request.query_params.get('limit', 5))
    
    categories = Category.objects.annotate(
        attraction_count=Count('attractions', filter=Q(attractions__is_active=True))
    ).filter(attraction_count__gt=0)
    
    result = []
    for category in categories:
        # Get top attractions in this category
        attractions = Attraction.objects.filter(
            category=category,
            is_active=True
        ).annotate(
            mention_count=Count('route_attractions', distinct=True)
        ).filter(mention_count__gt=0).order_by('-mention_count')[:limit_per_category]
        
        if attractions.exists():
            result.append({
                'category': category.name,
                'category_id': category.id,
                'attractions': [{
                    'id': attr.id,
                    'name': attr.name,
                    'mention_count': attr.mention_count,
                    'rating': float(attr.rating),
                } for attr in attractions]
            })
    
    return Response({'by_category': result})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def attraction_usage_trends(request):
    """Get trends of attraction usage over time."""
    days = int(request.query_params.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get routes created in the period
    routes = Route.objects.filter(created_at__gte=start_date).values('created_at__date').annotate(
        route_count=Count('id', distinct=True),
        attraction_mentions=Count('route_attractions', distinct=True)
    ).order_by('created_at__date')
    
    data = [{
        'date': str(route['created_at__date']),
        'routes_created': route['route_count'],
        'attraction_mentions': route['attraction_mentions'],
    } for route in routes]
    
    return Response({'trends': data})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def category_distribution_in_routes(request):
    """Get distribution of categories in routes."""
    # Count how many routes use each category
    categories = Category.objects.annotate(
        route_count=Count('attractions__route_attractions__route', distinct=True),
        total_mentions=Count('attractions__route_attractions', distinct=True)
    ).filter(route_count__gt=0).order_by('-route_count')
    
    data = [{
        'category': cat.name,
        'category_id': cat.id,
        'route_count': cat.route_count,
        'total_mentions': cat.total_mentions,
    } for cat in categories]
    
    return Response({'distribution': data})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_analytics(request):
    """Get analytics for current user."""
    user = request.user
    
    user_routes = Route.objects.filter(user=user)
    total_routes = user_routes.count()
    total_views = user_routes.aggregate(total=Count('views_count'))['total'] or 0
    favorite_routes = user_routes.filter(is_favorite=True).count()
    
    # Routes created over time
    last_30_days = timezone.now() - timedelta(days=30)
    routes_created = user_routes.filter(created_at__gte=last_30_days).count()
    
    # Most used categories
    user_attractions = Attraction.objects.filter(
        route_attractions__route__user=user
    ).distinct()
    
    category_usage = Category.objects.filter(
        attractions__in=user_attractions
    ).annotate(
        usage_count=Count('attractions', filter=Q(attractions__in=user_attractions))
    ).order_by('-usage_count')[:5]
    
    return Response({
        'total_routes': total_routes,
        'total_views': total_views,
        'favorite_routes': favorite_routes,
        'routes_last_30_days': routes_created,
        'top_categories': [
            {'name': cat.name, 'count': cat.usage_count}
            for cat in category_usage
        ]
    })

