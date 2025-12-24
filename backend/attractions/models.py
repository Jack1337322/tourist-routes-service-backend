from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    """Category for attractions."""
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL')
    description = models.TextField(blank=True, null=True, verbose_name='Описание')
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name='Иконка')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Attraction(models.Model):
    """Tourist attraction model."""
    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='URL')
    description = models.TextField(verbose_name='Описание')
    short_description = models.CharField(max_length=500, blank=True, null=True, verbose_name='Краткое описание')
    
    # Location
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Широта')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='Долгота')
    address = models.CharField(max_length=300, blank=True, null=True, verbose_name='Адрес')
    
    # Metadata
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='attractions', verbose_name='Категория')
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name='Рейтинг'
    )
    visit_duration = models.IntegerField(help_text='Продолжительность посещения в минутах', default=60, verbose_name='Длительность посещения')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, verbose_name='Цена')
    is_free = models.BooleanField(default=False, verbose_name='Бесплатно')
    
    # Media
    image = models.ImageField(upload_to='attractions/', blank=True, null=True, verbose_name='Изображение')
    website = models.URLField(blank=True, null=True, verbose_name='Веб-сайт')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Достопримечательность'
        verbose_name_plural = 'Достопримечательности'
        ordering = ['-rating', 'name']
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['category']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return self.name

