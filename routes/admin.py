from django.contrib import admin
from .models import Route, RouteAttraction, UserPreference


class RouteAttractionInline(admin.TabularInline):
    model = RouteAttraction
    extra = 1
    ordering = ['order']


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'duration_hours', 'budget', 'is_public', 'views_count', 'created_at']
    list_filter = ['is_public', 'is_favorite', 'created_at']
    search_fields = ['name', 'description', 'user__email']
    inlines = [RouteAttractionInline]
    readonly_fields = ['created_at', 'updated_at', 'views_count']


@admin.register(RouteAttraction)
class RouteAttractionAdmin(admin.ModelAdmin):
    list_display = ['route', 'attraction', 'order', 'visit_duration']
    list_filter = ['route', 'attraction']
    ordering = ['route', 'order']


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_duration_min', 'preferred_duration_max', 'max_budget']
    search_fields = ['user__email']
    filter_horizontal = ['preferred_categories']
