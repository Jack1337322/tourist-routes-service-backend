"""
Route generation modules using LLM and algorithms.
"""
import math
import logging
from typing import List, Dict, Optional
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from attractions.models import Attraction, Category
from routes.models import Route, RouteAttraction, UserPreference

logger = logging.getLogger(__name__)


class LLMRouteGenerator:
    """Generate routes using OpenAI LLM."""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OpenAI API key not set. LLM generation will not work.")
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def generate_route(self, user_preferences: Dict, duration_hours: int = 4) -> Dict:
        """Generate route using OpenAI LLM."""
        if not self.api_key:
            raise ValueError("OpenAI API key is not configured")
        
        try:
            import openai
            
            # Get available attractions
            attractions = Attraction.objects.filter(is_active=True)
            if user_preferences.get('category_ids'):
                attractions = attractions.filter(category_id__in=user_preferences['category_ids'])
            
            # Build prompt
            attractions_list = "\n".join([
                f"- {att.name} ({att.category.name if att.category else 'Без категории'}) - {att.short_description or att.description[:100]}"
                for att in attractions[:50]  # Limit to avoid token limits
            ])
            
            prompt = f"""Создай туристический маршрут по Казани на {duration_hours} часов.

Интересы пользователя: {', '.join(user_preferences.get('interests', []))}
Бюджет: {user_preferences.get('max_budget', 0)} рублей

Доступные достопримечательности:
{attractions_list}

Требования:
1. Выбери 4-8 достопримечательностей, которые логично посетить за {duration_hours} часов
2. Расположи их в оптимальном порядке (учитывая расстояние между ними)
3. Учти интересы пользователя
4. Учти бюджет

Верни ответ в формате JSON:
{{
    "name": "Название маршрута",
    "description": "Подробное описание маршрута",
    "attractions": [
        {{"name": "Название достопримечательности", "order": 1, "visit_duration": 60}},
        ...
    ]
}}"""
            
            # Call OpenAI API
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты помощник по планированию туристических маршрутов в Казани."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response (might be wrapped in markdown)
            import json
            import re
            
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                route_data = json.loads(json_match.group())
            else:
                # Fallback: try to parse entire content
                route_data = json.loads(content)
            
            return route_data
        
        except Exception as e:
            logger.error(f"Error generating route with LLM: {e}")
            raise
    
    def create_route_from_llm_response(self, user, llm_response: Dict, duration_hours: int) -> Route:
        """Create Route object from LLM response."""
        # Map attraction names to actual Attraction objects
        attractions_map = {}
        for att in Attraction.objects.filter(is_active=True):
            attractions_map[att.name.lower()] = att
        
        route = Route.objects.create(
            user=user,
            name=llm_response.get('name', 'Сгенерированный маршрут'),
            description=llm_response.get('description', ''),
            duration_hours=duration_hours,
            budget=Decimal('0.0'),
            distance_km=Decimal('0.0'),
            is_public=False
        )
        
        # Add attractions
        total_distance = 0.0
        prev_lat = None
        prev_lon = None
        
        for att_data in llm_response.get('attractions', []):
            att_name = att_data.get('name', '').lower()
            attraction = attractions_map.get(att_name)
            
            if not attraction:
                # Try fuzzy matching
                for key, att in attractions_map.items():
                    if att_name in key or key in att_name:
                        attraction = att
                        break
            
            if attraction:
                order = att_data.get('order', 1)
                visit_duration = att_data.get('visit_duration', 60)
                
                RouteAttraction.objects.create(
                    route=route,
                    attraction=attraction,
                    order=order,
                    visit_duration=visit_duration
                )
                
                # Calculate distance
                if prev_lat and prev_lon:
                    distance = self._calculate_distance(
                        prev_lat, prev_lon,
                        float(attraction.latitude), float(attraction.longitude)
                    )
                    total_distance += distance
                
                prev_lat = float(attraction.latitude)
                prev_lon = float(attraction.longitude)
        
        route.distance_km = Decimal(str(total_distance))
        route.save()
        
        return route


