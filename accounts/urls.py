from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('test/', views.test, name='test'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.me, name='me'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
]
