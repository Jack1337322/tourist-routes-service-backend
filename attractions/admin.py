from django.contrib import admin
from .models import Category, Attraction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Attraction)
class AttractionAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'rating', 'latitude', 'longitude', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'is_free', 'created_at']
    search_fields = ['name', 'description', 'address']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