class AlgorithmicRouteGenerator:
    """Generate routes using algorithms."""
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points."""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    def generate_route(
        self,
        user,
        duration_hours: int = 4,
        category_ids: Optional[List[int]] = None,
        max_budget: Decimal = Decimal('0.0'),
        interests: Optional[List[str]] = None,
        start_latitude: Optional[float] = None,
        start_longitude: Optional[float] = None
    ) -> Route:
        """Generate route using algorithm."""
        # Get preferences if available
        try:
            preferences = user.preferences
            if not category_ids:
                category_ids = list(preferences.preferred_categories.values_list('id', flat=True))
            if not max_budget:
                max_budget = preferences.max_budget
            if not interests:
                interests = preferences.interests
        except UserPreference.DoesNotExist:
            pass
        
        # Filter attractions
        attractions = Attraction.objects.filter(is_active=True)
        if category_ids:
            attractions = attractions.filter(category_id__in=category_ids)
        
        # Filter by budget
        if max_budget and max_budget > 0:
            attractions = attractions.filter(
                Q(is_free=True) | Q(price__lte=max_budget)
            )
        
        # Convert to list and sort by rating
        attractions_list = list(attractions.order_by('-rating'))
        
        if not attractions_list:
            raise ValueError("No attractions found matching criteria")
        
        # Select starting point
        if start_latitude and start_longitude:
            # Find nearest attraction to start point
            start_point = min(
                attractions_list,
                key=lambda a: self._calculate_distance(
                    start_latitude, start_longitude,
                    float(a.latitude), float(a.longitude)
                )
            )
        else:
            start_point = attractions_list[0]  # Highest rated
        
        # Build route using nearest neighbor algorithm
        selected_attractions = [start_point]
        remaining_attractions = [a for a in attractions_list if a != start_point]
        
        total_duration = start_point.visit_duration
        total_budget = Decimal('0.0') if start_point.is_free else start_point.price
        max_duration = duration_hours * 60  # Convert to minutes
        
        current_lat = float(start_point.latitude)
        current_lon = float(start_point.longitude)
        
        while remaining_attractions and total_duration < max_duration:
            # Find nearest attraction
            nearest = min(
                remaining_attractions,
                key=lambda a: self._calculate_distance(
                    current_lat, current_lon,
                    float(a.latitude), float(a.longitude)
                )
            )
            
            # Check if we can add it
            travel_time = self._calculate_distance(
                current_lat, current_lon,
                float(nearest.latitude), float(nearest.longitude)
            ) * 2  # Approximate travel time (2 min per km)
            
            visit_duration = nearest.visit_duration
            cost = Decimal('0.0') if nearest.is_free else nearest.price
            
            if (total_duration + travel_time + visit_duration <= max_duration and
                (max_budget == 0 or total_budget + cost <= max_budget)):
                
                selected_attractions.append(nearest)
                total_duration += travel_time + visit_duration
                total_budget += cost
                current_lat = float(nearest.latitude)
                current_lon = float(nearest.longitude)
                remaining_attractions.remove(nearest)
            else:
                break
        
        # Create route
        route = Route.objects.create(
            user=user,
            name=f"Маршрут на {duration_hours} часов",
            description=f"Автоматически сгенерированный маршрут по {len(selected_attractions)} достопримечательностям",
            duration_hours=duration_hours,
            budget=total_budget,
            distance_km=Decimal('0.0'),
            is_public=False
        )
        
        # Calculate total distance
        total_distance = 0.0
        for i in range(len(selected_attractions) - 1):
            distance = self._calculate_distance(
                float(selected_attractions[i].latitude),
                float(selected_attractions[i].longitude),
                float(selected_attractions[i + 1].latitude),
                float(selected_attractions[i + 1].longitude)
            )
            total_distance += distance
        
        route.distance_km = Decimal(str(total_distance))
        route.save()
        
        # Add attractions to route
        for order, attraction in enumerate(selected_attractions, 1):
            RouteAttraction.objects.create(
                route=route,
                attraction=attraction,
                order=order,
                visit_duration=attraction.visit_duration
            )
        
        return route


class HybridRouteGenerator:
    """Hybrid generator combining LLM and algorithms."""
    
    def __init__(self):
        self.llm_generator = LLMRouteGenerator()
        self.algorithmic_generator = AlgorithmicRouteGenerator()
    
    def generate_route(
        self,
        user,
        duration_hours: int = 4,
        use_llm: bool = True,
        **kwargs
    ) -> Route:
        """Generate route using hybrid approach."""
        if use_llm and settings.OPENAI_API_KEY:
            try:
                # Get user preferences
                preferences_data = {}
                try:
                    prefs = user.preferences
                    preferences_data = {
                        'interests': prefs.interests,
                        'max_budget': float(prefs.max_budget),
                        'category_ids': list(prefs.preferred_categories.values_list('id', flat=True))
                    }
                except UserPreference.DoesNotExist:
                    preferences_data = kwargs.get('preferences', {})
                
                # Generate with LLM
                llm_response = self.llm_generator.generate_route(
                    preferences_data,
                    duration_hours
                )
                
                # Create route from LLM response
                route = self.llm_generator.create_route_from_llm_response(
                    user,
                    llm_response,
                    duration_hours
                )
                
                # Optimize order using algorithm
                self._optimize_route_order(route)
                
                return route
            
            except Exception as e:
                logger.warning(f"LLM generation failed, falling back to algorithm: {e}")
        
        # Fallback to algorithmic generation
        return self.algorithmic_generator.generate_route(
            user,
            duration_hours,
            **kwargs
        )
    
    def _optimize_route_order(self, route: Route):
        """Optimize the order of attractions in route using nearest neighbor."""
        route_attractions = list(route.route_attractions.select_related('attraction').all())
        
        if len(route_attractions) <= 1:
            return
        
        # Get coordinates
        points = [
            (float(ra.attraction.latitude), float(ra.attraction.longitude), ra)
            for ra in route_attractions
        ]
        
        # Reorder using nearest neighbor
        ordered = [points[0]]
        remaining = points[1:]
        
        while remaining:
            current = ordered[-1]
            nearest = min(
                remaining,
                key=lambda p: self._calculate_distance(
                    current[0], current[1], p[0], p[1]
                )
            )
            ordered.append(nearest)
            remaining.remove(nearest)
        
        # Update order
        for new_order, (_, _, route_attraction) in enumerate(ordered, 1):
            route_attraction.order = new_order
            route_attraction.save()
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points."""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        return R * c
