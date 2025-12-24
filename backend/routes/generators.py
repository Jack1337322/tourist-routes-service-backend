"""
Route generation modules using LLM and algorithms.
"""
import math
import logging
import json
import re
from typing import List, Dict, Optional
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from attractions.models import Attraction, Category
from routes.models import Route, RouteAttraction, UserPreference

logger = logging.getLogger(__name__)


class LLMRouteGenerator:
    """Generate routes using Perplexity LLM."""
    
    def __init__(self):
        try:
            self.api_key = getattr(settings, 'PERPLEXITY_API_KEY', '')
        except AttributeError:
            self.api_key = ''
        # Model name for Perplexity API
        # Valid models: sonar-pro, sonar-online, sonar-reasoner, etc.
        # See https://docs.perplexity.ai/getting-started/models for full list
        default_model = 'sonar-pro'
        self.model = getattr(settings, 'PERPLEXITY_MODEL', default_model)
        if not self.api_key:
            logger.warning("Perplexity API key not set. LLM generation will not work.")
    
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
    
    def _detect_place_types_from_text(self, text: str) -> List[str]:
        """Detect place types from route name or description."""
        if not text:
            return ['attractions']
        
        text_lower = text.lower()
        detected_types = []
        
        # Keywords mapping
        keywords_map = {
            'attractions': ['достопримечательность', 'памятник', 'архитектур', 'исторический', 'культурный', 'экскурсия', 'обзор'],
            'restaurants': ['ресторан', 'рестораны', 'еда', 'кухня', 'гастроном', 'обед', 'ужин', 'трапеза'],
            'bars': ['бар', 'бары', 'паб', 'пабы', 'пивной', 'коктейль', 'напиток', 'алкоголь'],
            'cafes': ['кафе', 'кофе', 'кофейня', 'завтрак', 'перекус', 'десерт'],
            'museums': ['музей', 'музеи', 'экспозиция', 'выставка', 'коллекция', 'галерея'],
            'parks': ['парк', 'парки', 'сквер', 'скверы', 'природа', 'набережная', 'прогулка'],
            'entertainment': ['развлечение', 'развлечения', 'клуб', 'клубы', 'кинотеатр', 'театр', 'концерт'],
            'shopping': ['магазин', 'магазины', 'торговый', 'шоппинг', 'покупка', 'сувенир'],
            'hotels': ['отель', 'отели', 'гостиница', 'размещение', 'ночлег']
        }
        
        # Check for each type
        for place_type, keywords in keywords_map.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_types.append(place_type)
        
        # If nothing detected, default to attractions
        return detected_types if detected_types else ['attractions']
    
    def generate_route(self, user_preferences: Dict, duration_hours: int = 4) -> Dict:
        """Generate route using Perplexity LLM."""
        if not self.api_key:
            raise ValueError("Perplexity API key is not configured")
        
        try:
            from perplexity import Perplexity
            import re
            
            # Get available attractions
            attractions = Attraction.objects.filter(is_active=True)
            if user_preferences.get('category_ids'):
                attractions = attractions.filter(category_id__in=user_preferences['category_ids'])
            
            # Build prompt
            attractions_list = "\n".join([
                f"- {att.name} ({att.category.name if att.category else 'Без категории'}) - {att.short_description or att.description[:100]}"
                for att in attractions[:50]  # Limit to avoid token limits
            ])
            
            # Get route name and description from preferences
            route_name = user_preferences.get('route_name', None)
            route_description = user_preferences.get('route_description', None)
            place_types = user_preferences.get('place_types', None)
            
            # If place_types not explicitly provided, detect from name/description
            if place_types is None or place_types == ['attractions']:
                # Combine name and description for detection
                combined_text = ""
                if route_name:
                    combined_text += route_name + " "
                if route_description:
                    combined_text += route_description
                
                if combined_text.strip():
                    place_types = self._detect_place_types_from_text(combined_text)
                else:
                    place_types = ['attractions']
            
            # Build base prompt
            base_prompt = f"""Создай туристический маршрут по Казани на {duration_hours} часов."""
            
            # Add route name if provided
            if route_name:
                base_prompt += f"\n\nНазвание маршрута (используй это название или похожее): {route_name}"
            
            # Add route description if provided
            if route_description:
                base_prompt += f"\n\nОписание маршрута от пользователя: {route_description}"
            
            # Add user preferences
            base_prompt += f"""

Интересы пользователя: {', '.join(user_preferences.get('interests', [])) if user_preferences.get('interests') else 'не указаны'}
Бюджет: {user_preferences.get('max_budget', 0)} рублей"""
            
            # Map place types to Russian descriptions
            place_types_map = {
                'attractions': 'достопримечательности (памятники, архитектурные объекты, исторические места)',
                'restaurants': 'рестораны (места для обеда и ужина)',
                'bars': 'бары и пабы (места для вечерних напитков)',
                'cafes': 'кафе (места для легких перекусов и кофе)',
                'museums': 'музеи (культурные и исторические экспозиции)',
                'parks': 'парки и скверы (природные зоны для прогулок)',
                'entertainment': 'развлекательные заведения (клубы, кинотеатры, развлечения)',
                'shopping': 'магазины и торговые центры',
                'hotels': 'отели и места размещения'
            }
            
            # Build instruction about route theme and place types
            theme_instruction = ""
            
            # Check if multiple place types are detected or requested
            if len(place_types) > 1 or (len(place_types) == 1 and place_types[0] != 'attractions'):
                # Build time distribution based on selected place types (without explicitly listing types)
                time_distribution = []
                
                # Morning (9-12)
                morning_types = []
                if 'attractions' in place_types:
                    morning_types.append('достопримечательности')
                if 'museums' in place_types:
                    morning_types.append('музеи')
                if 'parks' in place_types:
                    morning_types.append('парки')
                if morning_types:
                    time_distribution.append(f"- Утро (9-12): {', '.join(morning_types)}")
                
                # Lunch (12-14)
                lunch_types = []
                if 'restaurants' in place_types:
                    lunch_types.append('рестораны')
                if 'cafes' in place_types:
                    lunch_types.append('кафе')
                if lunch_types:
                    time_distribution.append(f"- Обед (12-14): {', '.join(lunch_types)}")
                
                # Afternoon (14-18)
                afternoon_types = []
                if 'attractions' in place_types:
                    afternoon_types.append('достопримечательности')
                if 'museums' in place_types:
                    afternoon_types.append('музеи')
                if 'parks' in place_types:
                    afternoon_types.append('парки')
                if 'shopping' in place_types:
                    afternoon_types.append('магазины')
                if afternoon_types:
                    time_distribution.append(f"- День (14-18): {', '.join(afternoon_types)}")
                
                # Evening (18-22)
                evening_types = []
                if 'bars' in place_types:
                    evening_types.append('бары')
                if 'restaurants' in place_types:
                    evening_types.append('рестораны')
                if 'entertainment' in place_types:
                    evening_types.append('развлечения')
                if evening_types:
                    time_distribution.append(f"- Вечер (18-22): {', '.join(evening_types)}")
                
                if time_distribution:
                    theme_instruction = "\n\nВАЖНО: Маршрут должен включать разные типы мест, соответствующие теме маршрута. Распредели места по маршруту логично по времени дня:\n"
                    theme_instruction += "\n".join(time_distribution)
                    theme_instruction += "\n\nСоздай сбалансированный маршрут, который включает соответствующие типы мест в логичной последовательности."
            
            # If only attractions, add general instruction based on route name
            elif route_name:
                route_name_lower = route_name.lower()
                if any(word in route_name_lower for word in ['бар', 'бары', 'клуб', 'клубы', 'развлечения', 'ночная']):
                    theme_instruction = "\n\nВАЖНО: Маршрут должен быть посвящен барам, клубам и ночным развлечениям Казани. Выбери бары, пабы, клубы и развлекательные заведения."
                elif any(word in route_name_lower for word in ['еда', 'ресторан', 'кафе', 'кухня', 'гастроном']):
                    theme_instruction = "\n\nВАЖНО: Маршрут должен быть посвящен гастрономии Казани. Выбери рестораны, кафе и места с местной кухней."
                elif any(word in route_name_lower for word in ['история', 'исторический', 'музей', 'памятник']):
                    theme_instruction = "\n\nВАЖНО: Маршрут должен быть посвящен истории и культуре Казани. Выбери исторические достопримечательности и музеи."
                elif any(word in route_name_lower for word in ['природа', 'парк', 'сквер', 'набережная']):
                    theme_instruction = "\n\nВАЖНО: Маршрут должен быть посвящен природе и паркам Казани. Выбери парки, скверы и природные достопримечательности."
            
            prompt = f"""{base_prompt}{theme_instruction}

Доступные достопримечательности:
{attractions_list}

ВАЖНО: Ты ДОЛЖЕН вернуть ответ ТОЛЬКО в формате JSON без дополнительного текста. JSON должен содержать:
1. "name" - название маршрута
2. "description" - подробное описание маршрута (2-3 предложения)
3. "attractions" - МАССИВ объектов, где каждый объект содержит:
   - "name" - точное название достопримечательности
   - "order" - порядковый номер посещения (начиная с 1)
   - "visit_duration" - время посещения в минутах
   - "latitude" - широта координат достопримечательности в Казани (обязательно, число от 55.7 до 55.9)
   - "longitude" - долгота координат достопримечательности в Казани (обязательно, число от 48.9 до 49.2)
   - "description" - краткое описание достопримечательности (1-2 предложения, опционально)
   - "address" - адрес достопримечательности в Казани (опционально)

Выбери 4-8 мест (можно использовать из списка выше или добавить известные места Казани) и расположи их в логичном порядке. 

Если маршрут должен комбинировать разные типы мест (достопримечательности + рестораны + бары и т.д.), распредели их по времени дня логично:
- Утро (9-12): достопримечательности, музеи, парки
- Обед (12-14): рестораны, кафе
- День (14-18): достопримечательности, музеи, прогулки
- Вечер (18-22): бары, рестораны, развлечения

ОБЯЗАТЕЛЬНО укажи координаты для каждого места.

Пример правильного ответа:
{{
    "name": "Маршрут по центру Казани",
    "description": "Описание маршрута...",
    "attractions": [
        {{
            "name": "Казанский Кремль",
            "order": 1,
            "visit_duration": 90,
            "latitude": 55.7981,
            "longitude": 49.1063,
            "description": "Историческая крепость, объект Всемирного наследия ЮНЕСКО",
            "address": "Кремль, Казань"
        }},
        {{
            "name": "Улица Баумана",
            "order": 2,
            "visit_duration": 60,
            "latitude": 55.7947,
            "longitude": 49.1054,
            "description": "Главная пешеходная улица Казани",
            "address": "ул. Баумана, Казань"
        }}
    ]
}}"""
            
            # Use official Perplexity Python SDK
            # Make the prompt more explicit about JSON format requirement
            user_message = f"""Ты помощник по планированию туристических маршрутов в Казани.

{prompt}

КРИТИЧЕСКИ ВАЖНО: Твой ответ должен быть ТОЛЬКО валидным JSON объектом без дополнительного текста, комментариев или markdown разметки. Начни ответ сразу с открывающей фигурной скобки {{ и закончи закрывающей }}. Массив "attractions" ОБЯЗАТЕЛЕН и должен содержать минимум 4 элемента."""
            
            # Initialize Perplexity client
            client = Perplexity(api_key=self.api_key)
            
            # Call Perplexity API using official SDK
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract content from response
            content = response.choices[0].message.content
            
            # Extract JSON from response (might be wrapped in markdown)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                route_data = json.loads(json_match.group())
            else:
                # Fallback: try to parse entire content
                route_data = json.loads(content)
            
            # Validate that attractions array exists
            if 'attractions' not in route_data or not isinstance(route_data.get('attractions'), list):
                logger.warning(f"Perplexity response missing attractions array. Full response: {json.dumps(route_data, ensure_ascii=False, indent=2)}")
                route_data['attractions'] = []
            else:
                logger.info(f"Perplexity returned {len(route_data.get('attractions', []))} attractions: {[a.get('name') for a in route_data.get('attractions', [])]}")
            
            return route_data
        
        except Exception as e:
            logger.error(f"Error generating route with Perplexity LLM: {e}")
            raise
    
    def create_route_from_llm_response(self, user, llm_response: Dict, duration_hours: int) -> Route:
        """Create Route object from LLM response."""
        # Map attraction names to actual Attraction objects
        # Create multiple mappings for better matching
        attractions_map = {}
        attractions_by_keyword = {}
        
        for att in Attraction.objects.filter(is_active=True):
            # Exact name match (lowercase)
            attractions_map[att.name.lower()] = att
            
            # Also index by keywords from name
            name_words = att.name.lower().split()
            for word in name_words:
                if len(word) > 3:  # Only index meaningful words
                    if word not in attractions_by_keyword:
                        attractions_by_keyword[word] = []
                    attractions_by_keyword[word].append(att)
        
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
        matched_attractions = []
        unmatched_names = []
        created_count = 0
        
        attractions_list = llm_response.get('attractions', [])
        
        # If no attractions in response, try to extract from description using LLM
        if not attractions_list:
            logger.warning("No attractions array in LLM response, attempting to extract from description")
            description = llm_response.get('description', '')
            api_key = getattr(settings, 'PERPLEXITY_API_KEY', None)
            if description and api_key:
                try:
                    # Try to extract attraction names from description using a second LLM call
                    from perplexity import Perplexity
                    model = getattr(settings, 'PERPLEXITY_MODEL', 'sonar-pro')
                    
                    # Get available attractions for matching
                    available_attractions = Attraction.objects.filter(is_active=True)[:30]
                    attractions_names_list = "\n".join([f"- {att.name}" for att in available_attractions])
                    
                    extract_prompt = f"""Из следующего описания маршрута извлеки названия достопримечательностей с координатами и верни ТОЛЬКО JSON массив с объектами:

Описание: {description}

Доступные достопримечательности:
{attractions_names_list}

Верни JSON в формате:
{{
    "attractions": [
        {{
            "name": "Точное название из списка выше или известная достопримечательность Казани",
            "order": 1,
            "visit_duration": 60,
            "latitude": 55.7981,
            "longitude": 49.1063,
            "description": "Краткое описание",
            "address": "Адрес в Казани"
        }},
        ...
    ]
}}

ОБЯЗАТЕЛЬНО укажи координаты (latitude, longitude) для каждой достопримечательности. Координаты Казани: широта от 55.7 до 55.9, долгота от 48.9 до 49.2."""
                    
                    client = Perplexity(api_key=api_key)
                    extract_response = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": extract_prompt}],
                        temperature=0.3,
                        max_tokens=1000
                    )
                    
                    extract_content = extract_response.choices[0].message.content
                    json_match = re.search(r'\{.*\}', extract_content, re.DOTALL)
                    if json_match:
                        extract_data = json.loads(json_match.group())
                        attractions_list = extract_data.get('attractions', [])
                        logger.info(f"Extracted {len(attractions_list)} attractions from description")
                except Exception as e:
                    logger.error(f"Failed to extract attractions from description: {e}")
        
        for idx, att_data in enumerate(attractions_list, start=1):
            att_name = att_data.get('name', '').strip()
            if not att_name:
                continue
                
            att_name_lower = att_name.lower()
            attraction = attractions_map.get(att_name_lower)
            
            # Try fuzzy matching if exact match failed
            if not attraction:
                # Try substring matching (more lenient)
                best_match = None
                best_score = 0
                
                for key, att in attractions_map.items():
                    # Calculate similarity score
                    score = 0
                    # Exact substring match gets high score
                    if att_name_lower in key:
                        score = len(att_name_lower) / len(key)
                    elif key in att_name_lower:
                        score = len(key) / len(att_name_lower)
                    
                    if score > best_score and score > 0.5:  # At least 50% match
                        best_score = score
                        best_match = att
                
                if best_match:
                    attraction = best_match
                    logger.info(f"Fuzzy matched '{att_name}' to '{attraction.name}' (score: {best_score:.2f})")
                
                # Try keyword matching as fallback
                if not attraction:
                    att_words = [w for w in att_name_lower.split() if len(w) > 3]
                    for word in att_words:
                        if word in attractions_by_keyword:
                            # Use first match (could be improved with scoring)
                            attraction = attractions_by_keyword[word][0]
                            logger.info(f"Keyword matched '{att_name}' to '{attraction.name}' via keyword '{word}'")
                            break
            
            # If attraction not found, create it in DB using data from Perplexity
            if not attraction:
                # Get coordinates from Perplexity response
                latitude = att_data.get('latitude')
                longitude = att_data.get('longitude')
                
                if latitude and longitude:
                    try:
                        # Create new attraction in database
                        from django.utils.text import slugify
                        
                        # Generate unique slug
                        base_slug = slugify(att_name)
                        slug = base_slug
                        counter = 1
                        while Attraction.objects.filter(slug=slug).exists():
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        
                        # Get or create default category (or use first available)
                        default_category = Category.objects.first()
                        
                        # Create attraction
                        attraction = Attraction.objects.create(
                            name=att_name,
                            slug=slug,
                            description=att_data.get('description', f'Достопримечательность {att_name} в Казани'),
                            short_description=att_data.get('description', '')[:200] if att_data.get('description') else None,
                            latitude=Decimal(str(latitude)),
                            longitude=Decimal(str(longitude)),
                            address=att_data.get('address', ''),
                            category=default_category,
                            visit_duration=att_data.get('visit_duration', 60),
                            is_free=True,  # Assume free by default
                            is_active=True
                        )
                        
                        logger.info(f"Created new attraction in DB: {att_name} at ({latitude}, {longitude})")
                        created_count += 1
                    except Exception as e:
                        logger.error(f"Failed to create attraction '{att_name}': {e}")
                        unmatched_names.append(att_name)
                        continue
                else:
                    unmatched_names.append(att_name)
                    logger.warning(f"Could not match attraction '{att_name}' and no coordinates provided. Skipping.")
                    continue
            
            # Add attraction to route
            if attraction:
                # Use order from LLM response or use position in list
                order = att_data.get('order', idx)
                visit_duration = att_data.get('visit_duration', attraction.visit_duration or 60)
                
                RouteAttraction.objects.create(
                    route=route,
                    attraction=attraction,
                    order=order,
                    visit_duration=visit_duration,
                    notes=att_name if att_name != attraction.name else None
                )
                
                matched_attractions.append(att_name)
                
                # Calculate distance
                if prev_lat and prev_lon:
                    distance = self._calculate_distance(
                        prev_lat, prev_lon,
                        float(attraction.latitude), float(attraction.longitude)
                    )
                    total_distance += distance
                
                prev_lat = float(attraction.latitude)
                prev_lon = float(attraction.longitude)
        
        # Log matching results
        if matched_attractions:
            logger.info(f"Successfully added {len(matched_attractions)} attractions to route (created {created_count} new): {matched_attractions}")
        if unmatched_names:
            logger.warning(f"Failed to match {len(unmatched_names)} attractions: {unmatched_names}")
        
        route.distance_km = Decimal(str(total_distance))
        route.save()
        
        return route



