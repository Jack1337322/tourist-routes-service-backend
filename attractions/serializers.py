from rest_framework import serializers
from .models import Category, Attraction


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'icon')


class AttractionSerializer(serializers.ModelSerializer):
    """Serializer for Attraction model."""
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Attraction
        fields = (
            'id', 'name', 'slug', 'description', 'short_description',
            'latitude', 'longitude', 'address', 'category', 'category_id',
            'rating', 'visit_duration', 'price', 'is_free',
            'image', 'website', 'created_at', 'updated_at', 'is_active'
        )
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')


class AttractionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for attraction lists."""
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Attraction
        fields = (
            'id', 'name', 'slug', 'short_description',
            'latitude', 'longitude', 'category', 'rating',
            'visit_duration', 'price', 'is_free', 'image'
        )
