from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RouteViewSet, UserPreferenceViewSet

router = DefaultRouter()
router.register(r'', RouteViewSet, basename='route')
router.register(r'preferences', UserPreferenceViewSet, basename='preference')

urlpatterns = [
    path('', include(router.urls)),
]

