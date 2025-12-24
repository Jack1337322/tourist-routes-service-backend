from django.urls import path
from . import views

urlpatterns = [
    path('popular/', views.popular_routes, name='popular-routes'),
    path('stats/', views.route_statistics, name='route-statistics'),
    path('attractions/stats/', views.attraction_statistics, name='attraction-statistics'),
    path('popular-attractions/', views.popular_attractions, name='popular-attractions'),
    path('categories/popularity/', views.category_popularity, name='category-popularity'),
    path('attractions/by-category/', views.popular_attractions_by_category, name='attractions-by-category'),
    path('trends/attractions/', views.attraction_usage_trends, name='attraction-trends'),
    path('categories/in-routes/', views.category_distribution_in_routes, name='category-distribution'),
    path('user/', views.user_analytics, name='user-analytics'),
]
