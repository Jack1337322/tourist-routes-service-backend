from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.http import HttpResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
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
def route_popularity_chart(request):
    """Generate route popularity chart."""
    limit = int(request.query_params.get('limit', 10))
    
    routes = Route.objects.filter(is_public=True).order_by('-views_count')[:limit]
    
    # Create DataFrame
    df = pd.DataFrame([{
        'name': route.name[:30] + '...' if len(route.name) > 30 else route.name,
        'views': route.views_count
    } for route in routes])
    
    # Create plot
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x='views', y='name', palette='viridis')
    plt.title('Популярные маршруты', fontsize=16, fontweight='bold')
    plt.xlabel('Количество просмотров', fontsize=12)
    plt.ylabel('Маршрут', fontsize=12)
    plt.tight_layout()
    
    # Save to buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    # Return as base64
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return Response({'image': f'data:image/png;base64,{image_base64}'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def category_distribution_chart(request):
    """Generate category distribution chart."""
    categories = Category.objects.annotate(
        count=Count('attractions', filter=Q(attractions__is_active=True))
    ).filter(count__gt=0).order_by('-count')[:10]
    
    # Create DataFrame
    df = pd.DataFrame([{
        'category': cat.name,
        'count': cat.count
    } for cat in categories])
    
    # Create plot
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x='count', y='category', palette='mako')
    plt.title('Распределение достопримечательностей по категориям', fontsize=16, fontweight='bold')
    plt.xlabel('Количество', fontsize=12)
    plt.ylabel('Категория', fontsize=12)
    plt.tight_layout()
    
    # Save to buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    # Return as base64
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return Response({'image': f'data:image/png;base64,{image_base64}'})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def rating_distribution_chart(request):
    """Generate rating distribution chart."""
    attractions = Attraction.objects.filter(is_active=True)
    
    # Create DataFrame
    df = pd.DataFrame(list(attractions.values('rating')))
    
    # Create plot
    plt.figure(figsize=(10, 6))
    sns.histplot(data=df, x='rating', bins=20, kde=True, color='skyblue')
    plt.title('Распределение рейтингов достопримечательностей', fontsize=16, fontweight='bold')
    plt.xlabel('Рейтинг', fontsize=12)
    plt.ylabel('Количество', fontsize=12)
    plt.xlim(0, 5)
    plt.tight_layout()
    
    # Save to buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    plt.close()
    
    # Return as base64
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    return Response({'image': f'data:image/png;base64,{image_base64}'})


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
