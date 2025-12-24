from rest_framework import serializers
from attractions.serializers import AttractionListSerializer
from .models import Route, RouteAttraction, UserPreference


class RouteAttractionSerializer(serializers.ModelSerializer):
    """Serializer for RouteAttraction model."""
    attraction = AttractionListSerializer(read_only=True)
    attraction_id = serializers.PrimaryKeyRelatedField(
        queryset=__import__('attractions.models', fromlist=['Attraction']).Attraction.objects.all(),
        source='attraction',
        write_only=True
    )

    class Meta:
        model = RouteAttraction
        fields = ('id', 'attraction', 'attraction_id', 'order', 'visit_duration', 'notes')
        read_only_fields = ('id',)


class RouteSerializer(serializers.ModelSerializer):
    """Serializer for Route model."""
    user = serializers.StringRelatedField(read_only=True)
    route_attractions = RouteAttractionSerializer(many=True, read_only=True)
    attractions_count = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = (
            'id', 'name', 'description', 'user', 'duration_hours',
            'budget', 'distance_km', 'is_public', 'is_favorite',
            'views_count', 'route_attractions', 'attractions_count',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'views_count', 'created_at', 'updated_at')

    def get_attractions_count(self, obj):
        return obj.route_attractions.count()


class RouteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating routes with attractions."""
    attractions = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text='List of attractions with order and visit_duration'
    )

    class Meta:
        model = Route
        fields = (
            'name', 'description', 'duration_hours', 'budget',
            'distance_km', 'is_public', 'is_favorite', 'attractions'
        )

    def create(self, validated_data):
        attractions_data = validated_data.pop('attractions', [])
        route = Route.objects.create(user=self.context['request'].user, **validated_data)
        
        for att_data in attractions_data:
            RouteAttraction.objects.create(
                route=route,
                attraction_id=att_data.get('attraction_id'),
                order=att_data.get('order', 1),
                visit_duration=att_data.get('visit_duration', 60),
                notes=att_data.get('notes', '')
            )
        
        return route

    def update(self, instance, validated_data):
        attractions_data = validated_data.pop('attractions', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if attractions_data is not None:
            # Delete existing attractions
            instance.route_attractions.all().delete()
            # Create new ones
            for att_data in attractions_data:
                RouteAttraction.objects.create(
                    route=instance,
                    attraction_id=att_data.get('attraction_id'),
                    order=att_data.get('order', 1),
                    visit_duration=att_data.get('visit_duration', 60),
                    notes=att_data.get('notes', '')
                )
        
        return instance


class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for UserPreference model."""
    preferred_categories = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = UserPreference
        fields = (
            'id', 'interests', 'preferred_duration_min', 'preferred_duration_max',
            'max_budget', 'preferred_categories', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

