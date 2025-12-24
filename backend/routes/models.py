from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import User
from attractions.models import Attraction


class Route(models.Model):
    """Tourist route model."""
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routes', verbose_name='Пользователь')
    
    # Route metadata
    duration_hours = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Продолжительность маршрута в часах',
        verbose_name='Длительность (часы)'
    )
    budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.0,
        validators=[MinValueValidator(0.0)],
        verbose_name='Бюджет'
    )
    distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.0,
        verbose_name='Расстояние (км)'
    )
    
    # Route properties
    is_public = models.BooleanField(default=False, verbose_name='Публичный')
    is_favorite = models.BooleanField(default=False, verbose_name='Избранный')
    views_count = models.IntegerField(default=0, verbose_name='Количество просмотров')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршруты'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_public']),
            models.Index(fields=['-views_count']),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class RouteAttraction(models.Model):
    """Many-to-many relationship between Route and Attraction with order."""
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='route_attractions', verbose_name='Маршрут')
    attraction = models.ForeignKey(Attraction, on_delete=models.CASCADE, related_name='route_attractions', verbose_name='Достопримечательность')
    order = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Порядок')
    visit_duration = models.IntegerField(
        help_text='Продолжительность посещения в минутах',
        default=60,
        verbose_name='Длительность посещения'
    )
    notes = models.TextField(blank=True, null=True, verbose_name='Заметки')

    class Meta:
        verbose_name = 'Достопримечательность маршрута'
        verbose_name_plural = 'Достопримечательности маршрутов'
        unique_together = [['route', 'order']]
        ordering = ['route', 'order']
        indexes = [
            models.Index(fields=['route', 'order']),
        ]

    def __str__(self):
        return f"{self.route.name} - {self.attraction.name} (#{self.order})"


class UserPreference(models.Model):
    """User preferences for route generation."""
    INTEREST_CHOICES = [
        ('history', 'История'),
        ('culture', 'Культура'),
        ('architecture', 'Архитектура'),
        ('nature', 'Природа'),
        ('entertainment', 'Развлечения'),
        ('shopping', 'Шоппинг'),
        ('food', 'Еда'),
        ('sports', 'Спорт'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences', verbose_name='Пользователь')
    interests = models.JSONField(
        default=list,
        help_text='Список интересов пользователя',
        verbose_name='Интересы'
    )
    preferred_duration_min = models.IntegerField(
        default=60,
        validators=[MinValueValidator(30)],
        verbose_name='Минимальная длительность (мин)'
    )
    preferred_duration_max = models.IntegerField(
        default=480,
        validators=[MinValueValidator(60)],
        verbose_name='Максимальная длительность (мин)'
    )
    max_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0.0)],
        verbose_name='Максимальный бюджет'
    )
    preferred_categories = models.ManyToManyField(
        'attractions.Category',
        blank=True,
        related_name='user_preferences',
        verbose_name='Предпочитаемые категории'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Предпочтения пользователя'
        verbose_name_plural = 'Предпочтения пользователей'

    def __str__(self):
        return f"Preferences for {self.user.email}"

