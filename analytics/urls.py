from django.urls import path
from . import views

urlpatterns = [
    path('popular/', views.popular_routes, name='popular-routes'),
    path('stats/', views.route_statistics, name='route-statistics'),
    path('attractions/stats/', views.attraction_statistics, name='attraction-statistics'),
    path('charts/popularity/', views.route_popularity_chart, name='popularity-chart'),
    path('charts/categories/', views.category_distribution_chart, name='category-chart'),
    path('charts/ratings/', views.rating_distribution_chart, name='rating-chart'),
    path('user/', views.user_analytics, name='user-analytics'),
]
